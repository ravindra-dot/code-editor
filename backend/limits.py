"""Small single-process traffic guard for a single-host deployment."""

import threading
import time
from collections import defaultdict, deque


WINDOW_SECONDS = 60
_requests = defaultdict(deque)
_lock = threading.Lock()


def allow(client, category, maximum):
    now = time.monotonic()
    key = (client, category)
    with _lock:
        # Keep the table bounded even when clients send only one request each.
        if len(_requests) > 10000:
            for old_key, timestamps in list(_requests.items()):
                if not timestamps or timestamps[-1] <= now - WINDOW_SECONDS:
                    del _requests[old_key]
        if key not in _requests and len(_requests) >= 10000:
            return False
        timestamps = _requests[key]
        while timestamps and timestamps[0] <= now - WINDOW_SECONDS:
            timestamps.popleft()
        if len(timestamps) >= maximum:
            return False
        timestamps.append(now)
        return True
