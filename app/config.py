from pathlib import Path


BASE_DIR=Path(__file__).resolve().parent.parent

DATA_DIR= BASE_DIR / 'data'
CHROMA_DIR= BASE_DIR / ".chroma"
CHUNK_SIZE= 800
CHUNK_OVERLAP= 150

MIN_RELEVANT_DOCS = 2


GRADER_MODEL = "gemini-3.5-flash-lite"
EMBEDDING_MODEL = "gemini-embedding-2"
REWRITER_MODEL = "gemini-3.6-flash"



