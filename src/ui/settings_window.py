from tkinter import Toplevel, ttk

class SettingsWindow:
    def __init__(self, root, settings, on_save):
        self.settings = settings
        self.on_save = on_save
        self.window = Toplevel(root)
        self.window.title("Settings")
        self.window.geometry("400x300")
        self.create_widgets()

    def create_widgets(self):
        label = ttk.Label(self.window, text="Settings", font=("Arial", 14))
        label.pack(pady=10)

        # Example setting: Frame rate
        frame_rate_label = ttk.Label(self.window, text="Frame Rate (FPS):")
        frame_rate_label.pack(pady=5)

        self.frame_rate_entry = ttk.Entry(self.window)
        self.frame_rate_entry.pack(pady=5)

        # Example setting: Video resolution
        resolution_label = ttk.Label(self.window, text="Video Resolution:")
        resolution_label.pack(pady=5)

        self.resolution_entry = ttk.Entry(self.window)
        self.resolution_entry.pack(pady=5)

        # Save button
        save_button = ttk.Button(self.window, text="Save", command=self.save_settings)
        save_button.pack(pady=20)

    def save_settings(self):
        frame_rate = int(self.frame_rate_entry.get())
        resolution = self.resolution_entry.get().lower().split('x')
        if len(resolution) == 2 and resolution[0].isdigit() and resolution[1].isdigit():
            width, height = int(resolution[0]), int(resolution[1])
        else:
            width, height = 1920, 1080 # fallback value
        
        new_settings = {
            "fps": frame_rate,
            "video_width": width,
            "video_height": height,
        }
        self.on_save(new_settings)
        self.window.destroy()