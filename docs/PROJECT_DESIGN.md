# ResearchLens — Project Design Notes

This document records the architectural decisions, experiments, reasoning, and current implementation status for ResearchLens.

## 1. Project Goal

ResearchLens is an adaptive technical research assistant.

The system should answer technical questions using indexed documentation when the answer is available there, while also being able to use web search for fresh or external information.

The project is intentionally bounded. The goal is not to keep adding RAG techniques indefinitely, but to demonstrate a strong intermediate-level system that combines:

- LangGraph orchestration
- hybrid RAG
- reranking
- retrieval correction
- web fallback
- self-evaluation
- LangSmith observability and evaluation
- deployment

## 2. Locked v1 Architecture

```text
                         QUESTION
                            |
                            v
                      Query Analysis
                            |
                  +---------+---------+
                  |                   |
             Documentation        Web Search
                  |                   |
          +-------+-------+           v
          |               |      Search + Fetch
          v               v           |
     Vector Search     BM25 Search     v
          |               |      Web Evidence Grader
          +-------+-------+          / \
                  v                 /   \
             Merge Results      evidence  none
                  v                |       |
               Rerank              |       v
                  v                |  Insufficient Evidence
          Relevance Grader         |
             /        \            |
          Good        Poor          |
           |            |           |
           |       Rewrite Query    |
           |            |           |
           |       Retrieve Again   |
           |            |           |
           |   still poor -> Web Search
           |                        |
           +------------------------+
                            |
                            v
                         Generate
                            |
                            v
                    Faithfulness Check
                       /          \
                    Pass          Fail
                     |             |
                     v             +--> bounded retry
                Usefulness Check
                   /       \
                Pass       Fail
                 |          |
                 v          +--> bounded retry
                END
```

The best short description for the current system is:

**Adaptive RAG with corrective retrieval behavior.**

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
- configuration keys
- API names
- exception names

### Combined approach

Vector top-k and BM25 top-k candidate sets are merged using reciprocal-rank-style scoring before reranking.

This increases recall without relying entirely on either semantic or lexical retrieval.

## 4. Why Reranking?

The first-stage retrievers are optimized for candidate recall.

The reranker performs a deeper query-document comparison over only the merged candidate set.

The current reranker is:

```text
BAAI/bge-reranker-base
```

It is loaded locally through `FlagEmbedding`.

### Reranker experiments

Several rerankers were evaluated because broad technical questions sometimes caused specialized chunks to outrank broader documentation.

`BAAI/bge-reranker-v2-m3`

- strong quality
- clean 12/12 evaluation
- roughly 2.27 GB of weights
- too large and slow for the intended free deployment target

`BAAI/bge-reranker-base`

- roughly 1.11 GB
- clean 12/12 evaluation
- median end-to-end evaluation latency around 20 seconds in the established baseline
- chosen as the v1 balance of quality, footprint, and deployment practicality

`Alibaba-NLP/gte-reranker-modernbert-base`

- much smaller model footprint
- did not materially improve end-to-end latency
- produced an answer-behavior regression in the 12-case evaluation
- rejected for v1

The reranker search was therefore stopped instead of continuously optimizing one component.

## 5. Why a Separate Relevance Grader?

Reranking improves ordering but does not guarantee that every surviving result is useful at the scope requested.

A recurring observed case was broad credential-resolution questions retrieving narrower IAM Identity Center or provider-specific chunks.

The relevance grader performs a binary decision:

```text
Question + Chunk
      |
      v
 relevant / irrelevant
```

The prompt was tightened so lexical similarity alone is not enough, and a specialized subtype should not dominate a broad question unless it materially contributes to the broader answer.

The grader remains intentionally separate from the reranker because ordering and evidence sufficiency are different decisions.

## 6. Query Rewriting and Corrective Retrieval

If too few documents survive relevance grading, the system rewrites the query.

Purpose:

- improve technical terminology
- make the query more explicit
- align it with documentation language
- preserve the original intent

The query rewriter does not answer the question.

The default threshold remains:

```python
MIN_RELEVANT_DOCS = 2
```

