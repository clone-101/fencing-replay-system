import tkinter as tk

from utils.replay import SPEEDS

def bind_shortcuts(main_window):
    main_window.root.protocol("WM_DELETE_WINDOW", main_window.on_close)

    if main_window.is_mac:
        main_window.root.createcommand('tk::mac::ShowPreferences', main_window.open_settings)
    else:
        main_window.root.bind('<Control-comma>', lambda e: main_window.open_settings())

    for key in ('<Control-r>', '<r>', '<R>'):
        main_window.root.bind(key, lambda e: main_window.replay_video())

    # replay playback; the controller ignores these while live
    main_window.root.bind('<space>', lambda e: main_window.toggle_pause())
    main_window.root.bind('<Left>', lambda e: main_window.step_frame(-1))
    main_window.root.bind('<Right>', lambda e: main_window.step_frame(1))
    for key, speed in zip('123', SPEEDS):
        main_window.root.bind(f'<Key-{key}>', lambda e, s=speed: main_window.set_replay_speed(s))
    main_window.root.bind('<Home>', lambda e: main_window.restart_replay())
    main_window.root.bind('<Escape>', lambda e: main_window.exit_replay())
