import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "video_width": 1920,
    "video_height": 1080,
    "fps": 30,
    "buffer_seconds": 120,
    "udp_port": 5050,
    "wemos_ip": None
}

def load_settings():
    settings = DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                loaded = json.load(f)
                settings.update({k: loaded.get(k, v) for k, v in DEFAULT_SETTINGS.items()})
        except Exception as e:
            print(f"Error loading settings: {e}")
    return settings

def save_settings(settings):
    to_save = {k: settings.get(k, v) for k, v in DEFAULT_SETTINGS.items()}
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(to_save, f, indent=4)