import { CircleAlert, Clock3, LoaderCircle, RefreshCw } from "lucide-react";
import type { ResearchResponse } from "../types/research";
import { AnswerView } from "./AnswerView";
import { CitationList } from "./CitationList";

export type RequestStatus = "idle" | "loading" | "success" | "error";

interface ResearchResultProps {
  status: RequestStatus;
  result: ResearchResponse | null;
  error: { title: string; message: string } | null;
  copied: boolean;
  onRetry: () => void;
  onCopy: () => void;
}

export function ResearchResult({
  status,
  result,
  error,
  copied,
  onRetry,
  onCopy,
}: ResearchResultProps) {
  const showResult = status === "success" && result;

  return (
    <div className="results-area">
      <div className="results-heading">
        <h2>{showResult ? "Answer" : status === "error" ? "Request status" : ""}</h2>
        {showResult && (
          <div className="result-time">
            <Clock3 size={14} /> Just now
            <span className={`route-badge ${result.route === "web" ? "web" : ""}`}>
              {result.route === "web" ? "Fresh web" : "Documentation"}
            </span>
          </div>
        )}
      </div>

      {status === "idle" && (
        <div className="empty-state">
          <p>Ask a technical question to get a grounded answer with sources.</p>
        </div>
      )}

      {status === "loading" && (
        <div className="loading-state">
          <LoaderCircle className="spin" size={19} />
          <div>
            <strong>Researching…</strong>
            <span>Finding and evaluating evidence. This can take 15–30 seconds.</span>
          </div>
        </div>
      )}

      {status === "error" && error && (
        <div className="error-card">
          <div className="error-symbol">
            <CircleAlert size={20} />
          </div>
          <div>
            <strong>{error.title}</strong>
            <p>{error.message}</p>
            <button type="button" className="text-button retry-button" onClick={onRetry}>
              <RefreshCw size={14} /> Try again
            </button>
          </div>
        </div>
      )}

      {showResult && (
        <div className="result-layout">
          <AnswerView result={result} copied={copied} onCopy={onCopy} />
          <CitationList citations={result.citations} />
        </div>
      )}
    </div>
  );
}
