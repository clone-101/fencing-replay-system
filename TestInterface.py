import tkinter as tk
import ttkbootstrap as ttk
from tkinter import Menu, Toplevel
import platform

window = ttk.Window(themename="darkly")
window.title("Fencing Replay System")
# window size (widthxheight)
window.geometry("800x600")

# Create a label
label = ttk.Label(master=window, text="Welcome to the Fencing Replay System!", font=("Arial", 16))
label.pack()

# create a frame
frame = ttk.Frame(master=window)

# create a button
button = ttk.Button(master=frame, text="Replay")
button.pack()
frame.pack(pady=10)

def open_settings():
    if hasattr(open_settings, 'window') and open_settings.window.winfo_exists():
        open_settings.window.lift()
    else:
        open_settings.window = Toplevel(window)
        open_settings.window.title("Settings")
        open_settings.window.geometry("400x300")
        settings_label = ttk.Label(open_settings.window, text="Settings will go here", font=("Arial", 14))
        settings_label.pack()
        
is_mac = platform.system() == "Darwin"

if is_mac:
    # macOS: Add Preferences to app menu
    window.createcommand('tk::mac::ShowPreferences', open_settings)
else:
    # Windows/Linux: Create a menubar with Preferences item
    menubar = Menu(window)
    file_menu = Menu(menubar, tearoff=0)
    file_menu.add_command(label="Settings", command=open_settings, accelerator="Ctrl+,")
    menubar.add_cascade(label="File", menu=file_menu)
    window.config(menu=menubar)
window.bind('<Control-comma>', lambda e: open_settings())

window.mainloop()