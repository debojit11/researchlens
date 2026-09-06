import { useCallback, useEffect, useRef, useState } from "react";
import { HealthIndicator } from "../components/HealthIndicator";
import { QuestionForm } from "../components/QuestionForm";
import {
  ResearchResult,
  type RequestStatus,
} from "../components/ResearchResult";
import { ApiError, fetchHealth, runResearch } from "../lib/api";
import type { ResearchResponse } from "../types/research";

const examples = [
  "How does AWS SDK credential resolution work?",
  "How does AWS_PROFILE affect credential selection?",
  "What is the latest stable version of the AWS SDK for Java?",
];

export default function Home() {
  const [query, setQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [status, setStatus] = useState<RequestStatus>("idle");
  const [error, setError] = useState<{ title: string; message: string } | null>(
    null,
  );
  const [health, setHealth] = useState<boolean | null>(null);
  const [checkingHealth, setCheckingHealth] = useState(true);
  const [copied, setCopied] = useState(false);

  const abortRef = useRef<AbortController | null>(null);

  const checkBackend = useCallback(async () => {
    const controller = new AbortController();
    setCheckingHealth(true);

    try {
      const response = await fetchHealth(controller.signal);
      setHealth(response.status === "ok" && response.runtime_ready !== false);
    } catch {
      setHealth(false);
    } finally {
      setCheckingHealth(false);
    }

    return () => controller.abort();
  }, []);

  useEffect(() => {
    void checkBackend();

    return () => {
      abortRef.current?.abort();
    };
  }, [checkBackend]);

  const submitQuery = async (rawQuery: string) => {
    const trimmed = rawQuery.trim();

    if (!trimmed) {
      setError({
        title: "A question is required",
        message: "Enter a question before asking.",
      });
      setStatus("error");
      return;
    }

    if (status === "loading") return;

    abortRef.current?.abort();

    const controller = new AbortController();
    abortRef.current = controller;

    setQuery(trimmed);
    setActiveQuery(trimmed);
    setStatus("loading");
    setError(null);
    setResult(null);

    try {
      const researchResult = await runResearch(
        { query: trimmed },
        controller.signal,
      );

      setResult(researchResult);
      setStatus("success");
    } catch (requestError) {
      if (
        requestError instanceof DOMException &&
        requestError.name === "AbortError"
      ) {
        return;
      }

      const apiError =
        requestError instanceof ApiError
          ? requestError
          : new ApiError("Something unexpected happened.", "network");

      const errorTitle =
        apiError.kind === "network"
          ? "Backend unavailable"
          : apiError.status === 429
            ? "Usage limit reached"
            : apiError.status === 504
              ? "Request timed out"
              : apiError.status === 502 || apiError.status === 503
                ? "Service temporarily unavailable"
                : "Research request failed";

      setError({
        title: errorTitle,
        message: apiError.message,
      });
      setStatus("error");
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
      }
    }
  };

  const retry = () => {
    if (activeQuery) void submitQuery(activeQuery);
  };

  const cancelRequest = () => {
    abortRef.current?.abort();
    abortRef.current = null;

    setStatus("idle");
    setError(null);
    setResult(null);
  };

  const copyAnswerWithCitations = async () => {
    if (!result) return;

    const citations = result.citations?.length
      ? `\n\nSources:\n${result.citations
          .map((citation, index) => {
            if (citation.type === "web") {
              return `${index + 1}. ${citation.title} — ${citation.url}`;
            }

            const pages =
              citation.page_start && citation.page_end
                ? ` (pp. ${citation.page_start}–${citation.page_end})`
                : citation.page_start
                  ? ` (p. ${citation.page_start})`
                  : "";

            return `${index + 1}. ${
              citation.section || "Referenced documentation section"
            }${pages} — ${citation.source}`;
          })
          .join("\n")}`
      : "\n\nSources: None returned";

    await navigator.clipboard?.writeText(`${result.answer}${citations}`);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className="site-frame">
      <header className="topbar">
        <a className="wordmark" href="#research">
          <span className="wordmark-symbol" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <span>ResearchLens</span>
        </a>
      </header>

      <main id="research" className="page-shell">
        <section className="workspace">
          <div className="page-heading">
            <h1>Ask a question</h1>
            <p className="heading-note">Docs or live web evidence per question.</p>
          </div>

          <div className="context-row">
            <div>
              <span>Corpus</span>
              <strong>AWS SDKs + Tools</strong>
            </div>
            <div>
              <span>Mode</span>
              <strong>Adaptive</strong>
            </div>
            <div className="context-health">
              <span>Backend</span>
              <HealthIndicator online={health} checking={checkingHealth} />
            </div>
          </div>

          <QuestionForm
            query={query}
            loading={status === "loading"}
            examples={examples}
            onQueryChange={(value) => {
              setQuery(value);
              if (status === "error") {
                setError(null);
                setStatus("idle");
              }
            }}
            onSubmit={() => void submitQuery(query)}
            onCancel={cancelRequest}
            onExample={(example) => {
              setQuery(example);
              setError(null);
              if (status === "error") setStatus("idle");
            }}
          />

          <ResearchResult
            status={status}
            result={result}
            error={error}
            copied={copied}
            onRetry={retry}
            onCopy={() => void copyAnswerWithCitations()}
          />
        </section>
      </main>

      <footer className="site-footer">
        <span>
          ResearchLens <b>·</b> Technical research with sources
        </span>
        <span>AWS SDKs + Tools</span>
      </footer>
    </div>
  );
}
