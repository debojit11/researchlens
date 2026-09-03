from app.state import ResearchState
from app.retrieval.vector import vector_search
from app.retrieval.hybrid import merge_results



def hybrid_retrieval_node(state: ResearchState, *, vector_store, bm25_retriever,) -> dict:

    query = state.get("rewritten_query") or state["query"]

    vector_results = vector_search(vector_store, query, k=5)
    bm25_results = bm25_retriever.search(query, k=5)

    # print("\nVECTOR TOP 5")
    # print("=" * 50)
    # for i, doc in enumerate(vector_results, start=1):
    #     print(f"\n--- Vector {i} ---")
    #     print("Page:", doc.metadata.get("page_label"))
    #     print(doc.page_content[:500])

    # print("\nBM25 TOP 5")
    # print("=" * 50)
    # for i, doc in enumerate(bm25_results, start=1):
    #     print(f"\n--- BM25 {i} ---")
    #     print("Page:", doc.metadata.get("page_label"))
    #     print(doc.page_content[:500])

    hybrid_results = merge_results(vector_results, bm25_results)

    # print("\nMERGED RESULTS")
    # print("=" * 50)
    # for i, doc in enumerate(hybrid_results, start=1):
    #     print(f"\n--- Merged {i} ---")
    #     print("Page:", doc.metadata.get("page_label"))
    #     print(doc.page_content[:500])

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




def web_search_node(state, *, web_search, web_evidence_grader):
    results = web_search.search_and_fetch(state["query"])

    filtered_results = []

    for result in results:
        content = result.get("text", "") or result.get("content", "")

        if not content.strip():
            continue

        relevant = web_evidence_grader.grade(
            query=state["query"],
            title=result.get("title", ""),
            url=result.get("url", ""),
            content=content,
        )

        if relevant:
            filtered_results.append(result)

    return {"web_results": filtered_results}




def build_evidence(state: ResearchState) -> str:
    relevant_docs= state.get("relevant_docs", [])
    web_results = state.get("web_results", [])

    evidence_parts = []

    if web_results:
        for i, result in enumerate(web_results, start=1):
            content=(result.get("text") or result.get("content") or "")

            if not content:
                continue

            evidence_parts.append(f"[Web Source {i}]\n{content}")

    else:
        for i, doc in enumerate(relevant_docs, start=1):
            evidence_parts.append(f"[Documentation Source {i}]\n"
                                  f"{doc.page_content}")

    return "\n\n".join(evidence_parts)





def generate_answer_node(state: ResearchState, *, answer_generator) -> dict:

    query= state["query"]

    relevant_docs = state.get("relevant_docs", [])
    web_results = state.get("web_results", [])

    citations = []

    if web_results:
        for result in web_results:
            content = (result.get("text") or result.get("content") or "")

            if not content:
                continue

            citations.append(
                {"type": "web",
                 "title": result.get("title"),
                 "url": result.get("url"),}
            )

    else:
        for doc in relevant_docs:
            citations.append(
                {
                    "type": "documentation",
                    "source": doc.metadata.get("source"),
                    "section": doc.metadata.get("section"),
                    "page_start": doc.metadata.get("section_page_start"),
                    "page_end": doc.metadata.get("section_page_end"),
                }
            )


    evidence = build_evidence(state)

    answer = answer_generator.generate(query=query, evidence=evidence)

    generation_attempts = (state.get("generation_attempts", 0) + 1)

    return {"answer": answer, "citations": citations, "generation_attempts": generation_attempts}




def faithfulness_check_node(state: ResearchState, *, faithfulness_grader) -> dict:
    evidence = build_evidence(state)

    faithful = faithfulness_grader.grade(query=state["query"],
                                         answer=state["answer"],
                                         evidence=evidence)

    return {"faithful": faithful}




def usefulness_check_node(state: ResearchState, *, usefulness_grader) -> dict:
    useful = usefulness_grader.grade(query= state["query"],
                                    answer=state["answer"])

    return {"useful": useful}




def quality_failure_node(state: ResearchState) -> dict:
    return{
        "answer": (
            "I couldn't produce an answer that passed the required "
            "grounding and quality checks using the available evidence."
        ),
        "citations": [],
    }



def insufficient_evidence_node(state: ResearchState) -> dict:
    return {
        "answer": (
            "I couldn't find sufficient evidence to answer this question reliably."
        ),
        "citations": [],
    }