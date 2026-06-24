import html
import os
import time
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv()

POLL_TIMEOUT_SECONDS = 120
POLL_INTERVAL_SECONDS = 3
SAVE_PATH = "approved_tweets.md"

HELP = "Reply: y approve · n <reason> reject · e <old>|<new> edit (or e <full new text>)"


def _apply_edit(draft, arg):
    arg = arg.strip()
    # ponytail: "old|new" = substring replace; otherwise full replacement. '|' in a full edit is rare.
    if "|" in arg:
        old, new = arg.split("|", 1)
        return draft.replace(old.strip(), new.strip(), 1)
    return arg or draft


def _save_tweet(tweet, path=SAVE_PATH):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"- [{datetime.now():%Y-%m-%d %H:%M}] {tweet}\n")
    print(f"Saved approved tweet to {path}")


def _latest_update_id(base):
    # ponytail: drain stale updates so an old reply isn't replayed as the answer to a new prompt
    resp = httpx.get(f"{base}/getUpdates", params={"timeout": 0}).json()
    results = resp.get("result", [])
    return results[-1]["update_id"] + 1 if results else None


def _send(base, chat_id, draft, edited=False):
    label = "Edited draft (tap to copy):" if edited else "Tweet draft (tap to copy):"
    body = f"{label}\n<code>{html.escape(draft)}</code>\n\n{html.escape(HELP)}"
    httpx.post(f"{base}/sendMessage", json={"chat_id": chat_id, "text": body, "parse_mode": "HTML"})


def _parse_cmd(text):
    parts = text.strip().split(None, 1)
    cmd = parts[0].lower() if parts else ""
    arg = parts[1] if len(parts) > 1 else ""
    return cmd, arg


def _telegram_approval(draft, token, chat_id):
    base = f"https://api.telegram.org/bot{token}"
    last_update_id = _latest_update_id(base)
    _send(base, chat_id, draft)

    deadline = time.time() + POLL_TIMEOUT_SECONDS
    while time.time() < deadline:
        resp = httpx.get(
            f"{base}/getUpdates",
            params={"offset": last_update_id, "timeout": POLL_INTERVAL_SECONDS},
            timeout=POLL_INTERVAL_SECONDS + 10,
        ).json()
        for update in resp.get("result", []):
            last_update_id = update["update_id"] + 1
            cmd, arg = _parse_cmd(update.get("message", {}).get("text", ""))
            if cmd == "y":
                return "approved", None, draft
            if cmd == "n":
                return "rejected", arg or "no reason given", draft
            if cmd == "e":
                draft = _apply_edit(draft, arg)
                _send(base, chat_id, draft, edited=True)
                deadline = time.time() + POLL_TIMEOUT_SECONDS  # reset timer after an edit
    return "rejected", "approval timed out", draft


def _terminal_approval(draft):
    while True:
        print(f"\nTweet draft:\n{draft}\n{HELP}")
        cmd, arg = _parse_cmd(input("> "))
        if cmd == "y":
            return "approved", None, draft
        if cmd == "n":
            return "rejected", arg or "no reason given", draft
        if cmd == "e":
            draft = _apply_edit(draft, arg)
        else:
            print("Unknown command.")


def approval_node(state):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if token and chat_id:
        status, feedback, draft = _telegram_approval(state["selected_draft"], token, chat_id)
    else:
        status, feedback, draft = _terminal_approval(state["selected_draft"])

    state["selected_draft"] = draft  # may have been edited
    state["approval_status"] = status
    state["rejection_feedback"] = feedback
    if status == "approved":
        _save_tweet(draft)
    elif status == "rejected":
        state["retry_count"] = state.get("retry_count", 0) + 1
    return state


if __name__ == "__main__":
    import builtins

    os.environ.pop("TELEGRAM_BOT_TOKEN", None)  # force terminal path for the check
    os.environ.pop("TELEGRAM_CHAT_ID", None)
    answers = iter(["e hello|hey", "y"])  # edit then approve
    builtins.input = lambda _: next(answers)
    result = approval_node({"selected_draft": "hello world"})
    assert result["approval_status"] == "approved"
    assert result["selected_draft"] == "hey world", result["selected_draft"]
    print("approval edit+approve smoke test passed")
