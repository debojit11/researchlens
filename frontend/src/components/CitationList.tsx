import { CircleAlert } from "lucide-react";
import type { Citation } from "../types/research";
import { CitationItem } from "./CitationItem";

export function CitationList({ citations }: { citations?: Citation[] }) {
  return (
    <aside className="sources-panel">
      <div className="sources-heading">
        <div>
          <span>Sources</span>
          <strong>{citations?.length || 0}</strong>
        </div>
      </div>

      {citations && citations.length > 0 ? (
        citations.map((citation, index) => (
          <CitationItem
            key={`${citation.type}-${index}`}
            citation={citation}
            index={index}
          />
        ))
      ) : (
        <div className="no-citations">
          <CircleAlert size={15} />
          <span>No citations were returned for this run.</span>
        </div>
      )}
    </aside>
  );
}
