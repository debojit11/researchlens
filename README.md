# ResearchLens

ResearchLens is an adaptive technical research assistant built with **LangGraph**, **hybrid RAG**, **reranking**, and **LangSmith**.

The goal is to answer technical questions using indexed documentation when possible, fall back to web search when needed, recover from weak retrieval, and produce grounded answers with citations.

## Current Architecture

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

## Project Scope

### Included in v1

- Technical documentation ingestion
- Chunking and metadata preservation
- Persistent Chroma vector store
- Dense/vector retrieval
- BM25 keyword retrieval
- Hybrid result merging and deduplication
- Cross-encoder reranking
- LLM-based relevance grading
- Query rewriting when retrieval quality is poor
- LangGraph state, nodes, routing, and retry loops
- Web search fallback
- Grounded answer generation with citations
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

- PDF loading
- Chunking
- Metadata preservation
- Persistent Chroma vector store
- Dense/vector retrieval
- BM25 retrieval
- Hybrid result merging
- Deduplication
- Local cross-encoder reranking

### Phase 2 — Retrieval Correction
![Phase 2](https://img.shields.io/badge/Phase%202-Complete-brightgreen)

- Relevance grader
- Minimum evidence threshold
- Query rewriter
- Good-evidence branch
- Poor-evidence branch

### Phase 3 — LangGraph Orchestration
![Phase 3](https://img.shields.io/badge/Phase%203-Complete-brightgreen)

- Shared `ResearchState`
- Retrieval, reranking, grading, rewriting, and routing nodes
- Conditional graph routing
- Bounded rewrite/retrieval retry loop
- Documentation vs web query analysis

### Phase 4 — Web Search and Fallback
![Phase 4](https://img.shields.io/badge/Phase%204-Complete-brightgreen)

- TinyFish Search + Fetch integration
- Direct web route for fresh or external questions
- Web fallback after weak documentation retrieval
- Freshness-aware search using `recency_minutes`
- Live fetches for freshness-sensitive queries using `ttl=0`

### Phase 5 — Answer Generation and Citations
![Phase 5](https://img.shields.io/badge/Phase%205-Complete-brightgreen)

- Grounded generation from documentation evidence
- Grounded generation from fetched web evidence
- Structured documentation citations with page metadata
- Structured web citations with source titles and URLs

### Phase 6 — Output Quality Checks
![Phase 6](https://img.shields.io/badge/Phase%206-Next-blue)

Next:

- Faithfulness grader
- Usefulness grader
- Retry/fallback logic after generation

## Tech Stack

- Python 3.12+
- uv
- LangChain
- LangGraph
- ChromaDB
- rank-bm25
- sentence-transformers
- Gemini API
- LangSmith
- Streamlit

## Current Development Corpus

The current development corpus is the **AWS SDKs and Tools Reference Guide**.

It is used only for development and retrieval testing. The final technical ecosystem can be changed later without changing the core architecture.

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

LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=researchlens
```

Run the current pipeline:

```bash
uv run python main.py
```

## Repository Structure

```text
researchlens/
|
|-- app/
|   |-- config.py
|   |-- state.py
|   |
|   |-- ingestion/
|   |   |-- __init__.py
|   |   `-- loader.py
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
|-- tests/
|-- .env
|-- .gitignore
|-- main.py
|-- pyproject.toml
`-- README.md
```

## Roadmap

ResearchLens is currently under active development.

Next milestones include:

- Faithfulness and usefulness checks
- LangSmith tracing and evaluation
- Streamlit deployment
- Final documentation and examples
