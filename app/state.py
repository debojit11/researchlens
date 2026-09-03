from typing import TypedDict
from langchain_core.documents import Document


class ResearchState(TypedDict, total=False):
    query: str
    rewritten_query: str

    route:str

    hybrid_docs: list[Document]
    reranked_docs: list[Document]
    relevant_docs: list[Document]

    web_results: list[dict]

    rewrite_count: int

    answer: str
    citations: list[dict]

    faithful: bool
    useful: bool
    generation_attempts: int

    