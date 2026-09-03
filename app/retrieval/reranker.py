from FlagEmbedding import FlagReranker


class Reranker:
    def __init__(self):
        self.model = FlagReranker("BAAI/bge-reranker-base", use_fp16=False,)

    def rerank(self, query, documents, top_k=5):
        if not documents:
            return []

        pairs = [[query, doc.page_content] for doc in documents]

        scores = self.model.compute_score(pairs)

        ranked_results = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return ranked_results[:top_k]