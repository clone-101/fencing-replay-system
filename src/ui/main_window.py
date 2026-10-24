from tkinter import ttk, Toplevel, Menu
import tkinter as tk
import platform
import threading
import time
from datetime import datetime
from pathlib import Path
from ui.settings_window import SettingsWindow
from ui.video_view import VideoView
from utils.video_manager import VideoManager, decode
from utils.replay import ReplayController, REPLAY
from utils.udp import UDPListener
import utils.controls as controls
import utils.settings as settings
from utils import export
# from src.utils.settings import load_settings, save_settings

RECORDINGS_DIR = Path(__file__).resolve().parents[2] / "recordings"
CAPTURE_KEYS = ("fps", "video_width", "video_height", "camera_index", "buffer_seconds")

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Fencing Replay System")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")
        self.video = None
        self._last_frame_ts = None
        self._tick_id = None
        self._wait_id = None
        self._stopping = None
        self.replay = ReplayController()
        self._replay_frames = []
        self._replay_shown = None  # index of the replay frame currently on screen
        self.is_mac = platform.system() == "Darwin"

        # load settings
        self.settings = settings.load_settings()
        
        self.upd_listener = UDPListener(port=self.settings["udp_port"], callback=self.handle_udp_message, sender_ip=self.settings["wemos_ip"])
        self.upd_listener.start()

        self.create_widgets()
        self.create_menu()

        # main window event bindings
        controls.bind_shortcuts(self)
        
        
    def _start_capture(self):
        self.view.show_message("Waiting for camera...")
        self._last_frame_ts = None
        video = VideoManager(camera_index=self.settings["camera_index"], fps=self.settings["fps"], buffer_seconds=self.settings["buffer_seconds"], frame_width=self.settings["video_width"], frame_height=self.settings["video_height"])
        video.start()
        self.video = video

    def create_widgets(self):
        label = ttk.Label(master=self.root, text="Welcome to the Fencing Replay System!", font=("Arial", 16))
        label.pack()
        self.status_label = ttk.Label(master=self.root, text="LIVE", font=("Arial", 14))
        self.status_label.pack()

        # pack the buttons before the view so the expanding canvas can't push them off-screen
        frame = ttk.Frame(master=self.root)
        # takefocus off so Space toggles replay pause instead of pressing the button
        self.save_button = ttk.Button(master=frame, text="Save Video", command=self.save_clip, takefocus=False)
        self.save_button.pack()
        frame.pack(side="bottom", pady=10)

        self.view = VideoView(self.root)

        self._start_capture()
        self._tick()

    def _tick(self):
        # runs on the Tk thread; capture keeps filling the buffer in both modes
        if self.replay.state == REPLAY:
            self._tick_replay()
        else:
            self._tick_live()
        self._tick_id = self.root.after(33, self._tick)

    def _tick_live(self):
        # pulls the newest frame from the capture thread
        latest = self.video.latest() if self.video else None
        if latest is not None and latest[0] != self._last_frame_ts:
            self._last_frame_ts, frame = latest
            self.view.show(frame)

    def _tick_replay(self):
        index, (_, data) = self.replay.current(time.monotonic())
        if index != self._replay_shown:
            frame = decode(data)
            if frame is not None:
                self.view.show(frame)
            self._replay_shown = index
        icon = "⏸" if self.replay.paused else "▶"
        self.status_label.config(
            text=f"REPLAY {self.replay.speed}x {icon} {index + 1}/{len(self._replay_frames)}"
        )

    def save_clip(self):
        if self.replay.state == REPLAY:
            frames = list(self._replay_frames)
        elif self.video:
            frames = self.video.buffer.snapshot()
        else:
            return
        if not frames:
            print("No frames to save.")
            return
        RECORDINGS_DIR.mkdir(exist_ok=True)
        path = RECORDINGS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        duration = frames[-1][0] - frames[0][0]
        self.save_button.state(["disabled"])
        worker = threading.Thread(target=export.save_clip, args=(frames, path), daemon=True)
        worker.start()
        self._poll_save(worker, duration, path)

    def _poll_save(self, worker, duration, path):
        # runs on the Tk thread; the worker never touches Tk
        if worker.is_alive():
            self.root.after(100, self._poll_save, worker, duration, path)
            return
        self.save_button.state(["!disabled"])
        print(f"Saved {duration:.1f}s to {path}")

    def create_menu(self):
        menubar = Menu(self.root)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Settings", command=self.open_settings, accelerator="Ctrl+,")
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def open_settings(self):
         SettingsWindow(self.root, self.settings, self.on_settings_saved)	

    def on_settings_saved(self, new_settings):
        capture_changed = any(k in new_settings and new_settings[k] != self.settings.get(k) for k in CAPTURE_KEYS)
        self.settings.update(new_settings)
        settings.save_settings(self.settings)
        # FIXME: remove print in production
        print(f"Settings updated: {self.settings}")
        # a restart already in progress picks up the latest self.settings
        if capture_changed and self._stopping is None:
            self._stopping = self.video
            if self._stopping is not None:
                self._stopping.stop()
            self.view.show_message("Restarting camera...")
            self._wait_for_video_thread()

    def _wait_for_video_thread(self):
        old = self._stopping
        if old is not None and old.is_alive():
            self._wait_id = self.root.after(50, self._wait_for_video_thread)
            return
        self._wait_id = None
        if old is not None and old.vid is not None:
            old.vid.release()
        self._stopping = None
        self._start_capture()

    def replay_video(self):
        """Freeze the view and replay the last replay_pre_seconds; capture keeps running."""
        if not self.video:
            return
        now = time.monotonic()
        frames = self.video.buffer.snapshot(now - self.settings["replay_pre_seconds"], now)
        if not frames:
            print("No frames to replay.")
            return
        self._replay_frames = frames
        self._replay_shown = None
        self.replay.enter(frames, now)

    def toggle_pause(self):
        self.replay.toggle_pause(time.monotonic())

    def step_frame(self, n):
        self.replay.step(n)

    def set_replay_speed(self, speed):
        self.replay.set_speed(speed, time.monotonic())

    def restart_replay(self):
        self.replay.restart(time.monotonic())

    def exit_replay(self):
        if self.replay.state != REPLAY:
            return
        self.replay.exit()
        self._replay_frames = []
        self._replay_shown = None
        # force the next tick to redraw the newest live frame even if it is unchanged
        self._last_frame_ts = None
        self.status_label.config(text="LIVE")
        self._tick_live()

    def handle_udp_message(self, msg):
        # FIXME: Implement UDP message handling
        print(f"Received UDP message: {msg}")

    def on_close(self):
        if self._tick_id is not None:
            self.root.after_cancel(self._tick_id)
        if self._wait_id is not None:
            self.root.after_cancel(self._wait_id)
        # stop whatever instance exists, including one still shutting down mid-restart
        for video in {self._stopping, self.video} - {None}:
            video.stop()
            if video.is_alive():
                video.join(timeout=2)
        self.upd_listener.stop()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()