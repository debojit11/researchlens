import type { FormEvent, KeyboardEvent } from "react";
import { LoaderCircle, Send, Square } from "lucide-react";

interface QuestionFormProps {
  query: string;
  loading: boolean;
  examples: string[];
  onQueryChange: (value: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  onExample: (example: string) => void;
}

export function QuestionForm({
  query,
  loading,
  examples,
  onQueryChange,
  onSubmit,
  onCancel,
  onExample,
}: QuestionFormProps) {
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!loading) onSubmit();
  };

  const handleShortcut = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      if (!loading && query.trim()) onSubmit();
    }
  };

  return (
    <form className="query-form" onSubmit={submit}>
      <div className="form-heading">
        <label htmlFor="query">Question</label>
        <span>⌘ / Ctrl + Enter to run</span>
      </div>

      <div className="query-wrap">
        <textarea
          id="query"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          onKeyDown={handleShortcut}
          placeholder="How does AWS SDK credential resolution work?"
          rows={3}
          disabled={loading}
        />

        <button
          type="button"
          className={`submit-button${loading ? " is-running" : ""}`}
          disabled={!loading && !query.trim()}
          onClick={(event) => {
            event.preventDefault();

            if (loading) {
              onCancel();
            } else {
              onSubmit();
            }
          }}
          aria-label={loading ? "Stop current request" : "Ask question"}
        >
          {loading ? (
            <span className="stop-loader" aria-hidden="true">
              <LoaderCircle className="spin" size={18} />
              <Square className="stop-square" size={7} fill="currentColor" />
            </span>
          ) : (
            <Send size={16} />
          )}
          {loading ? "Stop" : "Ask"}
        </button>
      </div>

      <div className="example-row" aria-label="Example questions">
        {examples.map((example) => (
          <button
            key={example}
            type="button"
            className="example-button"
            onClick={() => onExample(example)}
            disabled={loading}
          >
            {example}
          </button>
        ))}
      </div>
    </form>
  );
}
