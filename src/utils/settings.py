import json
import os

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def get_default_settings():
    return {
        "video_width": 1920,
        "video_height": 1080,
        "fps": 30,
        "buffer_seconds": 120,
        "udp_port": 5050,
        "wemos_ip": ""
    }