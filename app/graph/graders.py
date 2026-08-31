from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GRADER_MODEL


class RelevanceGrade(BaseModel):
    relevant: bool = Field(
        description="Whether the document is relevant to the user's question."
    )


class RelevanceGrader:
    def __init__(self):
        llm= ChatGoogleGenerativeAI(model=GRADER_MODEL)
        self.grader= llm.with_structured_output(RelevanceGrade)



    def grade(self, query: str, document: str) -> bool:
        prompt= f"""
You are evaluating whether a retrieved technical documentation
chunk is useful for answering a user's question.

Question:
{query}

Document:
{document}

Mark the document as relevant if it contains information that
would help answer the question.

Do not mark a document relevant merely because it contains
similar words or terminology.
"""

        result = self.grader.invoke(prompt)
        return result.relevant