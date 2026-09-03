# ResearchLens

ResearchLens is an adaptive technical research assistant built with **LangGraph**, **hybrid RAG**, **reranking**, **corrective retrieval**, **web fallback**, and **LangSmith**.

The system answers technical questions from indexed documentation when possible, falls back to web search when the question is fresh or outside the indexed corpus, retries weak retrieval, and produces grounded answers with citations.

## Current Architecture

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

## Project Scope

### Included in v1

- Technical documentation ingestion
- Structure-aware chunking and metadata preservation
- Persistent Chroma vector store
- Gemini Embedding 2 retrieval embeddings
- Dense/vector retrieval
- BM25 keyword retrieval
- Reciprocal-rank hybrid merging
- Local cross-encoder reranking
- LLM-based relevance grading
- Query rewriting when retrieval quality is poor
- LangGraph state, nodes, conditional routing, and bounded retry loops
- Freshness-aware web search fallback
- Web evidence filtering before generation
- Grounded answer generation with structured citations
- Faithfulness checking
- Answer usefulness checking
- LangSmith tracing and evaluation
- Streamlit frontend
- Free deployment

### Explicitly out of scope

- Multimodal RAG
- GraphRAG
- CAG
- Multi-agent systems
- Authentication and billing
- Large-scale production infrastructure
- Fine-tuning
- Multiple technical ecosystems in v1

## Current Progress

