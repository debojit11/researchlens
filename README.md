# ResearchLens

ResearchLens is an adaptive technical research assistant built with **LangGraph**, **hybrid RAG**, **corrective retrieval**, **web fallback**, and **LangSmith**.

It answers technical questions from indexed documentation when possible, routes freshness-sensitive questions to live web search, retries weak retrieval, and returns grounded answers with citations.

## Live Application

**ResearchLens:** https://gen-lang-client-0560064293.web.app

Backend API: `https://researchlens-150737449748.asia-south1.run.app`

## What It Does

- Routes each question to documentation retrieval or live web search
- Combines vector retrieval with BM25
- Reranks retrieved evidence before generation
- Grades evidence quality and rewrites weak queries
- Falls back to web search when documentation retrieval remains insufficient
- Filters web evidence before generation
- Produces cited answers grounded in retrieved evidence
- Runs faithfulness and usefulness checks
- Exposes LangSmith traces and evaluation results
- Supports cancellable requests from the deployed UI

## Architecture

ResearchLens is an **adaptive RAG system with corrective retrieval behavior**.

At a high level:

- LangGraph controls routing, retrieval, retries, generation, and quality checks
- documentation questions use Chroma + BM25 hybrid retrieval
- a local BGE reranker improves candidate ordering
- weak retrieval is corrected through query rewriting and bounded retries
- fresh or external questions use TinyFish Search + Fetch
- Gemini models handle routing, grading, rewriting, and answer generation
- FastAPI serves the backend on Google Cloud Run
- React + Vite serves the frontend on Firebase Hosting

For the full architecture, design decisions, experiments, and evaluation notes, see [`docs/PROJECT_DESIGN.md`](docs/PROJECT_DESIGN.md).

## Development Approach

### Phase 1 — Retrieval Foundation
Built persistent Chroma retrieval, BM25 keyword search, hybrid merging, and local reranking.

### Phase 2 — Retrieval Correction
Added relevance grading, query rewriting, minimum-evidence thresholds, and bounded corrective retrieval.

### Phase 3 — LangGraph Orchestration
Moved the system into a stateful graph with conditional routing, retries, and explicit terminal paths.

### Phase 4 — Web Search and Fallback
Added TinyFish Search + Fetch, freshness-aware routing, web fallback, and web-evidence grading.

### Phase 5 — Grounded Generation
Added documentation/web answer generation with structured citations and explicit insufficient-evidence behavior.

### Phase 6 — Output Quality
Added faithfulness and usefulness checks with bounded regeneration.

### Phase 7 — LangSmith Evaluation
Added tracing and evaluation across routing, answer behavior, faithfulness, and usefulness.

Final evaluation:

```text
route accuracy:        1.00
answer behavior:       1.00
faithfulness:          1.00 on generated answers
usefulness:            1.00 on generated answers
successful runs:       12/12
```

### Phase 8 — UI and Deployment
Added FastAPI, a React + Vite frontend, request cancellation, friendly upstream error handling, Docker packaging, Cloud Run deployment, and Firebase Hosting.

**Status: Complete**

## Tech Stack

### AI / Retrieval
- LangChain
- LangGraph
- Gemini API
- Gemini Embedding 2
- ChromaDB
- BM25
- FlagEmbedding / `BAAI/bge-reranker-base`
- TinyFish
- LangSmith

### Backend
- Python 3.12+
- FastAPI
- uv
- Docker

### Frontend
- React
- TypeScript
- Vite
- Firebase Hosting

### Deployment
- Google Cloud Run
- Firebase Hosting
- Google Secret Manager

## Current Corpus

The v1 corpus is the **AWS SDKs and Tools Reference Guide**.

The project intentionally uses one technical documentation corpus so the focus stays on retrieval quality, correction, evaluation, and production deployment rather than ecosystem breadth.

## Local Setup

Install dependencies:

```bash
uv sync
```

Create a root `.env` file:

```env
GOOGLE_API_KEY=
HF_TOKEN=
TINYFISH_API_KEY=

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=researchlens
```

Run the backend:

```bash
uv run uvicorn app.api:app --reload --port 8001
```

Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

For local frontend development:

```env
VITE_API_BASE_URL=http://localhost:8001
```

Run the evaluation suite:

```bash
uv run python -m evals.run_experiment
```

## Production Deployment

Frontend:

```text
https://gen-lang-client-0560064293.web.app
```

Backend:

```text
https://researchlens-150737449748.asia-south1.run.app
```

Current Cloud Run configuration:

```text
region:         asia-south1
memory:         4 GiB
CPU:            1 vCPU
concurrency:    2
min instances:  1
max instances:  2
timeout:        300 seconds
```

## Repository Structure

```text
researchlens/
├── app/
│   ├── api.py
│   ├── runtime.py
│   ├── config.py
│   ├── state.py
│   ├── graph/
│   ├── ingestion/
│   ├── retrieval/
│   └── web/
├── data/
├── docs/
│   └── PROJECT_DESIGN.md
├── evals/
├── frontend/
├── scripts/
├── tests/
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

## Project Status

ResearchLens v1 is complete.

The deployed system satisfies the original v1 goal: a user can ask a technical question, be routed to documentation or web search, receive retrieved and reranked evidence, trigger corrective retrieval when needed, get a grounded answer with citations, and use the full system through the deployed application.
