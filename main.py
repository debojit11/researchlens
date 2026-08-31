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
        vector_store= load_vector_store()
    else:
        print("\nCreating vector store...")
        vector_store= create_vector_store(chunks)

    print("Creating BM25 index...")
    bm25_retriever= BM25Retriever(chunks)

    print("\nLoading reranker...")
    reranker=Reranker()

    query= "How does AWS SDK credential resolution work?"

    vector_results= vector_search(vector_store, query, k=5)

    bm25_results = bm25_retriever.search(query, k=5)

    hybrid_results= merge_results(vector_results, bm25_results)

    reranked_results = reranker.rerank(query, hybrid_results, top_k=5)

    print(f"\nQuery: {query}")

    print_results("VECTOR SEARCH RESULTS", vector_results)

    print_results("BM25 SEARCH RESULTS", bm25_results)

    print_results("HYBRID CANDIDATES", hybrid_results)

    print(f"\nTotal hybrid candidates: {len(hybrid_results)}")

    print_reranked_results(reranked_results)

    print("\nGrading reranked documents...")
    relevance_grader = RelevanceGrader()

    graded_results=[]

    for doc, score in reranked_results:
        is_relevant= relevance_grader.grade(query=query,
                                            document=doc.page_content)

        graded_results.append((doc, score, is_relevant))

    print_graded_results(graded_results)

    relevant_docs = [doc for doc, _, relevant in graded_results
    if relevant]

    print(f"\nRelevant documents: {len(relevant_docs)}")

    if len(relevant_docs) < MIN_RELEVANT_DOCS:
        print("\nRetrieval quality is poor. Rewriting query...")

        rewriter = QueryRewriter()

        rewritten_query = rewriter.rewrite(query)

        print(f"Original query:  {query}")
        print(f"Rewritten query: {rewritten_query}")

    else:
        print("\nEnough relevant evidence found.")


if __name__ == "__main__":
    main()
