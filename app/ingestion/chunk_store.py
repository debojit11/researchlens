import json
from pathlib import Path

from langchain_core.documents import Document


def save_chunks(chunks: list[Document], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            record = {
                "page_content": chunk.page_content,
                "metadata": chunk.metadata,
            }

            file.write(json.dumps(record, ensure_ascii=False,) + "\n")


def load_chunks(input_path: str) -> list[Document]:
    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"Persisted chunk file not found: {path}")

    chunks = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)

            chunks.append(Document(page_content=record["page_content"],
                    metadata=record["metadata"],))

    return chunks