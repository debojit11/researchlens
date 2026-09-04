from unittest.mock import patch

from dotenv import load_dotenv

from app.ingestion.loader_v2 import load_pdf_v2

from app.retrieval.vector import (
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
from app.graph.generator import AnswerGenerator
from app.graph.workflow import build_research_graph

from app.web.search import TinyFishSearch


TEST_THRESHOLD = 6


def test_corrective_retrieval_branch():
    load_dotenv()

    query = "How does AWS SDK credential resolution work?"

    print("\nLoading structured chunks...")
    chunks = load_pdf_v2("data/sample.pdf")

    if not vector_store_exists():
        raise RuntimeError("Vector store does not exist. Run main.py first.")

    print("Loading existing vector store...")
    vector_store = load_vector_store()

    print("Creating BM25 index...")
    bm25_retriever = BM25Retriever(chunks)

    print("Loading reranker...")
    reranker = Reranker()

    relevance_grader = RelevanceGrader()
    query_rewriter = QueryRewriter()
    query_router = QueryRouter()

    web_search = TinyFishSearch()
    web_evidence_grader = WebEvidenceGrader()

    answer_generator = AnswerGenerator()
    faithfulness_grader = FaithfulnessGrader()
    usefulness_grader = UsefulnessGrader()

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

    initial_state = {
        "query": query,
        "rewritten_query": "",
        "route": "",
        "hybrid_docs": [],
        "reranked_docs": [],
        "relevant_docs": [],
        "web_results": [],
        "rewrite_count": 0,
        "answer": "",
        "citations": [],
        "faithful": False,
        "useful": False,
        "generation_attempts": 0,
    }

    # Force the corrective-retrieval path only inside this test.
    #
    # Production config stays MIN_RELEVANT_DOCS = 2.
    with patch("app.graph.routes.MIN_RELEVANT_DOCS", TEST_THRESHOLD,):
        result = graph.invoke(initial_state)

    print("\nCORRECTIVE RETRIEVAL TEST")
    print("=" * 60)
    print("Query:", result["query"])
    print("Route:", result["route"])
    print("Rewrite count:", result["rewrite_count"])
    print("Relevant docs:", len(result["relevant_docs"]))
    print("Generation attempts:", result["generation_attempts"])
    print("Answer:")
    print(result["answer"])

    assert result["route"] == "documentation"

    assert result["rewrite_count"] > 0, (
        "Corrective retrieval did not execute: "
        "rewrite_count remained 0."
    )