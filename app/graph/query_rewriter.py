from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import REWRITER_MODEL



class QueryRewriter:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model= REWRITER_MODEL)



    async def rewrite(self, query: str) -> str:
        prompt=f"""
You are rewriting a user's technical question to improve
retrieval from technical documentation.

Original question:
{query}

Rewrite the question so that it is:
- clear and specific
- likely to match terminology used in technical documentation
- faithful to the user's original intent

Do not answer the question.
Return only the rewritten question.
"""

        response = await self.llm.ainvoke(prompt)
        return response.text.strip()