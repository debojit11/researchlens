import os
import requests


SEARCH_URL = "https://api.search.tinyfish.ai"
FETCH_URL = "https://api.fetch.tinyfish.ai"


FRESHNESS_TERMS = (
    "today",
    "this week",
    "latest",
    "recent",
    "recently",
    "newest",
    "current",
)


def needs_fresh_search(query: str) -> bool:
    query_lower = query.lower()
    return any(term in query_lower for term in FRESHNESS_TERMS)



class TinyFishSearch:
    def __init__(self):
        api_key = os.getenv("TINYFISH_API_KEY")

        if not api_key:
            raise ValueError("TINYFISH_API_KEY is not set")

        self.headers ={"X-API-Key": api_key}



    def search(self, query: str, max_results: int = 5,) -> list[dict]:

        params = {"query": query,
            "purpose": "Find up-to-date technical information relevant to the user's question.",
        }

        if needs_fresh_search(query):
            params["recency_minutes"] = 10080  # 7 days

        response = requests.get(SEARCH_URL, headers=self.headers,
            params=params,
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        return data.get("results", [])[:max_results]



    def fetch(self, urls: list[str], live: bool = False,) -> list[dict]:

        payload = {"urls": urls,"format": "markdown",}

        if live:
            payload["ttl"] = 0

        response = requests.post(FETCH_URL,
            headers={
                **self.headers,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )

        response.raise_for_status()
        data = response.json()

        return data.get("results", [])



    def search_and_fetch(self, query: str, max_results: int = 3,) -> list[dict]:

        search_results = self.search(query=query, max_results=max_results,)

        urls = [result["url"] for result in search_results
            if result.get("url")]

        if not urls:
            return []

        fresh = needs_fresh_search(query)
        fetched_results = self.fetch(urls, live=fresh,)

        return fetched_results