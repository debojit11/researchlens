from dotenv import load_dotenv
from langsmith import Client

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
from app.graph.generator import AnswerGenerator
from app.graph.workflow import build_research_graph
from app.web.search import TinyFishSearch
from evals.evaluators import answer_behavior_evaluator
from app.config import DATA_DIR


DATASET_NAME = "researchlens-v1-eval"


def build_app():
    chunks = load_pdf_v2(str(DATA_DIR / "sample.pdf"))

    if vector_store_exists():
        vector_store = load_vector_store()
    else:
        vector_store = create_vector_store(chunks)

    bm25_retriever = BM25Retriever(chunks)
    reranker = Reranker()

    relevance_grader = RelevanceGrader()
    faithfulness_grader = FaithfulnessGrader()
    usefulness_grader = UsefulnessGrader()
    web_evidence_grader = WebEvidenceGrader()

    query_rewriter = QueryRewriter()
    query_router = QueryRouter()
    answer_generator = AnswerGenerator()
    web_search = TinyFishSearch()

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

    return graph


def route_evaluator(inputs: dict, outputs: dict, reference_outputs: dict,) -> dict:

    expected_route = reference_outputs["expected_route"]
    actual_route = outputs.get("route")

    return {
        "key": "route_accuracy",
        "score": int(actual_route == expected_route),
    }



def faithfulness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict,) -> dict:
    generation_attempts = outputs.get("generation_attempts", 0)

    if generation_attempts == 0:
        return {"key": "faithfulness", "score": None,}

    return {"key": "faithfulness", "score": int(outputs.get("faithful") is True),}


def usefulness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict,) -> dict:
    generation_attempts = outputs.get("generation_attempts", 0)

    if generation_attempts == 0:
        return {"key": "usefulness", "score": None,}

    return {"key": "usefulness", "score": int(outputs.get("useful") is True),}



def main():
    load_dotenv()

    client = Client()
    graph = build_app()

    def target(inputs: dict) -> dict:
        result = graph.invoke(
            {
                "query": inputs["query"],
                "rewrite_count": 0,
                "generation_attempts": 0,
            }
        )

        return {
            "answer": result.get("answer"),
            "route": result.get("route"),
            "faithful": result.get("faithful"),
            "useful": result.get("useful"),
            "generation_attempts": result.get("generation_attempts"),
            "rewrite_count": result.get("rewrite_count"),
            "citations": result.get("citations", [],),
        }

    results = client.evaluate(target, data=DATASET_NAME,
        evaluators=[route_evaluator, faithfulness_evaluator, 
                    usefulness_evaluator, answer_behavior_evaluator],
        experiment_prefix="researchlens-v1",)

    print(results)


if __name__ == "__main__":
    main()