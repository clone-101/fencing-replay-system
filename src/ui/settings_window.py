from tkinter import Toplevel, messagebox, ttk

import utils.settings as settings_module


class SettingsWindow:
    def __init__(self, root, settings, on_save):
        self.settings = settings
        self.on_save = on_save
        self.window = Toplevel(root)
        self.window.title("Settings")
        self.window.transient(root)
        self.create_widgets()
        self.window.update_idletasks()
        self.window.geometry(f"{self.window.winfo_reqwidth()}x{self.window.winfo_reqheight()}")
        self.window.grab_set()

    def create_widgets(self):
        form = ttk.Frame(self.window, padding=15)
        form.pack()

        current = self.settings
        resolution = f"{current['video_width']}x{current['video_height']}"
        rows = [
            ("fps_entry", "Frame Rate (FPS):", current["fps"], ""),
            ("resolution_entry", "Video Resolution (WxH):", resolution, ""),
            ("buffer_entry", "Buffer (seconds):", current["buffer_seconds"], ""),
            ("replay_pre_entry", "Replay length (seconds):", current["replay_pre_seconds"], "1 to buffer length"),
            ("camera_entry", "Camera index:", current["camera_index"], ""),
            ("udp_port_entry", "UDP port:", current["udp_port"], "Takes effect after restart"),
        ]
        for row, (attr, text, value, note) in enumerate(rows):
            ttk.Label(form, text=text).grid(row=row, column=0, sticky="w", pady=5, padx=(0, 10))
            entry = ttk.Entry(form)
            entry.insert(0, str(value))
            entry.grid(row=row, column=1, pady=5)
            setattr(self, attr, entry)
            if note:
                ttk.Label(form, text=note).grid(row=row, column=2, sticky="w", padx=(10, 0))

        buttons = ttk.Frame(form)
        buttons.grid(row=len(rows), column=0, columnspan=3, pady=(15, 0))
        ttk.Button(buttons, text="Save", command=self.save_settings).pack(side="left", padx=5)
        ttk.Button(buttons, text="Cancel", command=self.window.destroy).pack(side="left", padx=5)

    @staticmethod
    def _parse_int(label, text):
        try:
            return int(text.strip())
        except ValueError:
            raise ValueError(f"{label} must be a whole number, got {text!r}") from None

    def save_settings(self):
        try:
            width, height = settings_module.parse_resolution(self.resolution_entry.get())
            candidate = dict(self.settings)
            candidate.update(
                fps=self._parse_int("fps", self.fps_entry.get()),
                video_width=width,
                video_height=height,
                buffer_seconds=self._parse_int("buffer_seconds", self.buffer_entry.get()),
                replay_pre_seconds=self._parse_int("replay_pre_seconds", self.replay_pre_entry.get()),
                camera_index=self._parse_int("camera_index", self.camera_entry.get()),
                udp_port=self._parse_int("udp_port", self.udp_port_entry.get()),
            )
            new_settings = settings_module.validate_settings(candidate)
        except ValueError as e:
            messagebox.showerror("Invalid settings", str(e), parent=self.window)
            return
        self.window.destroy()
        self.on_save(new_settings)