The retry loop is bounded by configuration so the graph cannot rewrite forever.

If repeated retrieval remains weak, control moves to web search.

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

- grading and routing are constrained classification tasks, so lightweight models are sufficient,
- rewriting and final answer generation benefit from a stronger generation model,
- embeddings use a dedicated embedding model,
- reranking runs locally to avoid additional API cost and external rate limits.

Gemini 3.x calls intentionally do not set temperature.

## 8. Persistence

Chroma is persisted under:

```text
.chroma/
```

Current behavior:

```text
First run after an ingestion or embedding change:
PDF -> structured chunks -> embeddings -> persistent Chroma

Later runs:
persistent Chroma -> query embedding -> similarity search
```

The PDF is still parsed on application startup because BM25 needs the current chunk set in memory.

The vector and BM25 corpora must always come from the same ingestion version. When ingestion or embedding formatting changes, `.chroma` must be rebuilt rather than loading the stale index.

## 9. Web Search Strategy

TinyFish Search + Fetch is used when a question requires fresh/external information or documentation retrieval remains weak after bounded correction.

Freshness-sensitive terms include:

- `today`
- `this week`
- `latest`
- `recent`
- `recently`
- `newest`
- `current`

Fresh queries use a recency window and live fetch behavior with `ttl=0`.

### Web evidence filtering

Search results are not passed directly to generation.

Current web path:

```text
web search
   |
   v
Search + Fetch
   |
   v
Web Evidence Grader
   |
   +--> relevant evidence -> Generate
   |
   `--> no evidence -> Insufficient Evidence -> END
```

The web evidence grader checks whether the fetched result actually matches the requested product/entity/scope and whether freshness-sensitive claims contain suitable temporal evidence.

This prevents scope-drift results from reaching the generator merely because search returned something superficially related.

## 10. Answer Generation and Citations

The generator receives only evidence that survived the relevant retrieval path.

Documentation evidence and web evidence remain separate so their citation metadata can be constructed differently.

The documentation generator prompt was adjusted to:

- prefer evidence that addresses the full scope of the question,
- use narrow/provider-specific evidence as supporting detail,
- avoid letting a specialized case dominate when broader evidence is available.

Current documentation citations contain:

```text
type
source
section
page_start
page_end
```

The page range represents the physical PDF page range occupied by the TOC section rather than exact per-chunk bounding boxes.

Web citations contain:

```text
type
title
url
```

## 11. Output Quality Checks

Phase 6 is complete.

After generation, the answer is checked in sequence:

```text
answer
  |
  v
Faithfulness
  |
  +--> fail -> bounded regeneration
  |
  v
Usefulness
  |
  +--> fail -> bounded regeneration
  |
  v
END
```

If the system cannot produce an answer that passes the required grounding and quality checks within the configured attempts, it returns an explicit quality-failure response instead of continuing indefinitely.

If no usable evidence exists, a separate insufficient-evidence terminal is used.

## 12. LangSmith Tracing and Evaluation

LangSmith tracing is enabled through:

```env
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=researchlens
```

The evaluation dataset is:

```text
researchlens-v1-eval
```

It contains 12 representative cases covering:

- broad credential resolution
- credential provider chain
- `AWS_PROFILE`
- credential configuration
- retry settings
- fresh authentication changes
- latest credential-related changes
- latest stable AWS SDK for Java version
- credential-source selection
- an external Django middleware query
- a credential precedence paraphrase
- recent credential precedence changes

Evaluation dimensions:

- route accuracy
- answer behavior
- faithfulness
- usefulness

Faithfulness and usefulness evaluators return `None` when no generation occurred, rather than incorrectly scoring the system for explicit insufficient-evidence behavior.

### Established reranker baseline

With `BAAI/bge-reranker-base`, the pre-ingestion-v2 benchmark achieved:

```text
route accuracy:        1.00
answer behavior:       1.00
faithfulness:          1.00
usefulness:            1.00
```

The same evaluation suite is being reused after ingestion changes so architecture decisions are compared against a stable set of cases.

## 13. Why Ingestion v2 Was Added

The original loader was intentionally simple:

```text
PyPDFLoader
   |
   v
