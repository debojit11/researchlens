from app.config import MIN_RELEVANT_DOCS, MAX_REWRITES
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