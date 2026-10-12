import ast
import threading
import time
from pathlib import Path

import pytest

import utils.frame_buffer
from utils.frame_buffer import FrameBuffer


class FakeArray:
    def __init__(self, nbytes):
        self.nbytes = nbytes


def test_empty_buffer():
    buf = FrameBuffer(max_seconds=10, max_bytes=1000)
    assert buf.latest() is None
    assert buf.snapshot() == []
    assert len(buf) == 0
    assert buf.measured_fps() == 0.0


def test_latest_returns_newest_pair():
    buf = FrameBuffer(max_seconds=10, max_bytes=1000)
    buf.append(1.0, b'a')
    buf.append(2.0, b'b')
    assert buf.latest() == (2.0, b'b')


def test_eviction_by_time_span():
    buf = FrameBuffer(max_seconds=2, max_bytes=10**9)
    for i in range(6):
        buf.append(float(i), b'x')
    # newest is 5.0, so pairs with 5.0 - t > 2 (t < 3.0) are evicted
    assert [t for t, _ in buf.snapshot()] == [3.0, 4.0, 5.0]


def test_eviction_by_byte_budget():
    buf = FrameBuffer(max_seconds=1000, max_bytes=25)
    for i in range(5):
        buf.append(float(i), b'0123456789')
    assert [t for t, _ in buf.snapshot()] == [3.0, 4.0]
    assert buf.total_bytes == 20


def test_nbytes_defaults():
    buf = FrameBuffer(max_seconds=1000, max_bytes=10**9)
    buf.append(0.0, b'abc')
    buf.append(1.0, bytearray(5))
    buf.append(2.0, FakeArray(100))
    buf.append(3.0, object(), nbytes=7)
    assert buf.total_bytes == 3 + 5 + 100 + 7


def test_oversized_frame_is_kept_as_latest():
    buf = FrameBuffer(max_seconds=1000, max_bytes=10)
    buf.append(0.0, b'abc')
    buf.append(1.0, b'x' * 50)
    assert len(buf) == 1
    assert buf.latest() == (1.0, b'x' * 50)


def test_out_of_order_timestamp_rejected():
    buf = FrameBuffer(max_seconds=10, max_bytes=1000)
    buf.append(2.0, b'a')
    with pytest.raises(ValueError):
        buf.append(1.0, b'b')
    assert len(buf) == 1


def test_snapshot_bounds_inclusive_and_open():
    buf = FrameBuffer(max_seconds=100, max_bytes=10**9)
    for i in range(10):
        buf.append(float(i), i, nbytes=1)
    assert [t for t, _ in buf.snapshot(3.0, 6.0)] == [3.0, 4.0, 5.0, 6.0]
    assert [t for t, _ in buf.snapshot(t0=7.0)] == [7.0, 8.0, 9.0]
    assert [t for t, _ in buf.snapshot(t1=2.0)] == [0.0, 1.0, 2.0]
    assert len(buf.snapshot()) == 10
    assert buf.snapshot(20.0, 30.0) == []


def test_snapshot_is_independent_of_later_mutation():
    buf = FrameBuffer(max_seconds=3, max_bytes=10**9)
    for i in range(4):
        buf.append(float(i), i, nbytes=1)
    snap = buf.snapshot()
    expected = list(snap)
    for i in range(4, 20):
        buf.append(float(i), i, nbytes=1)
    assert snap == expected
    assert [t for t, _ in buf.snapshot()] == [16.0, 17.0, 18.0, 19.0]


def test_measured_fps_30hz():
    buf = FrameBuffer(max_seconds=10, max_bytes=10**9)
    for i in range(150):
        buf.append(100.0 + i / 30.0, b'x')
    assert buf.measured_fps() == pytest.approx(30.0, rel=0.01)


def test_invalid_limits():
    with pytest.raises(ValueError):
        FrameBuffer(max_seconds=0, max_bytes=10)
    with pytest.raises(ValueError):
        FrameBuffer(max_seconds=10, max_bytes=0)


def test_concurrent_append_and_snapshot():
    buf = FrameBuffer(max_seconds=0.05, max_bytes=10**6)
    errors = []
    stop = threading.Event()

    def appender():
        try:
            while not stop.is_set():
                buf.append(time.monotonic(), b'x' * 100)
        except Exception as e:
            errors.append(e)

    def reader():
        try:
            while not stop.is_set():
                snap = buf.snapshot()
                ts = [t for t, _ in snap]
                assert ts == sorted(ts)
                buf.latest()
                buf.measured_fps()
                len(buf)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=appender), threading.Thread(target=reader)]
    for th in threads:
        th.start()
    time.sleep(0.5)
    stop.set()
    for th in threads:
        th.join(timeout=2)
    assert errors == []
    assert len(buf) > 0


def test_module_has_no_gui_or_cv_imports():
    tree = ast.parse(Path(utils.frame_buffer.__file__).read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split('.')[0])
    assert not imported & {'cv2', 'tkinter', 'PIL'}
