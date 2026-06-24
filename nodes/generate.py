import os
import random

from dotenv import load_dotenv

load_dotenv()

PROMPT = """Write one engaging tweet (max 280 characters, max 3 relevant hashtags) based on this item.
Source: {source}
Title: {title}
URL: {url}

Reply with ONLY the tweet text, no surrounding quotes."""


def _mock_draft(item):
    return f"{item['title']} — {item['url']}"[:280]


def generate_node(state):
    item = random.choice(state["research_data"])
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        draft = _mock_draft(item)
    else:
        from langchain_groq import ChatGroq

        llm = ChatGroq(model="llama-3.1-8b-instant", api_key=api_key)
        draft = llm.invoke(PROMPT.format(**item)).content.strip().strip('"')[:280]

    state["selected_draft"] = draft
    state["tweet_drafts"] = state.get("tweet_drafts", []) + [draft]
    state.setdefault("retry_count", 0)
    return state


if __name__ == "__main__":
    os.environ.pop("GROQ_API_KEY", None)  # deterministic no-LLM path for the check
    item = {"title": "Test headline", "url": "https://example.com", "source": "mock"}
    result = generate_node({"research_data": [item]})
    assert len(result["selected_draft"]) <= 280
    assert "https://example.com" in result["selected_draft"]  # draft is grounded in the sourced item
    print(result["selected_draft"])