### Phase 1 — Retrieval Foundation
![Phase 1](https://img.shields.io/badge/Phase%201-Complete-brightgreen)

- Persistent Chroma vector store
- Gemini embeddings
- Dense/vector retrieval
- BM25 retrieval
- Hybrid result merging and deduplication
- Local cross-encoder reranking
- Current reranker: `BAAI/bge-reranker-base`

The reranker choice was validated experimentally. Larger and alternative rerankers were tested, but `bge-reranker-base` provided the best balance of quality, model size, and latency for v1.

### Phase 2 — Retrieval Correction
![Phase 2](https://img.shields.io/badge/Phase%202-Complete-brightgreen)

- Relevance grader
- Minimum evidence threshold
- Query rewriter
- Good-evidence branch
- Poor-evidence branch
- Bounded rewrite/retrieval retry loop
- Web fallback after repeated weak retrieval

### Phase 3 — LangGraph Orchestration
![Phase 3](https://img.shields.io/badge/Phase%203-Complete-brightgreen)

- Shared `ResearchState`
- Retrieval, reranking, grading, rewriting, routing, generation, and quality-check nodes
- Conditional graph routing
- Documentation vs web query analysis
- Bounded generation retries
- Explicit terminal path when sufficient evidence cannot be found

### Phase 4 — Web Search and Fallback
![Phase 4](https://img.shields.io/badge/Phase%204-Complete-brightgreen)

- TinyFish Search + Fetch integration
- Direct web route for fresh or external questions
- Web fallback after weak documentation retrieval
- Freshness-aware search using `recency_minutes`
- Live fetches for freshness-sensitive queries using `ttl=0`
- LLM-based web evidence grading
- Empty-evidence terminal instead of generating from weak or mismatched web results

### Phase 5 — Answer Generation and Citations
![Phase 5](https://img.shields.io/badge/Phase%205-Complete-brightgreen)

- Grounded generation from documentation evidence
- Grounded generation from fetched web evidence
- Broad-scope evidence preference in the generator
- Structured documentation citations with source, section, and section page range
- Structured web citations with source titles and URLs
- Explicit refusal to invent an answer when evidence is insufficient

### Phase 6 — Output Quality Checks
![Phase 6](https://img.shields.io/badge/Phase%206-Complete-brightgreen)

- Faithfulness grader
- Usefulness grader
- Bounded regeneration after quality failure
- Explicit terminal response if an acceptable grounded answer cannot be produced

### Phase 7 — LangSmith and Evaluation
![Phase 7](https://img.shields.io/badge/Phase%207-In%20Progress-yellow)

Completed:

- LangSmith tracing
- Evaluation dataset: `researchlens-v1-eval`
- 12 representative documentation and web-search cases
- Route-accuracy evaluator
- Answer-behavior evaluator
- Faithfulness evaluator
- Usefulness evaluator
- Multiple reranker comparison runs
- Clean 12/12 quality benchmark with `BAAI/bge-reranker-base` before the ingestion-v2 experiment

Current validation work:

- The retrieval corpus has been rebuilt using the new structured ingestion pipeline and task-aware Gemini Embedding 2 formatting.
- A fresh 12-case evaluation is being rerun against this ingestion-v2 baseline.
- The latest run was interrupted by temporary Gemini Embedding 2 `429 RESOURCE_EXHAUSTED` errors during query embedding, so that comparison still needs a clean rerun.

### Phase 8 — UI and Deployment
![Phase 8](https://img.shields.io/badge/Phase%208-Not%20Started-lightgrey)

Remaining:

- Streamlit frontend
- Free deployment
- Final cleanup and examples

## Structured Ingestion v2

The original ingestion path used `PyPDFLoader` followed by fixed-size recursive character splitting. Retrieval testing exposed several issues:

- some chunks ended mid-sentence,
- section context could be lost,
- table content could be fragmented,
- printed page numbers and physical PDF page indexes were easy to confuse.

The AWS SDKs and Tools Reference Guide contains a reliable embedded PDF table of contents, so the ingestion pipeline was redesigned around the document's own structure instead of blindly increasing chunk size.

Current ingestion flow:

```text
PDF
 |
 v
PyMuPDF embedded TOC
 |
 +--> canonical section hierarchy
 |
 v
PyMuPDF4LLM Markdown extraction
 |
 v
TOC-bounded atomic sections
 |
 v
semantic block splitting
 |
 +--> prose / lists -> paragraph and sentence-aware packing
 |
 +--> tables -> complete-row splitting with repeated headers
 |
 v
LangChain Documents
```

Each chunk now preserves metadata such as:

- source
- section
- TOC title
- TOC level
- full TOC path
- section page start/end
- content type
- chunk index

The first structured prototype accidentally duplicated parent and child TOC content and produced 2,612 chunks. Switching to atomic ownership between one TOC heading and the immediately following TOC heading reduced the corpus to **746 structured chunks** while retaining hierarchy through `toc_path`.

PyMuPDF4LLM and Docling were compared for table-heavy pages. Docling reconstructed table structure more aggressively but remained much slower and still did not reliably repair narrow-cell word fragmentation. PyMuPDF + PyMuPDF4LLM was therefore kept for v1.

## Gemini Embedding 2 Retrieval Formatting

The vector layer now uses a small embedding wrapper so document and query text can be formatted differently for question-answering retrieval without modifying the stored `Document.page_content`.

Conceptually:

```text
Document embedding input:
title: <section heading> | text: <chunk content>

Query embedding input:
task: question answering | query: <user query>
```

This keeps BM25, reranking, relevance grading, answer generation, and citations working from the original clean chunk text while giving the dense retriever asymmetric query/document instructions.

## Tech Stack

- Python 3.12+
- uv
- LangChain
- LangGraph
- ChromaDB
- rank-bm25
- PyMuPDF
- PyMuPDF4LLM
- FlagEmbedding
- Gemini API
- TinyFish
- LangSmith
- Streamlit

## Current Development Corpus

The current development corpus is the **AWS SDKs and Tools Reference Guide**.

It is used as the single v1 documentation corpus so retrieval, correction, evaluation, and deployment can be completed without adding unnecessary ecosystem breadth.

## Setup

Create and activate the environment:

```bash
uv sync
```

Create a `.env` file:

```env
GOOGLE_API_KEY=
HF_TOKEN=
TINYFISH_API_KEY=

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=researchlens
```

Run the current pipeline:

```bash
uv run python main.py
```

Run the evaluation suite:

```bash
uv run python -m evals.run_experiment
```

## Repository Structure

```text
researchlens/
|
|-- .chroma/
|
|-- app/
|   |-- config.py
|   |-- state.py
|   |
|   |-- ingestion/
|   |   |-- __init__.py
|   |   |-- loader.py
|   |   `-- loader_v2.py
|   |
|   |-- retrieval/
|   |   |-- __init__.py
|   |   |-- vector.py
|   |   |-- bm25.py
|   |   |-- hybrid.py
|   |   `-- reranker.py
|   |
|   |-- web/
|   |   |-- __init__.py
|   |   `-- search.py
|   |
|   `-- graph/
|       |-- __init__.py
|       |-- graders.py
|       |-- generator.py
|       |-- nodes.py
|       |-- query_rewriter.py
|       |-- query_router.py
|       |-- routes.py
|       `-- workflow.py
|
|-- data/
|-- docs/
|   `-- PROJECT_DESIGN.md
|
|-- evals/
|   |-- __init__.py
|   |-- create_dataset.py
|   |-- add_examples.py
|   |-- evaluators.py
|   `-- run_experiment.py
|
|-- scripts/
|   |-- inspect_pdf.py
|   |-- chunking_prototype.py
|   |-- chunking_prototype_v2.py
|   |-- test_loader_v2.py
|   `-- test_embeddings_v2.py
|
|-- .env
|-- .gitignore
|-- main.py
|-- pyproject.toml
`-- README.md
```

## Roadmap

The core adaptive-RAG system is implemented.

Remaining v1 milestones are intentionally small:

- complete a clean ingestion-v2 LangSmith evaluation run,
- perform the final controlled corrective/rewrite branch validation if still needed,
- build the Streamlit UI,
- deploy on a free tier,
- finalize examples and documentation.

The project remains intentionally bounded: new RAG techniques or additional documentation ecosystems are not required for v1.
