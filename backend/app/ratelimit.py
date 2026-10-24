"""Tiny in-memory sliding-window rate limiter (pure Python).
Good for ONE server process. With several workers/servers, use a shared store such as Redis."""
import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_events: int, window_seconds: int):
        self.max_events = max_events
        self.window = window_seconds
        self._events = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, dq, now):
        while dq and now - dq[0] > self.window:
            dq.popleft()

    def seconds_until_allowed(self, key) -> int:
        """0 if the key may proceed, otherwise how many seconds to wait."""
        now = time.monotonic()
        with self._lock:
            dq = self._events[key]
            self._prune(dq, now)
            if len(dq) >= self.max_events:
                return int(self.window - (now - dq[0])) + 1
            return 0

    def hit(self, key):
        now = time.monotonic()
        with self._lock:
            self._events[key].append(now)
            if len(self._events) > 10000:  # keep memory bounded
                for k in [k for k, d in self._events.items() if not d or now - d[-1] > self.window]:
                    del self._events[k]

    def reset(self, key):
        with self._lock:
            self._events.pop(key, None)

    def reset_all(self):
        with self._lock:
            self._events.clear()
