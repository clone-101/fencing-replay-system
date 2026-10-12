import pytest

from utils.export import DEFAULT_FPS, effective_fps


def test_30hz_timestamps():
    timestamps = [i / 30 for i in range(61)]
    assert effective_fps(timestamps) == pytest.approx(30.0, abs=0.1)


def test_single_timestamp_falls_back():
    assert effective_fps([5.0]) == DEFAULT_FPS


def test_empty_falls_back():
    assert effective_fps([]) == DEFAULT_FPS


def test_identical_timestamps_fall_back():
    assert effective_fps([1.0, 1.0, 1.0]) == DEFAULT_FPS


def test_custom_fallback():
    assert effective_fps([], fallback=24.0) == 24.0
