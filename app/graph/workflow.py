from functools import partial
from langgraph.graph import StateGraph, START, END
from app.state import ResearchState

from app.graph.nodes import (
    hybrid_retrieval_node,
    rerank_node,
    grade_documents_node,
    rewrite_query_node,
    query_analysis_node,
    web_search_node,
    generate_answer_node,)

from app.graph.routes import route_after_grading, route_query




def build_research_graph(*, vector_store, bm25_retriever, reranker,
                         relevance_grader, query_rewriter, query_router,
                         web_search, answer_generator):

    graph = StateGraph(ResearchState)

    retrieve_node = partial(hybrid_retrieval_node,
                            vector_store=vector_store,
                            bm25_retriever=bm25_retriever)

    rerank_graph_node = partial(rerank_node, reranker=reranker)

    grade_node = partial(grade_documents_node,
                         relevance_grader=relevance_grader)

    rewrite_node= partial(rewrite_query_node,
                          query_rewriter=query_rewriter)

    query_node = partial(query_analysis_node, query_router=query_router)

    web_node = partial(web_search_node, web_search=web_search)

    generate_node = partial(generate_answer_node,
                            answer_generator=answer_generator)




    graph.add_node("retrieve", retrieve_node)
    graph.add_node("rerank", rerank_graph_node)
    graph.add_node("grade", grade_node)
    graph.add_node("rewrite", rewrite_node)
    graph.add_node("query_analysis", query_node)
    graph.add_node("web_search", web_node)
    graph.add_node("generate", generate_node)



    graph.add_edge(
        START,
        "query_analysis",
    )

    graph.add_conditional_edges(
        "query_analysis",
        route_query,
        {
            "documentation": "retrieve",
            "web": "web_search",
        }
    )

    graph.add_edge(
        "retrieve",
        "rerank",
    )

    graph.add_edge(
        "rerank",
        "grade",
    )

    graph.add_conditional_edges(
        "grade",
        route_after_grading,
        {
            "enough": "generate",
            "rewrite": "rewrite",
            "fallback": "web_search",
        }
    )

    graph.add_edge(
        "rewrite",
        "retrieve",
    )

    graph.add_edge(
        "web_search",
        "generate",
    )

    graph.add_edge(
        "generate",
        END,
    )


    return graph.compile()