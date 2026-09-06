import { BookOpen, ExternalLink, Globe2 } from "lucide-react";
import type { Citation } from "../types/research";

interface CitationItemProps {
  citation: Citation;
  index: number;
}

export function CitationItem({ citation, index }: CitationItemProps) {
  const isWeb = citation.type === "web";

  const pageRange =
    !isWeb && citation.page_start && citation.page_end
      ? `pp. ${citation.page_start}–${citation.page_end}`
      : !isWeb && citation.page_start
        ? `p. ${citation.page_start}`
        : "Page range unavailable";

  const content = (
    <>
      <span className="citation-number">{String(index + 1).padStart(2, "0")}</span>
      <div className="citation-copy">
        <div className="citation-topline">
          <span>
            {isWeb ? <Globe2 size={13} /> : <BookOpen size={13} />}
            {isWeb ? "Web source" : "Documentation"}
          </span>
          {isWeb ? <ExternalLink size={14} /> : <small>{pageRange}</small>}
        </div>
        <strong>
          {isWeb
            ? citation.title
            : citation.section || "Referenced documentation section"}
        </strong>
        <span>{isWeb ? citation.url : citation.source}</span>
      </div>
    </>
  );

  return isWeb ? (
    <a
      className="citation-row"
      href={citation.url}
      target="_blank"
      rel="noreferrer"
    >
      {content}
    </a>
  ) : (
    <div className="citation-row">{content}</div>
  );
}
