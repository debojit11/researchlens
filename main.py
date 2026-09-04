from dotenv import load_dotenv
from app.ingestion.loader_v2 import load_pdf_v2
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


def main():
    print("Loading and chunking document...")
    chunks = load_pdf_v2("data/sample.pdf")

    print(f"Total chunks: {len(chunks)}")

    if vector_store_exists():
        print("\nLoading existing vector store...")
        vector_store = load_vector_store()

    else:
        print("\nCreating vector store...")
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

    query = ("What is the latest stable version of the AWS SDK for Java?")

    result = graph.invoke(
        {
            "query": query,
            "rewrite_count": 0,
            "generation_attempts": 0,
        }
    )

    print("\nFINAL GRAPH STATE")

    print(f"Query: {result['query']}")

    print(f"Route: {result.get('route')}")

    print("Rewrite count:", result.get("rewrite_count", 0,),)

    print("Relevant docs:", len(result.get("relevant_docs", [],)),)

    print("\nANSWER")
    print("=" * 50)
    print(result.get("answer"))

    print("\nCITATIONS")
    print("=" * 50)

    for citation in result.get("citations", [],):
        print(citation)

    print("Generation attempts:", result.get("generation_attempts"),)

    print("Faithful:", result.get("faithful"),)

    print("Useful:", result.get("useful"),)

    print("\nRERANKED DOCS")
    print("=" * 50)

    for i, doc in enumerate(
        result.get("reranked_docs", [],), start=1,):
        print(f"\n--- Reranked {i} ---")

        print("Section:", doc.metadata.get("section"),)

        print("Section pages:", doc.metadata.get("section_page_start"),
            "-", doc.metadata.get("section_page_end"),)

        print("TOC path:", doc.metadata.get("toc_path"),)

        print(doc.page_content[:1000])

    print("\nRELEVANT DOCS")
    print("=" * 50)

    for i, doc in enumerate(result.get("relevant_docs", [],), start=1,):
        print(f"\n--- Relevant {i} ---")

        print("Section:", doc.metadata.get("section"),)

        print(
            "Section pages:", doc.metadata.get("section_page_start"),
            "-", doc.metadata.get("section_page_end"),)

        print("TOC path:", doc.metadata.get("toc_path"),)

        print(doc.page_content[:1000])


if __name__ == "__main__":
    main()