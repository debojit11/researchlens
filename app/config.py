from pathlib import Path


BASE_DIR=Path(__file__).resolve().parent.parent

DATA_DIR= BASE_DIR / 'data'
CHROMA_DIR= BASE_DIR / ".chroma"
CHUNK_SIZE= 800
CHUNK_OVERLAP= 150

MIN_RELEVANT_DOCS = 2
MAX_REWRITES = 2


GRADER_MODEL = "gemini-3.5-flash-lite"
EMBEDDING_MODEL = "gemini-embedding-2"
REWRITER_MODEL = "gemini-3.6-flash"
ROUTER_MODEL = "gemini-3.5-flash-lite"
GENERATOR_MODEL = "gemini-3.6-flash"



DOCS_DESCRIPTION = (
    "AWS SDKs and Tools Reference Guide covering authentication, "
    "credentials, configuration, SDK behavior, endpoints, retries, "
    "profiles, and related AWS SDK functionality."
)