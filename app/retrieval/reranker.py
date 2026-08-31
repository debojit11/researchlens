from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(self, 
                 model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)


    def rerank(self, query: str, documents, top_k: int = 5):
        pairs= [(query, doc.page_content) for doc in documents]

        scores = self.model.predict(pairs)

        ranked= sorted(zip(documents, scores),
                       key=lambda item: item[1], reverse=True)

        return ranked[:top_k]