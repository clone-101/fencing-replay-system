from tkinter import ttk, Toplevel, Menu
import tkinter as tk
import platform
import threading
from ui.settings_window import SettingsWindow
from utils.video_manager import VideoManager
# from src.utils.settings import load_settings, save_settings

# constants
DEFAULT_FPS = 30
BUFFER_SECONDS = 120
DEFAULT_FRAME_WIDTH = 1920
DEFAULT_FRAME_HEIGHT = 1080
DEFAULT_PORT = 5050

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Fencing Replay System")
        self.root.geometry("800x600")
        self.video = VideoManager(root=root)

        self.create_widgets()
        self.create_menu()

        self.is_mac = platform.system() == "Darwin"
        if self.is_mac:
            self.root.createcommand('tk::mac::ShowPreferences', self.open_settings)
        else:
            self.root.bind('<Control-comma>', lambda e: self.open_settings())

    def create_widgets(self):
        label = ttk.Label(master=self.root, text="Welcome to the Fencing Replay System!", font=("Arial", 16))
        label.pack()

        canvas = tk.Canvas(self.root, width=self.video.frame_width, height=self.video.frame_height)
        canvas.bind("<Configure>", lambda event: self.video.resize_canvas(event))
        self.video.canvas = canvas
        canvas.pack()


        frame = ttk.Frame(master=self.root)
        replay_button = ttk.Button(master=frame, text="Save Video", command=self.video.save_video)
        replay_button.pack()
        frame.pack(pady=10)

        threading.Thread(target=self.video.update_frame, daemon=True).start()

    def create_menu(self):
        menubar = Menu(self.root)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Settings", command=self.open_settings, accelerator="Ctrl+,")
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def open_settings(self):
         SettingsWindow(self.root)	

    def replay_video(self):
        # Placeholder for replay functionality
        print("Replay functionality not implemented yet.")

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()