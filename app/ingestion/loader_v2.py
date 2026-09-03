from __future__ import annotations

import re
from pathlib import Path

import pymupdf
import pymupdf4llm
from langchain_core.documents import Document


TARGET_CHUNK_SIZE = 1000


def normalize_heading(text: str) -> str:
    """
    Normalize Markdown headings so they can be compared against
    titles from the PDF's embedded TOC.
    """

    text = re.sub(r"^#{1,6}\s*", "", text)
    text = re.sub(r"[*_]", "", text)

    return text.strip()


def clean_markdown(markdown: str) -> str:
    """
    Remove obvious repeated page noise.

    We deliberately keep this conservative. It is better to leave
    a little harmless noise than accidentally delete documentation.
    """

    lines = markdown.splitlines()
    cleaned = []

    for line in lines:
        stripped = line.strip()

        if stripped in {"Reference Guide", "AWS SDKs and Tools",}:
            continue

        # Standalone printed page number.
        if re.fullmatch(r"\d{1,3}", stripped):
            continue

        cleaned.append(line)

    text = "\n".join(cleaned)

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def get_toc_path(toc: list[list], index: int,) -> list[str]:
    """
    Build the hierarchical TOC path for one entry.

    Example:
        AWS SDKs and tools settings reference
        > AWS SDKs and Tools standardized credential providers
        > Understand the credential provider chain
    """

    target_level = toc[index][0]

    path = [toc[index][1]]
    expected_level = target_level - 1

    for i in range(index - 1, -1, -1):
        level, title, _ = toc[i]

        if level == expected_level:
            path.append(title)
            expected_level -= 1

        if expected_level == 0:
            break

    return list(reversed(path))


def get_next_boundary(toc: list[list], index: int,) -> tuple[str | None, int | None]:
    """
    Return the immediately following TOC entry.

    For ingestion, each TOC entry owns only the content between
    its heading and the next TOC heading, regardless of level.

    Hierarchical context is preserved separately through toc_path.
    """

    if index + 1 >= len(toc):
        return None, None

    _, next_title, next_page = toc[index + 1]

    return next_title, next_page


def extract_section_markdown(pdf_path: Path, toc: list[list], index: int, page_count: int,) -> tuple[str, int, int]:
    """
    Extract one complete logical TOC section.

    A section may:
    - start halfway through a page,
    - continue onto later pages,
    - end halfway through another page.

    We therefore extract the candidate page range first and then trim
    based on the actual Markdown headings.
    """

    _, title, start_page = toc[index]

    boundary_title, boundary_page = get_next_boundary(toc, index,)

    # PyMuPDF TOC pages are 1-based.
    # pymupdf4llm page indexes are 0-based.
    start_index = start_page - 1

    if boundary_page is not None:
        # The boundary itself may start on this page, so include it
        # temporarily and trim it from the Markdown afterwards.
        end_index = boundary_page - 1
    else:
        end_index = page_count - 1

    markdown = pymupdf4llm.to_markdown(str(pdf_path), pages=list(range(start_index, end_index + 1,)),)

    markdown = clean_markdown(markdown)

    lines = markdown.splitlines()

    section_start = None

    for i, line in enumerate(lines):
        if (normalize_heading(line).lower() == title.strip().lower()):
            section_start = i
            break

    if section_start is None:
        return "", start_page, end_index + 1

    lines = lines[section_start:]

    if boundary_title:
        boundary_normalized = boundary_title.strip().lower()

        for i in range(1, len(lines)):
            if (normalize_heading(lines[i]).lower() == boundary_normalized):
                lines = lines[:i]
                break

    return ("\n".join(lines).strip(), start_page, end_index + 1,)


def split_blocks(markdown: str) -> list[dict]:
    """
    Convert Markdown into structural blocks.

    We currently distinguish:
    - headings
    - tables
    - normal text / lists

    This is intentionally lightweight for v1.
    """

    blocks = []

    current_text = []
    current_table = []

    heading_pattern = re.compile(r"^#{1,6}\s+")

    def flush_text():
        nonlocal current_text

        if not current_text:
            return

        text = "\n".join(current_text).strip()

        if text:
            blocks.append(
                {"type": "text", "content": text,})

        current_text = []

    def flush_table():
        nonlocal current_table

        if not current_table:
            return

        table = "\n".join(current_table).strip()

        if table:
            blocks.append({"type": "table", "content": table,})

        current_table = []

    for line in markdown.splitlines():
        stripped = line.strip()

        if heading_pattern.match(stripped):
            flush_text()
            flush_table()

            blocks.append(
                {
                    "type": "heading",
                    "content": normalize_heading(stripped),
                }
            )

            continue

        if (stripped.startswith("|") and stripped.endswith("|")):
            flush_text()

            current_table.append(stripped)

            continue

        flush_table()

        if stripped:
            current_text.append(stripped)
        elif current_text:
            current_text.append("")

    flush_text()
    flush_table()

    return blocks


