# ResearchLens Frontend

Clean Vite + React + TypeScript frontend for the ResearchLens FastAPI backend.

## Run locally

```bash
npm install
npm run dev
```

The default backend is:

```text
https://researchlens-150737449748.asia-south1.run.app
```

To override it, copy `.env.example` to `.env` and set:

```env
VITE_API_BASE_URL=https://your-backend.example.com
```

## Build

```bash
npm run build
```

Production files are emitted to `dist/`.

## Keyboard shortcut

The question textarea supports both:

- `Cmd + Enter` on macOS
- `Ctrl + Enter` on Windows/Linux

## Backend CORS

A frontend hosted on a different origin from the FastAPI backend requires CORS on the backend. If browser requests show the backend as unavailable even though `/health` works directly in a browser, add FastAPI `CORSMiddleware` for the frontend's deployed origin.

Example backend configuration:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://YOUR-FRONTEND-DOMAIN"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)
```

For local development, you may temporarily add `http://localhost:5173` as another allowed origin.

## What was cleaned from the Manus export

- Removed the unused Node/Express server.
- Removed `shared/` auth/session scaffolding.
- Removed Manus runtime/debug plugins.
- Removed unused shadcn/Radix component library files.
- Reduced dependencies to the packages actually used by ResearchLens.
- Split the large generated `Home.tsx` into focused components.
- Fixed retry so it reuses the actual previous query.
- Faithfulness/usefulness now show `N/A` when absent instead of incorrectly showing `No`.
- Implemented Cmd/Ctrl + Enter submission.
- Kept safe Markdown rendering with `react-markdown` + `remark-gfm` and raw HTML disabled.
