from dotenv import load_dotenv
from app.ingestion.loader import load_pdf
from app.retrieval.vector import (create_vector_store, load_vector_store,
vector_search, vector_store_exists)
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import merge_results
from app.retrieval.reranker import Reranker
from app.graph.graders import RelevanceGrader
from app.config import MIN_RELEVANT_DOCS
from app.graph.query_rewriter import QueryRewriter
from app.graph.query_router import QueryRouter
from app.web.search import TinyFishSearch
from app.graph.generator import AnswerGenerator
from app.graph.workflow import build_research_graph


load_dotenv()

def print_results(title, results):
    print(f"\n{'='*50}")
    print(title)
    print("="*50)

    for i, doc in enumerate(results, start=1):
        print(f"\n--- Result{i} ---")
        print(f"Page: {doc.metadata.get('page_label')}")
        print(doc.page_content[:500])


def print_reranked_results(results):
    print(f"\n{'=' * 50}")
    print("RERANKED RESULTS")
    print("=" * 50)

    for i, (doc, score) in enumerate(results, start=1):
        print(f"\n--- Result {i} ---")
        print(f"Score: {score:.4f}")
        print(f"Page: {doc.metadata.get('page_label')}")
        print(doc.page_content[:500])


def print_graded_results(results):
    print(f"\n{'=' * 50}")
    print("RELEVANCE GRADES")
    print("=" * 50)

    for i, (doc, score, relevant) in enumerate(results, start=1):
        print(f"\n--- Result {i} ---")
        print(f"Rerank score: {score:.4f}")
        print(f"Relevant: {relevant}")
        print(f"Page: {doc.metadata.get('page_label')}")
        print(doc.page_content[:400])


def main():
    print("Loading and chunking document...")
    chunks = load_pdf("data/sample.pdf")
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
    )

    query = "What changed in AWS SDK authentication this week?"

    result = graph.invoke(
        {
            "query": query,
            "rewrite_count": 0,
        }
    )

    web_results = result.get("web_results", [])

    print("\nFINAL GRAPH STATE")
    print(f"Query: {result['query']}")
    print(f"Route: {result.get('route')}")
    print(f"Rewrite count: {result.get('rewrite_count', 0)}")
    print(f"Relevant docs: {len(result.get('relevant_docs', []))}")
    print(f"Rewritten query: {result.get('rewritten_query', 'None')}")
    print(f"Web results: {len(web_results)}")

    for i, web_result in enumerate(web_results, start=1):
        print(f"\n--- Web Result {i} ---")
        print(f"Title: {web_result.get('title')}")
        print(f"URL: {web_result.get('url')}")
        print(web_result.get("text", "")[:500])

    print("\nANSWER")
    print("=" * 50)
    print(result.get("answer"))

    print("\nCITATIONS")
    print("=" * 50)

    for citation in result.get("citations", []):
        print(citation)


if __name__ == "__main__":
    main()
