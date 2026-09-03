from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GRADER_MODEL


class RelevanceGrade(BaseModel):
    relevant: bool = Field(
        description="Whether the document is relevant to the user's question."
    )


class RelevanceGrader:
    def __init__(self):
        llm = ChatGoogleGenerativeAI(model=GRADER_MODEL)
        self.grader = llm.with_structured_output(RelevanceGrade)


    def grade(self, query: str, document: str) -> bool:
        prompt = f"""
You are evaluating whether a retrieved technical documentation
chunk is useful for answering a user's question.

Question:
{query}

Document:
{document}

Mark the document as relevant only if it directly helps answer
the user's question at the scope requested.

Rules:
- The document should contain information that materially contributes
  to answering the question.
- For broad questions, a document that only describes one specialized
  subtype, provider, implementation, or example should not be marked
  relevant unless it also helps explain the broader concept.
- Do not mark a document relevant merely because it contains similar
  words or terminology.
"""

        result = self.grader.invoke(prompt)
        return result.relevant





class FaithfulnessGrade(BaseModel):
    faithful: bool = Field(
        description=(
            "True if the answer is fully supported by the supplied evidence "
            "and does not introduce unsupported factual claims"
        )
    )


class FaithfulnessGrader:
    def __init__(self):
        llm = ChatGoogleGenerativeAI(model=GRADER_MODEL)

        self.grader = llm.with_structured_output(FaithfulnessGrade)



    def grade(self, query: str, answer: str, evidence: str) -> bool:
        prompt= f"""
You are evaluating whether an answer is faithful to the supplied evidence.

A faithful answer:
- makes factual claims supported by the evidence
- does not invent facts
- does not add unsupported technical details
- may explicitly state that the evidence is insufficient

Do not judge whether the answer is useful or well written.
Judge only grounding and factual support.

Question:
{query}

Evidence:
{evidence}

Answer:
{answer}
"""

        result = self.grader.invoke(prompt)
        return result.faithful








class UsefulnessGrade(BaseModel):
    useful: bool = Field(
        description=(
            "True if the answer directly and sufficiently addresses "
            "the user's question."
        )
    )


class UsefulnessGrader:
    def __init__(self):
        llm = ChatGoogleGenerativeAI(model=GRADER_MODEL)

        self.grader = llm.with_structured_output(UsefulnessGrade)


    def grade(self, query: str, answer: str) -> bool:

        prompt= f"""
You are evaluating whether an answer is useful to the user.

A useful answer:
- directly addresses the user's question
- provides enough relevant information to be helpful
- avoids unnecessary tangents
- clearly communicates when the available evidence is insufficient

Do not evaluate factual grounding here.
Judge only whether the answer appropriately answers the question.

Question:
{query}

Answer:
{answer}
"""

        result = self.grader.invoke(prompt)
        return result.useful





class WebEvidenceGrade(BaseModel):
    relevant: bool = Field(
        description=(
            "Whether the web result directly provides evidence for the user's "
            "exact question and stays within the requested technology or entity scope."
        )
    )


class WebEvidenceGrader:
    def __init__(self):
        llm = ChatGoogleGenerativeAI(model=GRADER_MODEL)
        self.grader = llm.with_structured_output(WebEvidenceGrade)



    def grade(self, *, query: str, title: str, url: str, content: str,) -> bool:
        prompt = f"""
You are grading web evidence for a technical research assistant.

Determine whether this web result directly provides evidence relevant
to the user's exact question.

Be strict about entity and technology scope.

Rules:
- The result must concern the exact SDK, library, product, technology,
  or organization requested by the user.
- Do not treat a related third-party SDK or adjacent technology as the
  requested technology.
- Keyword overlap alone is not enough.
- For questions asking about recent changes, the result must actually
  contain information about the requested change.
- General pages that merely mention the technology are not sufficient.

User question:
{query}

Result title:
{title}

Result URL:
{url}

Result content:
{content[:3000]}
"""

        result = self.grader.invoke(prompt)
        return result.relevant