import tkinter as tk

def bind_shortcuts(root, open_settings_callback, replay_callback):
    root.bind('<Control-comma>', lambda e: open_settings_callback())
    root.bind('<Control-r>', lambda e: replay_callback())
    # root.bind('<Control-p>', lambda e: pause_video())
    # root.bind('<Control-s>', lambda e: save_last_10_seconds())

