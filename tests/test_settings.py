import json

import pytest

import utils.settings as settings
from utils.settings import DEFAULT_SETTINGS, parse_resolution, validate_settings


@pytest.mark.parametrize("text, expected", [
    ("1280x720", (1280, 720)),
    (" 1280X720 ", (1280, 720)),
])
def test_parse_resolution_valid(text, expected):
    assert parse_resolution(text) == expected


@pytest.mark.parametrize("text", ["", "abc", "1280", "0x720", "-1x5", "1x2x3", "1280x"])
def test_parse_resolution_invalid(text):
    with pytest.raises(ValueError):
        parse_resolution(text)


def test_validate_defaults_ok():
    assert validate_settings(DEFAULT_SETTINGS) == DEFAULT_SETTINGS


def test_validate_ip_accepted():
    cleaned = validate_settings(dict(DEFAULT_SETTINGS, wemos_ip="192.168.1.5"))
    assert cleaned["wemos_ip"] == "192.168.1.5"


@pytest.mark.parametrize("key, value", [
    ("fps", 0), ("fps", 121), ("fps", "30"), ("fps", True), ("fps", 29.5),
    ("video_width", 0), ("video_height", -5), ("video_width", "1920"),
    ("buffer_seconds", 1), ("buffer_seconds", 61),
    ("camera_index", -1), ("camera_index", "0"), ("camera_index", True),
    ("udp_port", 1023), ("udp_port", 65536),
    ("wemos_ip", "999.1.1.1"), ("wemos_ip", "abc"), ("wemos_ip", "1.2.3"), ("wemos_ip", 5),
    ("replay_pre_seconds", 0), ("replay_pre_seconds", "5"), ("replay_pre_seconds", 2.5),
    ("replay_pre_seconds", DEFAULT_SETTINGS["buffer_seconds"] + 1),
])
def test_validate_rejects_out_of_range(key, value):
    with pytest.raises(ValueError, match=key):
        validate_settings(dict(DEFAULT_SETTINGS, **{key: value}))


@pytest.mark.parametrize("pre", [1, 10])
def test_validate_replay_pre_seconds_up_to_buffer(pre):
    cleaned = validate_settings(dict(DEFAULT_SETTINGS, buffer_seconds=10, replay_pre_seconds=pre))
    assert cleaned["replay_pre_seconds"] == pre


def test_validate_replay_pre_seconds_above_buffer_rejected():
    with pytest.raises(ValueError, match="replay_pre_seconds"):
        validate_settings(dict(DEFAULT_SETTINGS, buffer_seconds=10, replay_pre_seconds=11))


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_FILE", path)
    return path


def test_round_trip(settings_file):
    new = dict(DEFAULT_SETTINGS, fps=60, wemos_ip="10.0.0.2")
    settings.save_settings(new)
    assert settings.load_settings() == new


def test_load_missing_file_gives_defaults(settings_file):
    assert settings.load_settings() == DEFAULT_SETTINGS


def test_load_invalid_value_falls_back(settings_file, capsys):
    settings_file.write_text(json.dumps(dict(DEFAULT_SETTINGS, fps=500, udp_port=6000)))
    loaded = settings.load_settings()
    assert loaded["fps"] == DEFAULT_SETTINGS["fps"]
    assert loaded["udp_port"] == 6000
    assert "fps" in capsys.readouterr().out


def test_load_replay_pre_seconds_above_buffer_falls_back(settings_file, capsys):
    settings_file.write_text(json.dumps(dict(DEFAULT_SETTINGS, buffer_seconds=3, replay_pre_seconds=10)))
    loaded = settings.load_settings()
    assert loaded["buffer_seconds"] == 3
    assert loaded["replay_pre_seconds"] == 3
    assert "replay_pre_seconds" in capsys.readouterr().out


def test_settings_file_is_project_relative():
    assert settings.SETTINGS_FILE.is_absolute()
    assert settings.SETTINGS_FILE.name == "settings.json"
    assert (settings.SETTINGS_FILE.parent / "src").is_dir()