def split_sentences(text: str) -> list[str]:
    """
    Sentence-level fallback for paragraphs that are too large.

    We do not normally split at arbitrary character positions.
    """

    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9`_*])", text,)

    return [sentence.strip() for sentence in sentences if sentence.strip()]


def chunk_text(heading: str, text: str,) -> list[str]:
    """
    Pack complete paragraphs until the target size is reached.

    Oversized paragraphs fall back to sentence boundaries.
    """

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text,)
        if paragraph.strip()
    ]

    units = []

    for paragraph in paragraphs:
        if len(paragraph) <= TARGET_CHUNK_SIZE:
            units.append(paragraph)
        else:
            units.extend(
                split_sentences(paragraph))

    chunks = []
    current = []

    for unit in units:
        candidate = "\n\n".join(current + [unit])

        if len(candidate) <= TARGET_CHUNK_SIZE:
            current.append(unit)
            continue

        if current:
            chunks.append("\n\n".join(current))

        current = [unit]

    if current:
        chunks.append("\n\n".join(current))

    return [f"{heading}\n\n{chunk}" for chunk in chunks]


def parse_markdown_table(table_text: str,) -> tuple[list[str], list[str]]:
    """
    Separate a Markdown table header from its body.

    Every resulting chunk can therefore repeat the table header.
    """

    rows = [line.strip() for line in table_text.splitlines() if line.strip()]

    if len(rows) < 2:
        return rows, []

    return rows[:2], rows[2:]


def chunk_table(heading: str, table_text: str,) -> list[str]:
    """
    Split a table only between complete Markdown rows.

    A row itself is never hard-split.
    """

    header, rows = parse_markdown_table(table_text)

    header_text = "\n".join(header)

    if not rows:
        return [f"{heading}\n\n{header_text}"]

    chunks = []
    current_rows = []

    for row in rows:
        candidate_rows = (current_rows + [row])

        rows_text = "\n".join(candidate_rows)

        candidate = (
            f"{heading}\n\n"
            f"{header_text}\n"
            f"{rows_text}"
        )

        if len(candidate) <= TARGET_CHUNK_SIZE:
            current_rows.append(row)
            continue

        if current_rows:
            rows_text = "\n".join(current_rows)

            chunks.append(
                f"{heading}\n\n"
                f"{header_text}\n"
                f"{rows_text}"
            )

        # A single row may itself exceed the target size.
        # We intentionally keep it whole.
        current_rows = [row]

    if current_rows:
        rows_text = "\n".join(current_rows)

        chunks.append(
            f"{heading}\n\n"
            f"{header_text}\n"
            f"{rows_text}"
        )

    return chunks


def remove_repeated_heading_chunks(chunks: list[dict],) -> list[dict]:
    """
    Remove chunks whose body is only the section heading repeated
    because of page headers/footers.
    """

    cleaned = []

    for chunk in chunks:
        content = chunk["content"].strip()
        section = chunk["section"].strip()

        lines = [line.strip() for line in content.splitlines() if line.strip()]

        meaningful_lines = [line for line in lines if line.lower() != section.lower()]

        if not meaningful_lines:
            continue

        cleaned.append(chunk)

    return cleaned


def section_to_chunks(markdown: str,) -> list[dict]:
    """
    Convert one logical TOC section into chunk dictionaries.
    """

    blocks = split_blocks(markdown)

    chunks = []

    current_heading = None

    for block in blocks:
        block_type = block["type"]
        content = block["content"]

        if block_type == "heading":
            current_heading = content
            continue

        if current_heading is None:
            continue

        if block_type == "table":
            table_chunks = chunk_table(current_heading, content,)

            for chunk in table_chunks:
                chunks.append(
                    {
                        "type": "table",
                        "section": current_heading,
                        "content": chunk,
                    }
                )

        elif block_type == "text":
            text_chunks = chunk_text(current_heading, content,)

            for chunk in text_chunks:
                chunks.append(
                    {
                        "type": "text",
                        "section": current_heading,
                        "content": chunk,
                    }
                )

    return remove_repeated_heading_chunks(chunks)


def load_pdf_v2(file_path: str,) -> list[Document]:
    """
    Production candidate for structured PDF ingestion.

    Returns LangChain Documents so the rest of ResearchLens can
    consume the result just like the old loader.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    doc = pymupdf.open(path)
    toc = doc.get_toc()

    if not toc:
        raise ValueError("PDF does not contain an embedded TOC.")

    documents = []

    for index, (toc_level, toc_title, _) in enumerate(toc):
        markdown, page_start, page_end = (
            extract_section_markdown(path, toc, index, doc.page_count,))

        if not markdown:
            continue

        toc_path = get_toc_path(toc, index,)

        chunks = section_to_chunks(markdown)

        for chunk_index, chunk in enumerate(chunks, start=1,):
            documents.append(
                Document(
                    page_content=chunk["content"],
                    metadata={
                        "source": str(path),
                        "section": chunk["section"],
                        "toc_title": toc_title,
                        "toc_level": toc_level,
                        "toc_path": " > ".join(
                            toc_path
                        ),
                        "section_page_start": page_start,
                        "section_page_end": page_end,
                        "content_type": chunk["type"],
                        "chunk_index": chunk_index,
                    },
                )
            )

    return documents