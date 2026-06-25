"""Register/remove Windows Task Scheduler jobs that run main.py 5 min before
peak-engagement times on X (so you get the Telegram prompt in time to approve
and post right at the good slot).

Times are the commonly-cited best-engagement windows for X (weekdays):
9am, 12pm (noon), 5pm local time. ponytail: hardcoded, no "research" module —
these are stable industry-standard slots, not something to compute at runtime.
Override via TWEET_BEST_TIMES env var, e.g. "08:00,13:30,19:00".

Usage:
    uv run python scheduler_setup.py install
    uv run python scheduler_setup.py remove
"""
import os
import subprocess
import sys
from datetime import datetime, timedelta

DEFAULT_TIMES = ["09:00", "12:00", "17:00"]
TASK_PREFIX = "TwitterAgent_"


def _best_times():
    raw = os.getenv("TWEET_BEST_TIMES")
    return [t.strip() for t in raw.split(",")] if raw else DEFAULT_TIMES


def _notify_time(hhmm):
    t = datetime.strptime(hhmm, "%H:%M") - timedelta(minutes=5)
    return t.strftime("%H:%M")


def install():
    py = sys.executable
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    for t in _best_times():
        notify_at = _notify_time(t)
        name = TASK_PREFIX + t.replace(":", "")
        subprocess.run([
            "schtasks", "/create", "/f", "/tn", name, "/sc", "DAILY",
            "/st", notify_at, "/tr", f'"{py}" "{script}"',
        ], check=True)
        print(f"Scheduled {name}: runs daily at {notify_at} (5 min before {t})")


def remove():
    for t in _best_times():
        name = TASK_PREFIX + t.replace(":", "")
        subprocess.run(["schtasks", "/delete", "/f", "/tn", name])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "install":
        install()
    elif cmd == "remove":
        remove()
    else:
        print(__doc__)
