import ast
from pathlib import Path

import pytest

import utils.replay
from utils.replay import LIVE, REPLAY, ReplayController

# uneven capture intervals, as from a camera with varying fps
OFFSETS = [0.0, 0.05, 0.2, 0.25, 0.6, 1.0]
T0 = 100.0
FRAMES = [(T0 + off, f'frame{i}') for i, off in enumerate(OFFSETS)]


def entered(now=0.0):
    rc = ReplayController()
    rc.enter(FRAMES, now)
    return rc


def index_at(rc, now):
    return rc.current(now)[0]


def test_starts_live():
    rc = ReplayController()
    assert rc.state == LIVE
    assert rc.current(0.0) is None


def test_enter_starts_at_index_zero_playing_at_1x():
    rc = entered(now=50.0)
    assert rc.state == REPLAY
    assert rc.speed == 1.0
    assert not rc.paused
    assert rc.current(50.0) == (0, FRAMES[0])


def test_enter_with_empty_list_stays_live():
    rc = ReplayController()
    rc.enter([], 0.0)
    assert rc.state == LIVE
    assert rc.current(0.0) is None


@pytest.mark.parametrize('elapsed, expected', [
    (0.0, 0),
    (0.049, 0),
    (0.05, 1),
    (0.19, 1),
    (0.2, 2),
    (0.3, 3),
    (0.59, 3),
    (0.6, 4),
    (0.99, 4),
])
def test_1x_playback_follows_frame_timestamps(elapsed, expected):
    rc = entered(now=10.0)
    assert index_at(rc, 10.0 + elapsed) == expected


def test_half_speed_takes_twice_as_long():
    rc = entered(now=0.0)
    rc.set_speed(0.5, 0.0)
    assert index_at(rc, 0.3) == 1  # clip offset 0.15
    assert index_at(rc, 0.39) == 1  # clip offset 0.195
    assert index_at(rc, 0.4) == 2  # clip offset 0.2
    assert index_at(rc, 1.2) == 4  # clip offset 0.6


def test_speed_change_mid_playback_keeps_position():
    rc = entered(now=0.0)
    assert index_at(rc, 0.2) == 2
    rc.set_speed(0.25, 0.2)
    # 0.2 + (0.4 * 0.25) = 0.3 clip offset
    assert index_at(rc, 0.6) == 3
    assert index_at(rc, 1.79) == 3  # 0.2 + 1.59 * 0.25 = 0.5975
    assert index_at(rc, 1.8) == 4  # 0.6


def test_invalid_speed_rejected():
    rc = entered()
    with pytest.raises(ValueError):
        rc.set_speed(2.0, 0.0)
    assert rc.speed == 1.0


def test_pause_freezes_index():
    rc = entered(now=0.0)
    assert index_at(rc, 0.2) == 2
    rc.toggle_pause(0.2)
    assert rc.paused
    assert index_at(rc, 5.0) == 2
    assert index_at(rc, 100.0) == 2


def test_resume_continues_from_paused_frame():
    rc = entered(now=0.0)
    rc.toggle_pause(0.25)  # paused on index 3 (offset 0.25)
    rc.toggle_pause(10.0)
    assert not rc.paused
    assert index_at(rc, 10.0) == 3
    assert index_at(rc, 10.34) == 3
    assert index_at(rc, 10.35) == 4  # 0.25 + 0.35 = 0.6


def test_step_moves_exactly_one_frame():
    rc = entered(now=0.0)
    assert index_at(rc, 0.2) == 2
    rc.step(+1)
    assert rc.paused
    assert index_at(rc, 0.2) == 3
    rc.step(-1)
    assert index_at(rc, 9.0) == 2
    rc.step(-1)
    assert index_at(rc, 9.0) == 1


def test_step_clamped_at_both_ends():
    rc = entered(now=0.0)
    rc.step(-1)
    assert index_at(rc, 0.0) == 0
    for _ in range(len(FRAMES) + 3):
        rc.step(+1)
    assert index_at(rc, 0.0) == len(FRAMES) - 1
    rc.step(-100)
    assert index_at(rc, 0.0) == 0
    rc.step(+100)
    assert index_at(rc, 0.0) == len(FRAMES) - 1


def test_reaching_end_pauses_on_last_frame():
    rc = entered(now=0.0)
    assert rc.current(1.0) == (5, FRAMES[5])
    assert rc.paused
    assert rc.current(50.0) == (5, FRAMES[5])


def test_overshooting_end_pauses_on_last_frame():
    rc = entered(now=0.0)
    assert rc.current(30.0) == (5, FRAMES[5])
    assert rc.paused


def test_restart_returns_to_index_zero_and_plays():
    rc = entered(now=0.0)
    rc.current(5.0)
    assert rc.paused
    rc.restart(7.0)
    assert not rc.paused
    assert index_at(rc, 7.0) == 0
    assert index_at(rc, 7.2) == 2


def test_restart_keeps_speed():
    rc = entered(now=0.0)
    rc.set_speed(0.5, 0.0)
    rc.restart(1.0)
    assert index_at(rc, 1.39) == 1
    assert index_at(rc, 1.4) == 2


def test_exit_returns_to_live():
    rc = entered(now=0.0)
    rc.exit()
    assert rc.state == LIVE
    assert rc.current(0.0) is None
    assert rc.current(10.0) is None


def test_controls_are_noops_when_live():
    rc = ReplayController()
    rc.toggle_pause(0.0)
    rc.step(1)
    rc.restart(0.0)
    rc.set_speed(0.5, 0.0)
    assert rc.state == LIVE
    assert rc.current(0.0) is None


def test_reenter_resets_speed_and_position():
    rc = entered(now=0.0)
    rc.set_speed(0.25, 0.0)
    rc.step(+3)
    rc.exit()
    rc.enter(FRAMES, 20.0)
    assert rc.speed == 1.0
    assert not rc.paused
    assert index_at(rc, 20.0) == 0


def test_duplicate_timestamps_do_not_trap_playback():
    frames = [(0.0, 'a'), (0.1, 'b'), (0.1, 'c'), (0.2, 'd')]
    rc = ReplayController()
    rc.enter(frames, 0.0)
    rc.step(+1)
    rc.step(-1)
    assert index_at(rc, 0.0) == 0
    rc.step(+1)
    rc.toggle_pause(0.0)
    assert index_at(rc, 0.1) == 3


def test_enter_copies_frames():
    frames = list(FRAMES)
    rc = ReplayController()
    rc.enter(frames, 0.0)
    frames.clear()
    assert rc.current(0.0) == (0, FRAMES[0])


def test_module_has_no_gui_or_cv_imports():
    tree = ast.parse(Path(utils.replay.__file__).read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split('.')[0])
    assert not imported & {'cv2', 'tkinter', 'PIL'}
