import tkinter as tk

def bind_shortcuts(main_window):
    main_window.root.protocol("WM_DELETE_WINDOW", main_window.on_close)

    if main_window.is_mac:
        main_window.root.createcommand('tk::mac::ShowPreferences', main_window.open_settings)
    else:
        main_window.root.bind('<Control-comma>', lambda e: main_window.open_settings())

    main_window.root.bind('<Control-r>', lambda e: main_window.replay_video())

