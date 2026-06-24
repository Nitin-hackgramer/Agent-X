import sys

from graph import graph

# Windows console defaults to cp1252; tweets/titles carry unicode → force UTF-8 so prints don't crash
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def app():
    initial_state = {
        "research_data": [],
        "tweet_drafts": [],
        "selected_draft": None,
        "approval_status": "pending",
        "rejection_feedback": None,
        "retry_count": 0,
    }
    final_state = graph.compile().invoke(initial_state)
    print(f"\nDone. status={final_state['approval_status']}")


if __name__ == "__main__":
    app()

