from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GRADER_MODEL
from datetime import datetime, timezone


class RelevanceGrade(BaseModel):
    relevant: bool = Field(
        description="Whether the document is relevant to the user's question."
    )


class RelevanceGrader:
    def __init__(self):
        llm = ChatGoogleGenerativeAI(model=GRADER_MODEL)
        self.grader = llm.with_structured_output(RelevanceGrade)


    async def grade(self, query: str, document: str) -> bool:
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

        result = await self.grader.ainvoke(prompt)
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



    async def grade(self, query: str, answer: str, evidence: str) -> bool:
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

        result = await self.grader.ainvoke(prompt)
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


    async def grade(self, query: str, answer: str) -> bool:

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

        result = await self.grader.ainvoke(prompt)
        return result.useful





class WebEvidenceGrade(BaseModel):
    scope_match: bool = Field(
        description=(
            "Whether the result concerns the exact SDK, library, product, "
            "technology, or organization requested by the user."
        )
    )

    content_match: bool = Field(
        description=(
            "Whether the result actually contains evidence that answers "
            "the substance of the user's question."
        )
    )

    temporal_match: bool = Field(
        description=(
            "Whether the result satisfies the requested freshness or time window. "
            "For non-time-sensitive questions, this should be true."
        )
    )


class WebEvidenceGrader:
    def __init__(self):
        llm = ChatGoogleGenerativeAI(model=GRADER_MODEL)
        self.grader = llm.with_structured_output(WebEvidenceGrade)



    async def grade(self, *, query: str, title: str, url: str, content: str,) -> bool:

        current_date = datetime.now(timezone.utc).date().isoformat()

        prompt = f"""
    You are grading web evidence for a technical research assistant.

    Evaluate the result against THREE independent requirements:

    1. SCOPE MATCH
    2. CONTENT MATCH
    3. TEMPORAL MATCH

    Be strict. A result is usable only when all required conditions are satisfied.

    Current date:
    {current_date}

    SCOPE MATCH rules:
    - The result must concern the exact SDK, library, product, technology,
    organization, or official ecosystem requested by the user.
    - A third-party package that integrates with or targets the requested
    technology is NOT automatically the requested technology.
    - For example, a third-party package for Amazon Bedrock is not itself
    an AWS SDK merely because it contains "AWS", "Bedrock", or SDK terminology.
    - Do not substitute adjacent technologies, wrappers, integrations,
    unofficial packages, or similarly named projects.
    - Keyword overlap alone is not enough.

    CONTENT MATCH rules:
    - The result must contain information that materially answers the
    specific question.
    - If the user asks what changed, the result must describe an actual
    change, release, modification, fix, behavior update, or documented
    difference.
    - A general documentation page that only explains the technology is
    not evidence of a change.
    - A page merely mentioning the requested subject is insufficient.
    - If the user asks for the latest or current version of an SDK or library,
    the result must provide evidence that identifies the current/latest
    release for the relevant active major version or overall product.
    - A documentation page that merely contains a version number is not enough.
    - Do not treat an old or end-of-support major version as the current/latest
    SDK merely because the page title or URL contains "latest".

   TEMPORAL MATCH rules:
    - If the question is not time-sensitive, temporal_match should be true.
    - If the question contains terms such as "today", "this week", "latest",
    "recent", "recently", "newest", or "current", the result should provide
    usable temporal evidence such as a publication date, release date,
    changelog date, commit date, or equivalent timestamp.
    - For "this week", strongly prefer evidence from roughly the most recent
    7-day period.
    - Slightly older evidence may still count as temporal_match if it is
    clearly recent, directly relevant to the requested change, and appears
    to represent a meaningful or latest available update.
    - Do not accept substantially old evidence as satisfying a freshness-sensitive
    request merely because it is relevant.
    - For "latest" or "current version" questions, temporal_match should be true
    only when the result provides evidence that the version is current/latest,
    or provides a recent release/version listing that allows that conclusion.
    - A URL or page title containing the word "latest" is not sufficient evidence
    by itself.
    - If evidence is slightly older than the requested window, temporal_match
    may still be true, but the final answer should state the exact date rather
    than imply that it happened strictly within the requested week.
    - If no usable date or temporal evidence is present, temporal_match
    should be false for a freshness-sensitive question.
    - Do not infer freshness merely because a search engine returned the page.

    User question:
    {query}

    Result title:
    {title}

    Result URL:
    {url}

    Result content:
    {content[:6000]}
    """

        result = await self.grader.ainvoke(prompt)

        # print("\nWEB EVIDENCE GRADE")
        # print("=" * 60)
        # print("Title:", title)
        # print("URL:", url)
        # print("Scope match:", result.scope_match)
        # print("Content match:", result.content_match)
        # print("Temporal match:", result.temporal_match)

        return (
            result.scope_match
            and result.content_match
            and result.temporal_match
        )