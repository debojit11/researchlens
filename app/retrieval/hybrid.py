def merge_results(vector_results, bm25_results, k: int = 60):
    scores = {}
    docs = {}

    for rank, doc in enumerate(vector_results, start=1):
        key = (
            doc.metadata.get("source"),
            doc.metadata.get("page"),
            doc.page_content,
        )

        docs[key] = doc
        scores[key] = scores.get(key, 0.0) + 1 / (k + rank)

    for rank, doc in enumerate(bm25_results, start=1):
        key = (
            doc.metadata.get("source"),
            doc.metadata.get("page"),
            doc.page_content,
        )

        docs[key] = doc
        scores[key] = scores.get(key, 0.0) + 1 / (k + rank)

    ranked_keys = sorted(scores, key=scores.get, reverse=True,)

    return [docs[key] for key in ranked_keys]