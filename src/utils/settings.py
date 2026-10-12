import ipaddress
import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parents[2] / "settings.json"

DEFAULT_SETTINGS = {
    "video_width": 1920,
    "video_height": 1080,
    "fps": 30,
    "buffer_seconds": 20,
    "udp_port": 5050,
    "wemos_ip": None
}

# field -> (min, max); max None means unbounded above
INT_RANGES = {
    "video_width": (1, None),
    "video_height": (1, None),
    "fps": (1, 120),
    "buffer_seconds": (2, 60),
    "udp_port": (1024, 65535),
}


def parse_resolution(text):
    """Parse "WIDTHxHEIGHT" (case and surrounding whitespace insensitive)."""
    if not isinstance(text, str):
        raise ValueError(f"Resolution must be text like 1280x720, got {text!r}")
    parts = text.strip().lower().split("x")
    if len(parts) != 2:
        raise ValueError(f"Resolution must look like 1280x720, got {text!r}")
    try:
        width, height = int(parts[0]), int(parts[1])
    except ValueError:
        raise ValueError(f"Resolution must look like 1280x720, got {text!r}") from None
    if width <= 0 or height <= 0:
        raise ValueError(f"Resolution must be positive, got {text!r}")
    return width, height


def _validate_field(key, value):
    if key in INT_RANGES:
        low, high = INT_RANGES[key]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{key} must be an integer, got {value!r}")
        if value < low or (high is not None and value > high):
            bound = f"at least {low}" if high is None else f"between {low} and {high}"
            raise ValueError(f"{key} must be {bound}, got {value}")
        return value
    if key == "wemos_ip":
        if value is None:
            return None
        try:
            if not isinstance(value, str):
                raise ValueError
            ipaddress.IPv4Address(value)
        except ValueError:
            raise ValueError(f"wemos_ip must be null or a dotted IPv4 address, got {value!r}") from None
        return value
    raise ValueError(f"Unknown setting: {key}")


def validate_settings(settings):
    """Return cleaned settings; missing keys take defaults. Raises ValueError on the first bad field."""
    return {k: _validate_field(k, settings.get(k, default)) for k, default in DEFAULT_SETTINGS.items()}


def load_settings():
    settings = DEFAULT_SETTINGS.copy()
    path = Path(SETTINGS_FILE)
    if not path.exists():
        return settings
    try:
        with open(path, 'r') as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            raise ValueError("top-level value must be an object")
    except Exception as e:
        print(f"Error loading settings: {e}")
        return settings
    for key, default in DEFAULT_SETTINGS.items():
        if key not in loaded:
            continue
        try:
            settings[key] = _validate_field(key, loaded[key])
        except ValueError as e:
            print(f"Warning: invalid setting ignored ({e}); using default {default!r}")
    return settings

def save_settings(settings):
    to_save = {k: settings.get(k, v) for k, v in DEFAULT_SETTINGS.items()}
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(to_save, f, indent=4)
