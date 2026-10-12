import threading
from collections import deque


class FrameBuffer:
    """Thread-safe ring of (timestamp, data) pairs bounded by time span and byte size.

    Timestamps must be non-decreasing. The newest pair is always kept, even if it
    alone exceeds max_bytes, so latest() never loses the current frame.
    """

    def __init__(self, max_seconds, max_bytes):
        if max_seconds <= 0:
            raise ValueError("max_seconds must be positive")
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.max_seconds = max_seconds
        self.max_bytes = max_bytes
        self._items = deque()  # (t, data, nbytes)
        self._total_bytes = 0
        self._lock = threading.Lock()

    def append(self, t, data, nbytes=None):
        if nbytes is None:
            nbytes = len(data) if isinstance(data, (bytes, bytearray)) else data.nbytes
        with self._lock:
            if self._items and t < self._items[-1][0]:
                raise ValueError(f"timestamp {t} is older than newest {self._items[-1][0]}")
            self._items.append((t, data, nbytes))
            self._total_bytes += nbytes
            while len(self._items) > 1 and (
                t - self._items[0][0] > self.max_seconds or self._total_bytes > self.max_bytes
            ):
                self._total_bytes -= self._items.popleft()[2]

    def latest(self):
        """Return the newest (t, data) pair, or None if empty."""
        with self._lock:
            if not self._items:
                return None
            t, data, _ = self._items[-1]
            return (t, data)

    def snapshot(self, t0=None, t1=None):
        """Return an independent list of (t, data) pairs with t0 <= t <= t1 (bounds optional)."""
        with self._lock:
            return [
                (t, data) for t, data, _ in self._items
                if (t0 is None or t >= t0) and (t1 is None or t <= t1)
            ]

    def measured_fps(self):
        """Frame rate from stored timestamps, or 0.0 if it cannot be measured."""
        with self._lock:
            if len(self._items) < 2:
                return 0.0
            duration = self._items[-1][0] - self._items[0][0]
            if duration <= 0:
                return 0.0
            return (len(self._items) - 1) / duration

    @property
    def total_bytes(self):
        with self._lock:
            return self._total_bytes

    def __len__(self):
        with self._lock:
            return len(self._items)
