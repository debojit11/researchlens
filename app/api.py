from contextlib import asynccontextmanager
import asyncio
import os
import re
import time

import httpx

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.runtime import build_runtime
from langchain_google_genai.chat_models import GoogleAPIError, GoogleRateLimitError
from google.genai.errors import ClientError, ServerError


graph = None


class ResearchRequest(BaseModel):
    query: str


class ResearchResponse(BaseModel):
    answer: str
    citations: list[dict]
    route: str | None
    rewrite_count: int
    generation_attempts: int
    faithful: bool | None
    useful: bool | None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph

    graph = build_runtime()
    yield


app = FastAPI(
    title="ResearchLens",
    version="0.1.0",
    lifespan=lifespan,
)


cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


def _exception_text(exc: BaseException) -> str:
    parts: list[str] = []
    seen: set[int] = set()
    current: BaseException | None = exc

    while current is not None and id(current) not in seen:
        seen.add(id(current))
        text = str(current)
        if text:
            parts.append(text)
        current = current.__cause__ or current.__context__

    return "\n".join(parts)


def _extract_retry_after_seconds(exc: BaseException) -> int | None:
    text = _exception_text(exc)

    patterns = (
        r"Please retry in\s+([0-9]+(?:\.[0-9]+)?)s",
        r"retryDelay['\"\s:]+([0-9]+(?:\.[0-9]+)?)s",
    )

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            seconds = float(match.group(1))
            whole = int(seconds)
            return max(1, whole if seconds == whole else whole + 1)

    return None


def _rate_limit_http_exception(exc: BaseException) -> HTTPException:
    retry_after = _extract_retry_after_seconds(exc)

    if retry_after is not None:
        detail = (
            "ResearchLens has temporarily reached an upstream model usage limit. "
            f"Please try again in about {retry_after} seconds."
        )
        headers = {"Retry-After": str(retry_after)}
    else:
        detail = (
            "ResearchLens has temporarily reached an upstream model usage limit. "
            "Please try again in a few minutes."
        )
        headers = None

    return HTTPException(status_code=429, detail=detail, headers=headers)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "runtime_ready": graph is not None,
    }


@app.post("/research", response_model=ResearchResponse)
async def research(payload: ResearchRequest, request: Request):
    start = time.perf_counter()

    graph_task = asyncio.create_task(
        graph.ainvoke(
            {
                "query": payload.query,
                "rewrite_count": 0,
                "generation_attempts": 0,
            }
        )
    )

    try:
        while not graph_task.done():
            if await request.is_disconnected():
                graph_task.cancel()

                try:
                    await graph_task
                except asyncio.CancelledError:
                    pass

                print("Research request cancelled: client disconnected.")
                return ResearchResponse(
                    answer="",
                    citations=[],
                    route=None,
                    rewrite_count=0,
                    generation_attempts=0,
                    faithful=None,
                    useful=None,
                )

            await asyncio.sleep(0.1)

        result = await graph_task

    except asyncio.CancelledError:
        if not graph_task.done():
            graph_task.cancel()
        raise

    # Chat-model quota errors surfaced by langchain-google-genai.
    except GoogleRateLimitError as exc:
        raise _rate_limit_http_exception(exc) from exc

    # Lower-level google-genai errors can surface from embeddings.
    except ClientError as exc:
        if getattr(exc, "code", None) == 429:
            raise _rate_limit_http_exception(exc) from exc

        raise HTTPException(
            status_code=502,
            detail="The upstream model service returned an invalid request.",
        ) from exc

    except ServerError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "The upstream model service is temporarily unavailable. "
                "Please try again shortly."
            ),
        ) from exc

    except GoogleAPIError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "The upstream model service is temporarily unavailable. "
                "Please try again shortly."
            ),
        ) from exc

    except (httpx.TimeoutException, TimeoutError) as exc:
        raise HTTPException(
            status_code=504,
            detail=(
                "The request timed out while waiting for an upstream service. "
                "Please try again."
            ),
        ) from exc

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            retry_after = exc.response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "An upstream service has temporarily reached its usage limit. "
                        f"Please try again in about {retry_after} seconds."
                    ),
                    headers={"Retry-After": retry_after},
                ) from exc

            raise HTTPException(
                status_code=429,
                detail=(
                    "An upstream service has temporarily reached its usage limit. "
                    "Please try again in a few minutes."
                ),
            ) from exc

        if 500 <= exc.response.status_code < 600:
            raise HTTPException(
                status_code=503,
                detail=(
                    "An upstream service is temporarily unavailable. "
                    "Please try again shortly."
                ),
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="An upstream service returned an unexpected error.",
        ) from exc

    except Exception as exc:
        print(f"Unhandled research error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=(
                "ResearchLens could not complete this request because of an "
                "unexpected error. Please try again."
            ),
        ) from exc

    elapsed = time.perf_counter() - start
    print(f"Research request completed in {elapsed:.2f}s")

    return ResearchResponse(
        answer=result.get("answer", ""),
        citations=result.get("citations", []),
        route=result.get("route"),
        rewrite_count=result.get("rewrite_count", 0),
        generation_attempts=result.get("generation_attempts", 0),
        faithful=result.get("faithful"),
        useful=result.get("useful"),
    )
