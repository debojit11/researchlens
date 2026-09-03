from app.config import MIN_RELEVANT_DOCS, MAX_REWRITES, MAX_GENERATION_ATTEMPTS
from app.state import ResearchState




def route_after_grading(state: ResearchState) -> str:

    relevant_docs = state.get("relevant_docs", [])
    rewrite_count = state.get("rewrite_count", 0)

    if len(relevant_docs) >= MIN_RELEVANT_DOCS:
        return "enough"

    if rewrite_count < MAX_REWRITES:
        return "rewrite"
    return "fallback"



def route_query(state: ResearchState) -> str:
    return state["route"]




def route_after_faithfulness(state: ResearchState) -> str:
    faithful = state.get("faithful", False)
    generation_attempts = state.get("generation_attempts", 0)

    if faithful:
        return "usefulness"
    if generation_attempts < MAX_GENERATION_ATTEMPTS:
        return "retry"
    return "failed"




def route_after_usefulness(state: ResearchState) -> str:
    useful = state.get("useful", False)
    generation_attempts = state.get("generation_attempts", 0)

    if useful:
        return "done"
    if generation_attempts < MAX_GENERATION_ATTEMPTS:
        return "retry"
    return "failed"



def route_after_web_search(state: ResearchState) -> str:
    if state.get("web_results"):
        return "generate"

    return "insufficient"