RecursiveCharacterTextSplitter
chunk_size = 800
chunk_overlap = 150
```

It produced 581 chunks.

During retrieval inspection, several problems became visible:

- chunks sometimes ended mid-sentence,
- some content appeared visually split inside words,
- section hierarchy was lost,
- table fragments were weak retrieval units,
- broad questions could be influenced by narrow chunks whose local wording happened to match well.

Instead of blindly increasing chunk size, the PDF structure itself was inspected.

The AWS SDKs and Tools Reference Guide was found to contain a reliable embedded hierarchical TOC. Font/layout inspection also showed regular heading levels, and PyMuPDF4LLM produced cleaner Markdown for prose, lists, and tables than the original flat extraction.

That justified a structure-aware ingestion experiment.

## 14. Ingestion v2 Design

Current flow:

```text
PDF
 |
 v
PyMuPDF embedded TOC
 |
 +--> canonical hierarchy
 |
 v
PyMuPDF4LLM Markdown extraction
 |
 v
clean repeated page noise
 |
 v
atomic TOC sections
 |
 v
structural block classification
 |
 +--> prose / lists
 |      |
 |      `--> paragraph and sentence-aware packing
 |
 +--> tables
        |
        `--> complete Markdown rows, header repeated
 |
 v
LangChain Document
```

### Why atomic TOC sections?

The first TOC-aware prototype defined a section as continuing until the next heading at the same or higher level.

That was useful for isolated inspection but wrong for whole-corpus indexing because parent sections duplicated all descendant content.

The first production attempt therefore produced:

```text
2,612 chunks
```

The section ownership model was corrected so each TOC entry owns only the content between itself and the immediately following TOC entry, regardless of level.

Hierarchy is preserved separately through `toc_path`.

After this change:

```text
746 structured chunks
```

This is larger than the original 581 because tables/text blocks are intentionally separated, but it removes the large parent/child duplication.

### Chunking rules

Preferred splitting order:

```text
section boundary
    |
paragraph boundary
    |
sentence boundary
    |
