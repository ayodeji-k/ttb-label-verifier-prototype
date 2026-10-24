"""Rate limiting module"""

import time
from collections import defaultdict


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self, max_requests: int, time_window: int):
        """
        Args:
            max_requests: Maximum requests allowed per time window.
            time_window: Time window in seconds.
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)

    def is_rate_limited(self, client_id: str) -> tuple[bool, int]:
        """
        Check if a client is rate limited.

        Args:
            client_id: Client identifier.

        Returns:
            Tuple of (is_limited, remaining_requests).
        """
        now = time.time()
        self.requests[client_id] = [
            request_time
            for request_time in self.requests[client_id]
            if now - request_time < self.time_window
        ]

        if len(self.requests[client_id]) >= self.max_requests:
            return True, 0

        self.requests[client_id].append(now)
        remaining = self.max_requests - len(self.requests[client_id])
        return False, remaining
