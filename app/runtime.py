from dotenv import load_dotenv
from app.ingestion.chunk_store import load_chunks
from app.retrieval.vector import (
    create_vector_store,
    load_vector_store,
    vector_store_exists,
)
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.reranker import Reranker

from app.graph.graders import (
    RelevanceGrader,
    FaithfulnessGrader,
    UsefulnessGrader,
    WebEvidenceGrader,
)

from app.graph.query_rewriter import QueryRewriter
from app.graph.query_router import QueryRouter
from app.web.search import TinyFishSearch
from app.graph.generator import AnswerGenerator
from app.graph.workflow import build_research_graph


load_dotenv()


def build_runtime():
    print("Loading persisted chunks...")
    chunks = load_chunks("data/chunks.jsonl")

    print(f"Total chunks: {len(chunks)}")

    if vector_store_exists():
        print("Loading existing vector store...")
        vector_store = load_vector_store()
    else:
        print("Creating vector store...")
        vector_store = create_vector_store(chunks)

    print("Creating BM25 index...")
    bm25_retriever = BM25Retriever(chunks)

    print("Loading reranker...")
    reranker = Reranker()

    relevance_grader = RelevanceGrader()
    faithfulness_grader = FaithfulnessGrader()
    usefulness_grader = UsefulnessGrader()
    web_evidence_grader = WebEvidenceGrader()

    query_rewriter = QueryRewriter()
    query_router = QueryRouter()

    web_search = TinyFishSearch()
    answer_generator = AnswerGenerator()

    graph = build_research_graph(
        vector_store=vector_store,
        bm25_retriever=bm25_retriever,
        reranker=reranker,
        relevance_grader=relevance_grader,
        query_rewriter=query_rewriter,
        query_router=query_router,
        web_search=web_search,
        answer_generator=answer_generator,
        faithfulness_grader=faithfulness_grader,
        usefulness_grader=usefulness_grader,
        web_evidence_grader=web_evidence_grader,
    )

    print("ResearchLens runtime ready.")

    return graph