hard character split only as an exceptional fallback
```

Tables are never intentionally split in the middle of a Markdown row. If one row exceeds the target size, the row is kept whole because semantic integrity is more important than a strict character limit.

### Current metadata

Each `Document` contains metadata including:

```text
source
section
toc_title
toc_level
toc_path
section_page_start
section_page_end
content_type
chunk_index
```

The section page fields intentionally describe the logical section range rather than claiming exact page bounds for every individual chunk.

## 15. Parser Comparison: PyMuPDF4LLM vs Docling

PyMuPDF4LLM significantly improved prose and Markdown structure but narrow PDF table cells still produced artifacts such as identifiers broken across visual line wraps.

A controlled Docling comparison was run to see whether a heavier document parser solved this.

Docling improved table reconstruction structurally but:

- required substantially more processing time on the 242-page corpus,
- emitted many table-cell recovery warnings,
- still produced broken identifiers in narrow cells,
- did not provide enough quality improvement to justify its weight for v1.

Decision:

```text
PyMuPDF + PyMuPDF4LLM
```

remain the production-candidate parser stack.

Perfect PDF table reconstruction is explicitly not a v1 goal.

## 16. Gemini Embedding 2 Retrieval Formatting

The original vector implementation passed raw document and query strings directly to `gemini-embedding-2`.

The current vector layer adds a custom LangChain `Embeddings` wrapper so query and document embedding inputs can be asymmetric while keeping stored `Document.page_content` unchanged.

Conceptual document input:

```text
title: <section heading> | text: <chunk body>
```

Conceptual query input:

```text
task: question answering | query: <user query>
```

Why preserve `page_content`?

BM25, the reranker, relevance grader, generator, and citations should receive normal documentation text, not embedding-only instructions.

The wrapper therefore transforms text only at embedding time.

A sanity test confirmed document and query embeddings are both 3072 dimensions.

Changing this embedding format required rebuilding `.chroma`, because the existing index contained embeddings produced from the older representation.

## 17. Current Ingestion-v2 Retrieval Observation

The new corpus and embedding format run end-to-end successfully.

For the broad query:

```text
How does AWS SDK credential resolution work?
```

the broad `Understand the credential provider chain` section survives into the top five, while several specialized credential-resolution sections still rank above it.

The generator correctly prefers the broader mechanism first and uses specialized evidence as support.

This means the system is currently healthy, but the broad-vs-specialized ordering behavior remains an observed retrieval characteristic rather than something being hidden.

The reranker will not be changed again unless the full evaluation shows a meaningful regression.

## 18. Current Evaluation Issue

A fresh 12-case LangSmith run is in progress for the ingestion-v2 baseline.

The latest attempt reached multiple cases successfully but then encountered temporary:

```text
429 RESOURCE_EXHAUSTED
```

errors from Gemini Embedding 2 during query embedding.

The exception occurs inside vector retrieval when Chroma requests `embed_query`, not in LangGraph orchestration or Chroma persistence.

Current plan:

- rerun after the temporary capacity/quota condition clears,
- if the problem repeats, add a small retry/backoff around query embedding,
- do not redesign the architecture because of a transient API-capacity failure.

## 19. Current Implementation Status

### Phase 1 — Retrieval Foundation

Status: COMPLETE

Implemented:

- structured PDF loading
- TOC-aware chunking
- persistent Chroma vector store
- Gemini Embedding 2
- dense similarity search
- BM25 retrieval
- reciprocal-rank hybrid merge
- deduplication
- local BGE reranking

### Phase 2 — Retrieval Correction

Status: COMPLETE

Implemented:

- LLM relevance grading
- minimum relevant-document threshold
- query rewriting
- bounded retrieval correction
- web fallback after repeated weak retrieval

### Phase 3 — LangGraph Orchestration

Status: COMPLETE

Implemented:

- `ResearchState`
- retrieval, reranking, grading, rewriting, routing, generation, and quality-check nodes
- documentation vs web routing
- bounded corrective retrieval loop
- bounded generation-quality retry loop
- explicit failure terminals

### Phase 4 — Query Routing and Web Search

Status: COMPLETE

Implemented:

- LLM documentation-vs-web routing
- TinyFish Search + Fetch
- direct web route
- web fallback
- freshness handling
- web evidence grader
- explicit no-evidence terminal

### Phase 5 — Answer Generation

Status: COMPLETE

Implemented:

- grounded documentation answers
- grounded web answers
- broad-scope evidence preference
- structured documentation citations
- structured web citations
- explicit insufficient-evidence behavior

### Phase 6 — Output Quality Checks

Status: COMPLETE

Implemented:

- faithfulness grader
- usefulness grader
- bounded retry logic
- explicit quality-failure terminal

### Phase 7 — LangSmith

Status: IN PROGRESS / ALMOST COMPLETE

Implemented:

- tracing
- evaluation dataset
- route evaluator
- answer-behavior evaluator
- faithfulness evaluator
- usefulness evaluator
- reranker comparison experiments
- established clean BGE-base benchmark

Remaining:

- complete a clean post-ingestion-v2 12-case run
- optionally perform one controlled corrective/rewrite-branch validation before final freeze

### Phase 8 — UI and Deployment

Status: NOT STARTED

Remaining:

- Streamlit frontend
- free deployment
- final cleanup
- final examples

## 20. v1 Boundary

The following remain intentionally excluded:

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

## 21. Definition of Done

ResearchLens v1 is finished when a deployed user can:

1. Ask a technical question.
2. Be routed to documentation or web search.
3. Retrieve evidence using vector + BM25.
4. Rerank the evidence.
5. Reject weak evidence.
6. Rewrite and retry failed retrieval.
7. Fall back to web search when necessary.
8. Reject weak web evidence.
9. Receive a grounded answer with citations.
10. Have the answer checked for faithfulness and usefulness.
11. Inspect traces/evaluations through LangSmith.
12. Use the system through the deployed Streamlit UI.

After this point, the project should be considered complete rather than continuously expanded.
