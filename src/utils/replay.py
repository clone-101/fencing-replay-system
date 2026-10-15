from bisect import bisect_right

LIVE = 'LIVE'
REPLAY = 'REPLAY'
SPEEDS = (0.25, 0.5, 1.0)

# tolerance for float drift when comparing clip offsets to frame offsets
_EPS = 1e-9


class ReplayController:
    """Live/replay state and playback position over a clip of (t, data) frames.

    Playback advances by elapsed wall time x speed against the frames' own
    timestamps, so uneven capture rates replay at true speed. Every time-dependent
    method takes `now` (seconds, monotonic) so the controller is deterministic.
    """

    def __init__(self):
        self.state = LIVE
        self.speed = 1.0
        self.paused = False
        self._frames = []
        self._offsets = []  # frame timestamp minus first frame timestamp
        self._index = 0
        self._anchor_wall = 0.0  # wall time at which _anchor_offset applied
        self._anchor_offset = 0.0  # clip offset at _anchor_wall

    def enter(self, frames, now):
        """Start replaying frames from index 0 at 1.0x. An empty clip stays LIVE."""
        if not frames:
            return
        frames = list(frames)
        t0 = frames[0][0]
        self._frames = frames
        self._offsets = [t - t0 for t, _ in frames]
        self.state = REPLAY
        self.speed = 1.0
        self._seek(0, now)
        self.paused = False

    def exit(self):
        self.state = LIVE
        self.paused = False
        self._frames = []
        self._offsets = []
        self._index = 0

    def toggle_pause(self, now):
        if self.state != REPLAY:
            return
        if self.paused:
            self._seek(self._index, now)
            self.paused = False
        else:
            self._advance(now)
            self.paused = True

    def step(self, n):
        """Pause and move n frames, clamped to the clip."""
        if self.state != REPLAY:
            return
        # step has no clock, so it steps from the last frame returned by current()
        self.paused = True
        self._index = max(0, min(len(self._frames) - 1, self._index + n))

    def set_speed(self, s, now):
        if s not in SPEEDS:
            raise ValueError(f"speed must be one of {SPEEDS}, got {s}")
        if self.state == REPLAY and not self.paused:
            self._advance(now)
            self._anchor_offset = self._clip_offset(now)
            self._anchor_wall = now
        self.speed = s

    def restart(self, now):
        """Return to index 0 and play."""
        if self.state != REPLAY:
            return
        self._seek(0, now)
        self.paused = False

    def current(self, now):
        """Return (index, (t, data)) for the frame to show at now, or None when LIVE."""
        if self.state != REPLAY:
            return None
        if not self.paused:
            self._advance(now)
        return self._index, self._frames[self._index]

    def _seek(self, index, now):
        self._index = index
        self._anchor_wall = now
        self._anchor_offset = self._offsets[index]

    def _clip_offset(self, now):
        return self._anchor_offset + (now - self._anchor_wall) * self.speed

    def _advance(self, now):
        # never move backwards while playing (frames may share a timestamp)
        offset = self._clip_offset(now)
        index = bisect_right(self._offsets, offset + _EPS) - 1
        self._index = max(self._index, index)
        if self._index >= len(self._frames) - 1:
            self._index = len(self._frames) - 1
            self.paused = True
