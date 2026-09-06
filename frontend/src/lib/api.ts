import type {
  HealthResponse,
  ResearchRequest,
  ResearchResponse,
} from "../types/research";

const DEFAULT_API_BASE_URL =
  "https://researchlens-150737449748.asia-south1.run.app";

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/$/, "");

export class ApiError extends Error {
  readonly kind: "backend" | "network";
  readonly status?: number;

  constructor(message: string, kind: "backend" | "network", status?: number) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
  }
}

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError(
      "The backend returned an unreadable response.",
      "backend",
      response.status,
    );
  }
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      headers: { Accept: "application/json" },
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError("ResearchLens could not reach the backend.", "network");
  }

  if (!response.ok) {
    throw new ApiError(
      `The backend health check returned ${response.status}.`,
      "backend",
      response.status,
    );
  }

  return parseJson<HealthResponse>(response);
}

export async function runResearch(
  request: ResearchRequest,
  signal?: AbortSignal,
): Promise<ResearchResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/research`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(
      "We could not connect to ResearchLens. Check your connection and try again.",
      "network",
    );
  }

  if (!response.ok) {
    let detail =
      response.status === 429
        ? "ResearchLens has temporarily reached an upstream usage limit. Please try again shortly."
        : response.status === 504
          ? "The request timed out. Please try again."
          : response.status >= 500
            ? "ResearchLens is temporarily unable to complete this request. Please try again shortly."
            : "The research request could not be completed.";

    try {
      const body = (await response.json()) as {
        detail?: string;
        message?: string;
      };
      detail = body.detail || body.message || detail;
    } catch {
      // Keep the friendly fallback when the backend does not return JSON.
    }

    throw new ApiError(detail, "backend", response.status);
  }

  return parseJson<ResearchResponse>(response);
}
