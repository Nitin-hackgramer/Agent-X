import urllib.parse
from datetime import date, timedelta

import feedparser
import httpx

BBC_TECH_RSS = "https://feeds.bbci.co.uk/news/technology/rss.xml"


def _parse_feed(source, url, limit=5):
    items = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit]:
            items.append({"title": entry.title, "url": entry.link, "source": source})
    except Exception:
        pass  # ponytail: one dead feed shouldn't kill the run
    return items


def _google_news_search(query, limit=5):
    # Google News RSS supports keyword search → real article URLs from legit outlets
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    return _parse_feed("GoogleNews", url, limit)


def _hn_search(query, limit=5):
    # HN Algolia search → best source for tech topics mainstream news ignores
    try:
        q = urllib.parse.quote(query)
        r = httpx.get(f"https://hn.algolia.com/api/v1/search?query={q}&tags=story", timeout=10)
        items = []
        for h in r.json().get("hits", [])[:limit]:
            if not h.get("title"):
                continue
            url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            items.append({"title": h["title"], "url": url, "source": "HackerNews"})
        return items
    except Exception:
        return []


def _github_trending(limit=3):
    # repos with the most stars created in the last week ≈ "going viral"
    try:
        since = (date.today() - timedelta(days=7)).isoformat()
        r = httpx.get(
            "https://api.github.com/search/repositories",
            params={"q": f"created:>{since}", "sort": "stars", "order": "desc", "per_page": limit},
            headers={"Accept": "application/vnd.github+json"},
            timeout=10,
        )
        items = []
        for repo in r.json().get("items", [])[:limit]:
            desc = (repo.get("description") or "").strip()
            items.append({
                "title": f"{repo['full_name']} ({repo['stargazers_count']} stars): {desc}".strip(),
                "url": repo["html_url"],
                "source": "GitHub",
            })
        return items
    except Exception:
        return []


def _huggingface_trending(limit=3):
    # Hugging Face trending models → the canonical source for "new models"
    try:
        r = httpx.get(
            "https://huggingface.co/api/models",
            params={"sort": "trendingScore", "direction": -1, "limit": limit},
            timeout=10,
        )
        items = []
        for m in r.json()[:limit]:
            mid = m.get("id") or m.get("modelId")
            if not mid:
                continue
            items.append({
                "title": f"Trending AI model on Hugging Face: {mid}",
                "url": f"https://huggingface.co/{mid}",
                "source": "HuggingFace",
            })
        return items
    except Exception:
        return []


def _fetch_quote():
    try:
        r = httpx.get("https://zenquotes.io/api/random", timeout=10)
        q = r.json()[0]
        return [{"title": f'"{q["q"]}" — {q["a"]}', "url": "https://zenquotes.io", "source": "ZenQuotes"}]
    except Exception:
        return []


def _hn_top(limit=3):
    try:
        ids = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()[:limit]
        items = []
        for i in ids:
            s = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json", timeout=10).json()
            items.append({"title": s.get("title", ""), "url": s.get("url", f"https://news.ycombinator.com/item?id={i}"), "source": "HackerNews"})
        return items
    except Exception:
        return []


def research_node(state):
    feedback = state.get("rejection_feedback")
    if feedback:
        # ponytail: whole feedback string as query; add keyword extraction if results get noisy
        data = _google_news_search(feedback) + _hn_search(feedback)
    else:
        # tech-focused default mix: tech news, viral repos, new models, latest AI, coding insights, quote
        data = (
            _parse_feed("BBC Tech", BBC_TECH_RSS, 2)
            + _github_trending(3)
            + _huggingface_trending(3)
            + _google_news_search("new AI model release OR LLM OR AI engineering when:7d", 3)
            + _hn_top(3)
            + _fetch_quote()
        )

    if not data:
        data = [{"title": f"No sources found for: {feedback or 'top news'}", "url": "https://example.com", "source": "mock"}]
    state["research_data"] = data
    return state


if __name__ == "__main__":
    default = research_node({})
    assert default["research_data"], "expected default research items"
    sources = {i["source"] for i in default["research_data"]}
    assert {"GitHub", "HuggingFace", "GoogleNews"} & sources, f"default mix should include tech/AI sources, got {sources}"
    targeted = research_node({"rejection_feedback": "Claude Code AI agent"})
    assert targeted["research_data"], "expected feedback-targeted items"
    assert any(i["source"] in ("GoogleNews", "HackerNews") for i in targeted["research_data"]), "feedback search should hit real search sources"
    print("DEFAULT:")
    for i in default["research_data"]:
        print(f"  [{i['source']}] {i['title']} ({i['url']})")
    print("TARGETED (feedback='Claude Code AI agent'):")
    for i in targeted["research_data"]:
        print(f"  [{i['source']}] {i['title']} ({i['url']})")
