def main():
    print("Hello from twitter-agent!")


if __name__ == "__main__":
    main()

"""
twitter_agent/
├── main.py              # entry point
├── graph.py             # LangGraph graph definition
├── nodes/
│   ├── research.py      # Tavily search + quote fetch
│   ├── generate.py      # Groq tweet generation
│   ├── approval.py      # human gate (terminal for now)
│   └── post.py          # tweepy posting (v0.3+)
├── state.py             # LangGraph state definition
├── config.py            # API keys, settings
└── requirements.txt
"""