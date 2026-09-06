import asyncio
import os

import httpx


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

        self.headers = {"X-API-Key": api_key}


    async def search(self, query: str, max_results: int = 5,) -> list[dict]:

        if self.is_version_query(query):
            purpose = (
                "Find authoritative evidence for the current or latest stable version "
                "of the exact SDK, library, product, or technology named in the question. "
                "Prefer official release pages, official changelogs, package registries, "
                "or the project's official GitHub releases. "
                "Do not substitute another SDK, major version, or adjacent package."
            )

        elif needs_fresh_search(query):
            purpose = (
                "Find recent, dated technical evidence that directly matches the exact "
                "technology, SDK, product, or library named in the user's question. "
                "Prefer official changelogs, release notes, GitHub release histories, "
                "official announcements, or other sources that contain explicit dates. "
                "Do not substitute related third-party SDKs or adjacent technologies."
            )

        else:
            purpose = (
                "Find technical information that directly matches the exact technology, "
                "SDK, product, or library named in the user's question. "
                "Do not substitute related third-party SDKs or adjacent technologies."
            )

        params = {"query": query, "purpose": purpose}

        if needs_fresh_search(query) and not self.is_version_query(query):
            params["recency_minutes"] = 10080

        response = await self._request_with_retry(
            "GET",
            SEARCH_URL,
            headers=self.headers,
            params=params,
            timeout=30,
        )

        data = response.json()
        return data.get("results", [])[:max_results]


    async def fetch(self, urls: list[str], live: bool = False,) -> list[dict]:

        payload = {"urls": urls, "format": "markdown"}

        if live:
            payload["ttl"] = 0

        response = await self._request_with_retry(
            "POST",
            FETCH_URL,
            headers={
                **self.headers,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )

        data = response.json()
        return data.get("results", [])


    def is_version_query(self, query: str) -> bool:
        query_lower = query.lower()

        return any(
            term in query_lower
            for term in (
                "latest version",
                "latest stable version",
                "current version",
                "newest version",
            )
        )


    async def search_and_fetch(self, query: str, max_results: int = 6,) -> list[dict]:

        queries = [query]

        if self.is_version_query(query):
            queries.append(f"{query} releases versions Maven GitHub")
        elif needs_fresh_search(query):
            queries.append(f"{query} changelog release notes")

        search_results = []

        for search_query in queries:
            results = await self.search(
                query=search_query,
                max_results=3,
            )
            search_results.extend(results)

        urls = []
        seen_urls = set()

        for result in search_results:
            url = result.get("url")

            if url and url not in seen_urls:
                seen_urls.add(url)
                urls.append(url)

        urls = urls[:max_results]

        if not urls:
            return []

        fresh = needs_fresh_search(query)

        return await self.fetch(urls, live=fresh)


    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        max_attempts: int = 3,
        **kwargs,
    ):
        for attempt in range(1, max_attempts + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(method, url, **kwargs)

                response.raise_for_status()
                return response

            except asyncio.CancelledError:
                # Never retry a request that the user explicitly stopped.
                raise

            except httpx.HTTPError:
                if attempt == max_attempts:
                    raise

                wait_seconds = 2 ** (attempt - 1)
                await asyncio.sleep(wait_seconds)
