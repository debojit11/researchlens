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
![Phase 3](https://img.shields.io/badge/Phase%203-In%20Progress-blue)

Next:

- Define graph state
- Convert retrieval pipeline into graph nodes
- Add conditional routing
- Add retry loop after query rewriting

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
|   `-- graph/
|       |-- __init__.py
|       |-- graders.py
|       |-- query_rewriter.py
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

- LangGraph orchestration
- Web search routing and fallback
- Grounded answer generation with citations
- Faithfulness and usefulness checks
- LangSmith tracing and evaluation
- Streamlit deployment
