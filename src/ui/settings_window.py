from tkinter import Toplevel, ttk

class SettingsWindow:
    def __init__(self, root):
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
        frame_rate = self.frame_rate_entry.get()
        resolution = self.resolution_entry.get()
        # Here you would typically save the settings to a file or apply them
        print(f"Settings saved: Frame Rate = {frame_rate}, Resolution = {resolution}")
        self.window.destroy()