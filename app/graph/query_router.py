from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from app.config import ROUTER_MODEL, DOCS_DESCRIPTION




class QueryRoute(BaseModel):
    route: Literal["documentation", "web"] = Field(
        decription="Where the user's question should be answered from."
    )


class QueryRouter:
    def __init__(self):
        llm = ChatGoogleGenerativeAI(model=ROUTER_MODEL)

        self.router = llm.with_structured_output(QueryRoute)


    async def route(self, query: str) -> str:
        prompt = f"""
You are routing technical research questions.

The system has an indexed documentation corpus described as:

{DOCS_DESCRIPTION}

Choose "documentation" when the question can reasonably be
answered from the indexed documentation.

Choose "web" when the question:
- asks for current or recently changed information
- asks about a topic outside the indexed documentation
- explicitly requires information from the internet
- depends on information newer than the indexed documentation

Do not answer the question.

Question:
{query}
"""
        result = await self.router.ainvoke(prompt)

        return result.route