# ResearchLens — Project Design Notes

This document records the architectural decisions, reasoning, and current implementation status for ResearchLens.

## 1. Project Goal

ResearchLens is an adaptive technical research assistant.

The system should answer technical questions using indexed documentation when the answer is available there, while also being able to use web search for fresh or external information.

The project is intentionally bounded. The goal is not to keep adding RAG techniques indefinitely, but to demonstrate a strong intermediate-level system that combines:

- LangGraph orchestration
- Hybrid RAG
- Reranking
- Retrieval correction
- Web fallback
- Self-evaluation
- LangSmith observability and evaluation
- Deployment

## 2. Locked v1 Architecture

```text
                         QUESTION
                             |
                             v
                      Query Analysis
                             |
                  +----------+----------+
                  |                     |
             Documentation          Web Search
                  |                     |
          +-------+--------+            |
          v                v            |
     Vector Search      BM25 Search     |
          |                |            |
          +-------+--------+            |
                  v                     |
             Merge Results              |
                  v                     |
               Rerank                   |
                  v                     |
          Relevance Grader              |
             /          \               |
         Good            Poor           |
          |                |            |
          |          Rewrite Query      |
          |                |            |
          |          Retrieve Again     |
          |                |            |
          |       still poor -> Web Search
          |                     |
          +---------------------+--------+
                                |
                                v
                             Generate
                                |
                                v
                        Faithfulness Check
                           /           \
                        Pass           Fail
                         |              |
                         v              +--> retry
                    Usefulness Check
                       /       \
                    Pass       Fail
                     |          |
                     v          +--> retry
                    END
```

## 3. Why Hybrid Retrieval?

Dense retrieval and BM25 solve different retrieval problems.

### Vector search

Vector search retrieves chunks based on semantic similarity.

Example:

- User query: `How are AWS credentials selected?`
- Documentation wording: `credential provider chain`

The wording is different, but the meaning is related.

### BM25

BM25 performs lexical retrieval and is especially useful for technical documentation containing exact identifiers such as:

- `AWS_PROFILE`
- `AWS_ACCESS_KEY_ID`
- `StateGraph`
- `InvalidUpdateError`
- configuration keys
- API names
- exception names

### Combined approach

The two candidate sets are merged and deduplicated before reranking.

This increases recall without relying entirely on either semantic or lexical search.

## 4. Why Reranking?

The retrieval systems are optimized for finding candidate chunks quickly.

The reranker performs a deeper query-document comparison using:

`cross-encoder/ms-marco-MiniLM-L-6-v2`

It runs locally through `sentence-transformers`.

The reranker does not search the corpus. It only reorders the candidate documents already retrieved by vector search and BM25.

## 5. Why a Separate Relevance Grader?

Reranking improves ordering but does not guarantee that every surviving result is truly useful.

Observed example:

- Some chunks about endpoint resolution received non-trivial reranker scores for a query about credential resolution.
- The LLM relevance grader correctly rejected those chunks.

The relevance grader therefore performs a stricter binary decision:

```text
Question + Chunk
      |
      v
 relevant / irrelevant
```

This result will later control LangGraph routing.

## 6. Query Rewriting

If too few documents survive relevance grading, the system rewrites the user query.

Purpose:

- improve technical terminology
- make the query more explicit
- align it with documentation language
- preserve the original intent

The query rewriter does not answer the question.

The current default threshold is:

```python
MIN_RELEVANT_DOCS = 2
```

A higher threshold was used temporarily only to test the rewrite branch.

## 7. Model Choices

Current configuration:

```python
GRADER_MODEL = "gemini-3.5-flash-lite"
REWRITER_MODEL = "gemini-3.6-flash"
ROUTER_MODEL = "gemini-3.5-flash-lite"
GENERATOR_MODEL = "gemini-3.6-flash"
EMBEDDING_MODEL = "gemini-embedding-2"
```

Reasoning:

- Grading is a simple classification-style task, so a lightweight model is sufficient.
- Query routing is also a constrained classification task and uses the lightweight model.
- Query rewriting and final answer generation benefit from a stronger generation model.
- Embeddings use a dedicated embedding model.
- Reranking is performed locally to avoid API cost and rate limits.

