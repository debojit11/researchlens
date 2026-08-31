from rank_bm25 import BM25Okapi


class BM25Retriever:
    def __init__(self, chunks):
        self.chunks= chunks

        self.tokenized_chunks= [chunk.page_content.lower().split()
                                for chunk in chunks]

        self.bm25= BM25Okapi(self.tokenized_chunks)


    def search(self, query: str, k: int=5):
        tokenized_query = query.lower().split()

        scores= self.bm25.get_scores(tokenized_query)

        ranked_indices = sorted(range(len(scores)), 
                                key=lambda i: scores[i],
                                reverse=True)[:k]

        return [self.chunks[i] for i in ranked_indices]