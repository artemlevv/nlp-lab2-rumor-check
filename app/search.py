"""Look up public sources for a claim. Wikipedia first, then web search."""

from dataclasses import dataclass

import httpx

USER_AGENT = "nlp-lab2-rumor-check/1.0 (university lab)"


@dataclass
class Source:
    id: str
    title: str
    url: str
    text: str
    origin: str


def search(query: str, limit: int = 5) -> list[Source]:
    sources: list[Source] = []
    sources.extend(_wikipedia(query, lang="en"))
    if _looks_ukrainian(query):
        sources.extend(_wikipedia(query, lang="uk"))
    sources.extend(_web(query, limit=3))
    seen: set[str] = set()
    unique = []
    for source in sources:
        if source.url in seen:
            continue
        seen.add(source.url)
        unique.append(source)
        if len(unique) >= limit:
            break
    for i, source in enumerate(unique, start=1):
        source.id = f"S{i}"
    return unique


def _looks_ukrainian(text: str) -> bool:
    return any("а" <= ch <= "я" or ch in "іїєґ" for ch in text.lower())


def _wikipedia(query: str, lang: str) -> list[Source]:
    try:
        with httpx.Client(timeout=15.0, headers={"User-Agent": USER_AGENT}) as client:
            found = client.get(
                f"https://{lang}.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": 2,
                    "utf8": 1,
                    "format": "json",
                },
            )
            found.raise_for_status()
            hits = found.json().get("query", {}).get("search", [])
            sources = []
            for hit in hits:
                title = hit["title"]
                page = client.get(
                    f"https://{lang}.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "prop": "extracts",
                        "exintro": 1,
                        "explaintext": 1,
                        "titles": title,
                        "format": "json",
                    },
                )
                page.raise_for_status()
                pages = page.json().get("query", {}).get("pages", {})
                extract = next(iter(pages.values()), {}).get("extract") or hit.get("snippet", "")
                url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
                sources.append(Source(id="", title=title, url=url, text=extract[:1200], origin="wikipedia"))
            return sources
    except httpx.HTTPError:
        return []


def _web(query: str, limit: int) -> list[Source]:
    try:
        from ddgs import DDGS

        hits = DDGS().text(query, max_results=limit)
    except Exception:
        return []
    sources = []
    for hit in hits:
        title = hit.get("title") or "web result"
        url = hit.get("href") or hit.get("url") or ""
        body = hit.get("body") or hit.get("snippet") or ""
        if not url:
            continue
        sources.append(Source(id="", title=title, url=url, text=body[:1200], origin="web"))
    return sources