## 8. Persistence

Chroma is persisted under:

```text
.chroma/
```

This prevents the documentation corpus from being re-embedded on every run.

Current behavior:

```text
First run:
PDF -> chunks -> embeddings -> persistent Chroma

Later runs:
persistent Chroma -> query embedding -> similarity search
```

The PDF is still parsed on every run because BM25 currently needs the chunks in memory.

This can be optimized later, but it is not currently a priority.

## 9. Web Search Strategy

TinyFish Search + Fetch is used when a question requires fresh or external information, or when documentation retrieval remains weak after bounded rewriting attempts.

Current behavior:

```text
normal web query
-> TinyFish Search
-> Fetch
-> Generate

freshness-sensitive query
-> TinyFish Search with recency_minutes
-> Fetch with ttl=0
-> Generate
```

Freshness-sensitive queries include terms such as `today`, `this week`, `latest`, `recent`, and `current`.

Web evidence is kept separate from indexed documentation evidence. The final answer-generation node can therefore construct source-specific citation metadata for either branch.

## 10. Current Implementation Status

### Phase 1 — Retrieval Foundation

Status: COMPLETE

Implemented:

- PDF loading
- Recursive text splitting
- metadata preservation
- persistent Chroma vector store
- Gemini embeddings
- dense similarity search
- BM25 retrieval
- hybrid merge
- deduplication
- local cross-encoder reranking

### Phase 2 — Retrieval Correction

Status: COMPLETE

Implemented:

- LLM relevance grading
- minimum relevant-document threshold
- query rewriting
- success branch test
- rewrite branch test

### Phase 3 — LangGraph Orchestration

Status: COMPLETE

Implemented:

- `ResearchState` with progressively populated graph fields
- graph nodes for retrieval, reranking, grading, rewriting, query analysis, web search, and generation
- documentation vs web conditional routing
- bounded query-rewrite and retrieval retry loop
- fallback to web search after repeated weak documentation retrieval

### Phase 4 — Query Routing and Web Search

Status: COMPLETE

Implemented:

- LLM-based documentation vs web query routing
- TinyFish Search + Fetch integration
- direct web route for fresh or external questions
- web fallback after failed documentation retrieval
- freshness-sensitive search with `recency_minutes`
- live fetches for fresh queries with `ttl=0`

### Phase 5 — Answer Generation

Status: COMPLETE

Implemented:

- grounded answer generation from documentation evidence
- grounded answer generation from fetched web evidence
- structured documentation citations containing source and page metadata
- structured web citations containing source title and URL
- explicit refusal to invent an answer when supplied evidence is insufficient

## 11. Planned Remaining Phases

### Phase 6 — Output quality checks
- faithfulness grader
- usefulness grader
- retry/fallback logic

### Phase 7 — LangSmith
- tracing
- evaluation dataset
- retrieval quality evaluation
- answer quality evaluation
- inspection of graph runs

### Phase 8 — UI and deployment
- Streamlit frontend
- free deployment
- final README
- architecture diagram
- example queries
- cleanup

## 12. v1 Boundary

The following are intentionally excluded from v1:

- multimodal RAG
- GraphRAG
- CAG
- multi-agent architecture
- authentication
- user accounts
- billing
- Kubernetes
- custom model training
- fine-tuning
- elaborate long-term memory
- multiple technical ecosystems

Adding another technical documentation ecosystem later should be treated as a data/configuration extension, not a new architectural milestone.

## 13. Definition of Done

ResearchLens v1 is finished when a deployed user can:

1. Ask a technical question.
2. Be routed to documentation or web search.
3. Retrieve evidence using vector + BM25.
4. Rerank the evidence.
5. Reject weak evidence.
6. Rewrite and retry failed retrieval.
7. Fall back to web search when necessary.
8. Receive a grounded answer with citations.
9. Have the answer checked for faithfulness and usefulness.
10. Inspect traces/evaluations through LangSmith.

After this point, the project should be considered complete rather than continuously expanded.
