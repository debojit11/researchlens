from datetime import datetime, timezone

from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GENERATOR_MODEL


class AnswerGenerator:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model=GENERATOR_MODEL)

    async def generate(self, query: str, evidence: str,) -> str:
        current_date = datetime.now(timezone.utc).date().isoformat()

        prompt = f"""
You are a technical research assistant.

Answer the user's question using only the evidence provided below.

Current date:
{current_date}

Rules:
- Do not use information that is not supported by the evidence.
- If the evidence is insufficient, clearly say so.
- Be technically precise.
- Prefer evidence that directly addresses the full scope of the user's question.
- Use narrower or specialized evidence only as supporting detail.
- Do not let a specialized case dominate the answer when broader evidence is available.

- For freshness-sensitive questions such as "today", "this week",
  "latest", "recent", "recently", "newest", or "current", preserve
  relevant temporal evidence in the answer.

- Treat "this week" and similar recent-window questions as a rolling
  7-day window ending on the current date.

- When individual evidence items contain dates, include only items
  whose dates fall inside the requested time window.

- Do not include older dated changes simply because they appear on
  the same changelog, release page, or document as newer changes.

- When the evidence provides a publication date, release date,
  changelog date, commit date, or equivalent timestamp, include that
  date when needed to justify the requested time scope.

- Do not describe something as happening "this week", "recently", or
  being "latest" unless the supplied evidence supports that claim.

- Do not invent dates or infer dates that are not present in the evidence.
- Do not invent citations or source names.
- Do not mention that you are an AI.
- Do not include a separate sources section.
- Citation metadata will be handled separately by the application.

Question:
{query}

Evidence:
{evidence}
"""

        response = await self.llm.ainvoke(prompt)

        return response.text.strip()