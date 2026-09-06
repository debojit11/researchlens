import { Settings2 } from "lucide-react";
import type { ResearchResponse } from "../types/research";

function booleanLabel(value: boolean | null | undefined) {
  if (value === true) return "Yes";
  if (value === false) return "No";
  return "N/A";
}

export function AnswerDetails({ result }: { result: ResearchResponse }) {
  return (
    <details className="metadata">
      <summary>
        <Settings2 size={15} /> Answer details
      </summary>
      <div className="metadata-grid">
        <div>
          <span>Route</span>
          <strong>
            {result.route === "web"
              ? "Fresh web"
              : result.route === "documentation"
                ? "Documentation"
                : result.route || "Unknown"}
          </strong>
        </div>
        <div>
          <span>Rewrites</span>
          <strong>{result.rewrite_count ?? 0}</strong>
        </div>
        <div>
          <span>Generation attempts</span>
          <strong>{result.generation_attempts ?? 0}</strong>
        </div>
        <div>
          <span>Faithful</span>
          <strong>{booleanLabel(result.faithful)}</strong>
        </div>
        <div>
          <span>Useful</span>
          <strong>{booleanLabel(result.useful)}</strong>
        </div>
      </div>
    </details>
  );
}
