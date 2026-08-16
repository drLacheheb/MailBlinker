import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict


class TokenBurstShield:
    """In-memory sliding-window anti-replay and burst throttle per tracking token."""

    def __init__(self, max_requests: int = 5, window_seconds: float = 10.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._last_cleanup = time.monotonic()

    def is_bursting(self, token: str) -> bool:
        """Check if request burst threshold is exceeded. Returns True if bursting."""
        now = time.monotonic()
        with self._lock:
            # Periodic cleanup every 60 seconds
            if now - self._last_cleanup > 60.0:
                self._cleanup(now)
                self._last_cleanup = now

            timestamps = self._history[token]
            # Evict timestamps outside sliding window
            cutoff = now - self.window_seconds
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            if len(timestamps) >= self.max_requests:
                return True

            timestamps.append(now)
            return False

    def _cleanup(self, now: float) -> None:
        cutoff = now - self.window_seconds
        stale_keys = []
        for token, timestamps in self._history.items():
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()
            if not timestamps:
                stale_keys.append(token)
        for k in stale_keys:
            del self._history[k]


token_burst_shield = TokenBurstShield(max_requests=5, window_seconds=10.0)
