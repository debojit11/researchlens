from app.state import ResearchState
from app.retrieval.vector import vector_search
from app. retrieval.hybrid import merge_results



def hybrid_retrieval_node(state: ResearchState, *, vector_store,
                          bm25_retriever,) -> dict:

    query = state.get("rewritten_query") or state["query"]

    vector_results = vector_search(vector_store, query, k=5)

    bm25_results = bm25_retriever.search(query, k=5)

    hybrid_results = merge_results(vector_results, bm25_results)

    return {"hybrid_docs": hybrid_results}





def rerank_node(state: ResearchState, *, reranker) -> dict:

    query = state.get("rewritten_query") or state["query"]
    hybrid_docs = state["hybrid_docs"]

    reranked_results = reranker.rerank(query, hybrid_docs, top_k=5)

    reranked_docs = [doc for doc, _ in reranked_results]

    return {"reranked_docs": reranked_docs}




def grade_documents_node(state: ResearchState, *, relevance_grader) ->dict:

    query = state.get("rewritten_query") or state["query"]
    reranked_docs = state["reranked_docs"]

    relevant_docs =[]
    for doc in reranked_docs:
        is_relevant = relevance_grader.grade(query=query, 
                                             document= doc.page_content)

        if is_relevant:
            relevant_docs.append(doc)

    return {"relevant_docs": relevant_docs}




def rewrite_query_node(state: ResearchState, *, query_rewriter) -> dict:

    current_query = state.get("rewritten_query") or state["query"]

    rewritten_query = query_rewriter.rewrite(current_query)

    rewrite_count = state.get("rewrite_count", 0) + 1

    return { "rewritten_query": rewritten_query,
             "rewrite_count": rewrite_count }




def query_analysis_node(state: ResearchState, *, query_router) -> dict:

    route = query_router.route(state["query"])

    return {"route": route}




def web_search_node(state: ResearchState, *, web_search) -> dict:

    query = state.get("rewritten_query") or state["query"]

    results = web_search.search_and_fetch(query=query, max_results=3)

    return {"web_results": results}




def generate_answer_node(state: ResearchState, *, answer_generator) -> dict:

    query= state["query"]

    relevant_docs = state.get("relevant_docs", [])
    web_results = state.get("web_results", [])

    evidence_parts = []
    citations = []

    if web_results:
        for i, result in enumerate(web_results, start=1):
            content = (result.get("text") or result.get("content") or "")

            if not content:
                continue

            evidence_parts.append(f"[Web Source{i}]\n{content}")

            citations.append(
                {"type": "web",
                 "title": result.get("title"),
                 "url": result.get("url"),}
            )

    else:
        for i, doc in enumerate(relevant_docs, start=1):
            evidence_parts.append(
                f"[Documentation Source {i}]\n"
                f"{doc.page_content}"
            )

            citations.append(
                {"type": "documentation",
                 "source": doc.metadata.get("source"),
                 "page": doc.metadata.get("page_label"),}
            )


    evidence = "\n\n".join(evidence_parts)

    answer = answer_generator.generate(query=query, evidence=evidence)

    return {"answer": answer, "citations": citations}
