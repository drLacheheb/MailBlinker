import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict, Optional


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


class CanarySubnetBlacklist:
    """Dynamic autonomous IP and subnet blacklist for crawlers tripping honeypot canary links."""

    def __init__(self, default_ttl: float = 86400.0):
        self.default_ttl = default_ttl
        self._blacklist: Dict[str, float] = {}
        self._lock = Lock()

    def record_trap_hit(self, ip: str, ttl: Optional[float] = None) -> None:
        """Register an IP and its /24 subnet into the honeypot blacklist."""
        now = time.monotonic()
        expires_at = now + (ttl if ttl is not None else self.default_ttl)
        clean_ip = ip.strip()
        with self._lock:
            self._blacklist[clean_ip] = expires_at
            # If IPv4, blacklist the entire /24 subnet
            if "." in clean_ip and len(clean_ip.split(".")) == 4:
                subnet_prefix = ".".join(clean_ip.split(".")[:3]) + ".0/24"
                self._blacklist[subnet_prefix] = expires_at

    def is_blacklisted(self, ip: Optional[str]) -> bool:
        """Check whether an IP or its /24 subnet is actively blacklisted."""
        if not ip:
            return False
        clean_ip = ip.strip()
        now = time.monotonic()
        with self._lock:
            # Check direct IP
            if clean_ip in self._blacklist:
                if now < self._blacklist[clean_ip]:
                    return True
                else:
                    del self._blacklist[clean_ip]

            # Check /24 subnet
            if "." in clean_ip and len(clean_ip.split(".")) == 4:
                subnet_prefix = ".".join(clean_ip.split(".")[:3]) + ".0/24"
                if subnet_prefix in self._blacklist:
                    if now < self._blacklist[subnet_prefix]:
                        return True
                    else:
                        del self._blacklist[subnet_prefix]

        return False


canary_blacklist = CanarySubnetBlacklist()
