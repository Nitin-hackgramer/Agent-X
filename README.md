# Tweet Generator

Researches the latest tech/AI from live sources → drafts a tweet with an LLM → sends it to you on Telegram to approve, edit, or reject. Approved tweets are saved to `approved_tweets.md` for you to copy and post manually. **No auto-posting to X** (X gates writes behind paid tiers).

## Flow

```
research → generate → approval ──approved──▶ save to approved_tweets.md
              ▲___________|   (rejected: re-research from your feedback, up to 3x)
```

## Sources

Tech/AI-focused, all free, no scraping:

- **BBC Technology** RSS — tech news
- **GitHub** search API — repos going viral (most stars created in last 7 days)
- **Hugging Face** API — trending new models
- **Google News** search — latest AI ("new model / LLM / AI engineering", last 7 days)
- **Hacker News** — top stories (coding/tech insights)
- **ZenQuotes** — a quote for variety

**On rejection feedback**: re-searches Google News + HN Algolia keyed on your feedback text — so rejecting with "make it about X" pulls real articles about X and regenerates.

## Approve / edit / reject

When a draft arrives (Telegram, or terminal if no bot token), reply:

| Reply | Action |
|-------|--------|
| `y` | approve → saved to `approved_tweets.md` |
| `n <reason>` | reject → re-research on `<reason>`, new draft |
| `e <old>\|<new>` | edit: replace `<old>` with `<new>`, re-confirm |
| `e <full new text>` | replace the whole tweet, re-confirm |

On Telegram the draft is sent as a tap-to-copy code block.

## Setup

```bash
uv sync                 # or: pip install -r requirements.txt
# fill in .env (keys below)
uv run python main.py
```

`.env` keys (all optional — missing ones fall back gracefully):

| Key | Used for | Without it |
|-----|----------|-----------|
| `GROQ_API_KEY` | LLM tweet generation | templated draft (`title — url`) |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | phone approval/edit | terminal prompt |

## Test individual nodes

```bash
uv run python nodes/research.py    # prints default + feedback-targeted results
uv run python nodes/generate.py
uv run python nodes/approval.py    # terminal edit+approve self-check
```

## Scheduler

`scheduler_setup.py` registers Windows Task Scheduler jobs (`schtasks`) that run `main.py` 5 min before the best X engagement windows (default 9am/12pm/5pm, override with `TWEET_BEST_TIMES=08:00,13:30,19:00`):

```bash
uv run python scheduler_setup.py install   # set up daily jobs
uv run python scheduler_setup.py remove    # tear down
```

## Approval follow-ups

If you don't reply within 2 minutes, the bot nags every 10s on Telegram until you `y`/`n`/`e` — no giving up.

## Ideas not built yet

- **Dedup**: skip items already in `approved_tweets.md` so you don't see repeats.
- **Auto-post to Mastodon** (genuinely free API) if you want hands-off publishing.
