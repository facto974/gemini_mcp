"""Reddit PRAW — scraping subreddits crypto/finance pour sentiment."""
from __future__ import annotations

import re

try:
    import praw
except Exception:  # noqa: BLE001
    praw = None


_BULL = {"buy", "long", "bull", "bullish", "moon", "pump", "rocket", "calls", "rally", "breakout"}
_BEAR = {"sell", "short", "bear", "bearish", "dump", "crash", "puts", "rekt", "rug"}


def _score(text: str) -> int:
    t = re.findall(r"[a-zA-Z]+", text.lower())
    s = sum(1 for w in t if w in _BULL) - sum(1 for w in t if w in _BEAR)
    return s


class RedditClient:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.enabled = bool(client_id and client_secret and praw is not None)
        self._reddit = None
        if self.enabled:
            self._reddit = praw.Reddit(client_id=client_id,
                                       client_secret=client_secret,
                                       user_agent=user_agent,
                                       check_for_async=False)

    def sentiment(self, ticker: str, subs: list[str], limit: int = 50) -> float:
        """Retourne un score normalisé [-1, 1]."""
        if not self.enabled:
            return 0.0
        base = ticker.split("-")[0].upper()
        total = 0
        n = 0
        try:
            for sub in subs:
                for post in self._reddit.subreddit(sub).search(base, sort="new", limit=limit, time_filter="day"):
                    total += _score(f"{post.title} {post.selftext or ''}")
                    n += 1
        except Exception:
            return 0.0
        if n == 0:
            return 0.0
        # Normalisation tanh-like
        avg = total / n
        return max(-1.0, min(1.0, avg / 3.0))
