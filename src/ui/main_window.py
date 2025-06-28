from tkinter import ttk, Toplevel, Menu
import tkinter as tk
import platform
import threading
from ui.settings_window import SettingsWindow
from utils.video_manager import VideoManager
from utils.udp import UDPListener
import utils.controls as controls
import utils.settings as settings
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
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")
        self.canvas = None
        self.is_mac = platform.system() == "Darwin"

        # load settings
        self.settings = settings.load_settings()
        
        self.upd_listener = UDPListener(port=self.settings["udp_port"], callback=self.handle_udp_message)
        self.upd_listener.start()

        self.create_widgets()
        self.create_menu()

        # main window event bindings
        controls.bind_shortcuts(self)
        
        
    def initialize_video(self):
        if self.canvas:
            self.canvas.destroy()

        self.video = VideoManager(root=self.root, fps=self.settings["fps"], buffer_seconds=self.settings["buffer_seconds"], frame_width=self.settings["video_width"], frame_height=self.settings["video_height"])
        self.canvas = tk.Canvas(self.root, width=self.video.frame_width, height=self.video.frame_height)
        self.canvas.bind("<Configure>", lambda event: self.video.resize_canvas(event))
        self.video.canvas = self.canvas
        self.canvas.pack()
        self.video.start()

    def create_widgets(self):
        label = ttk.Label(master=self.root, text="Welcome to the Fencing Replay System!", font=("Arial", 16))
        label.pack()

        self.initialize_video()

        frame = ttk.Frame(master=self.root)
        replay_button = ttk.Button(master=frame, text="Save Video", command=self.video.save_video)
        replay_button.pack()
        frame.pack(pady=10)

    def create_menu(self):
        menubar = Menu(self.root)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Settings", command=self.open_settings, accelerator="Ctrl+,")
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def open_settings(self):
         SettingsWindow(self.root, self.settings, self.on_settings_saved)	

    def on_settings_saved(self, new_settings):
        self.settings.update(new_settings)
        settings.save_settings(self.settings)
        self.video.stop()
        self._wait_for_video_thread()
        # FIXME: remove print in production
        print(f"Settings updated: {self.settings}")

    def _wait_for_video_thread(self):
        if self.video and self.video.is_alive():
            self.root.after(50, self._wait_for_video_thread)
        else:
            if hasattr(self.video, 'vid') and self.video.vid is not None:
                self.video.vid.release()
            self.video = None
            self.initialize_video()

    def replay_video(self):
        # FIXME: Implement replay functionality
        print("Replay functionality not implemented yet.")
    
    def handle_udp_message(self, msg):
        # FIXME: Implement UDP message handling
        print(f"Received UDP message: {msg}")

    def on_close(self):
        self.video.stop()
        self.upd_listener.stop()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()