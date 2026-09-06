import { Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ResearchResponse } from "../types/research";
import { AnswerDetails } from "./AnswerDetails";

interface AnswerViewProps {
  result: ResearchResponse;
  copied: boolean;
  onCopy: () => void;
}

export function AnswerView({ result, copied, onCopy }: AnswerViewProps) {
  return (
    <article className="answer-document">
      <div className="answer-toolbar">
        <span>Answer</span>
        <button type="button" className="text-button" onClick={onCopy}>
          <Check size={14} />
          {copied ? "Copied" : "Copy answer + sources"}
        </button>
      </div>

      <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml>
        {result.answer || "No answer was returned by the backend."}
      </ReactMarkdown>

      <AnswerDetails result={result} />
    </article>
  );
}
