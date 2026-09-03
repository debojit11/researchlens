from functools import lru_cache
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GRADER_MODEL


class AnswerBehaviorGrade(BaseModel):
    passed: bool = Field(
        description=(
            "True if the answer satisfies the expected behavior and "
            "correctly addresses the exact scope of the user's question."
        )
    )

    reason: str = Field(
        description="A short explanation of why the answer passed or failed."
    )


@lru_cache
def get_answer_behavior_judge():
    llm = ChatGoogleGenerativeAI(model=GRADER_MODEL)

    return llm.with_structured_output(AnswerBehaviorGrade)


def answer_behavior_evaluator(inputs: dict, outputs: dict, reference_outputs: dict,) -> dict:

    judge = get_answer_behavior_judge()

    query = inputs["query"]
    answer = outputs.get("answer", "")
    expected_behavior = reference_outputs["expected_behavior"]

    prompt = f"""
You are independently evaluating the final answer produced by a
technical research assistant.

Evaluate whether the final answer satisfies the expected answer behavior.

Pay particular attention to:

- whether it directly addresses the user's question
- whether it stays within the exact entity, library, SDK, product,
  technology, or technical scope requested
- whether it avoids substituting a related but different technology
- whether temporal claims such as "latest", "recent", or "this week"
  are appropriately addressed
- whether an insufficient-evidence response is appropriate when the
  requested information is not supported

Do not judge whether the system selected the correct retrieval route.
Routing is evaluated separately.

Do not automatically pass an answer merely because it sounds
technically plausible.

User question:
{query}

Expected answer behavior:
{expected_behavior}

Final answer:
{answer}
"""

    result = judge.invoke(prompt)

    return {
        "key": "answer_behavior",
        "score": int(result.passed),
        "comment": result.reason,
    }