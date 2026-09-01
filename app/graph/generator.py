from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GENERATOR_MODEL



class AnswerGenerator:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model=GENERATOR_MODEL)



    def generate(self, query: str, evidence: str) -> str:
        prompt=f"""
You are a technical research assistant.

Answer the user's question using only the evidence provided below.

Rules:
- Do not use information that is not supported by the evidence.
- If the evidence is insufficient, clearly say so.
- Be technically precise.
- Do not invent citations or source names.
- Do not mention that you are an AI.
- Do not include a separate sources section.
- Citation metadata will be handled separately by the application.

Question:
{query}

Evidence:
{evidence}
"""

        response = self.llm.invoke(prompt)
        return response.text.strip()