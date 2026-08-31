def merge_results(vector_results, bm25_results):
    combined=[]
    seen=set()

    for doc in vector_results + bm25_results:
        key=(doc.metadata.get("source"),
             doc.metadata.get("page"),
             doc.page_content,)

        if key not in seen:
            seen.add(key)
            combined.append(doc)

    return combined