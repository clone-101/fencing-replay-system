import tkinter as tk
from PIL import Image, ImageTk
import cv2


class VideoView:
    """Displays BGR frames on a Tk canvas. Must only be used from the Tk thread."""

    def __init__(self, master, background="black"):
        self.canvas = tk.Canvas(master, background=background, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._width = 1
        self._height = 1
        self._photo = None
        self._image_id = self.canvas.create_image(0, 0, anchor="center")
        self._text_id = self.canvas.create_text(0, 0, anchor="center", fill="white", font=("Arial", 16), state="hidden")
        self.canvas.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        self._width = event.width
        self._height = event.height
        cx, cy = event.width // 2, event.height // 2
        self.canvas.coords(self._image_id, cx, cy)
        self.canvas.coords(self._text_id, cx, cy)

    def show(self, frame_bgr):
        if self._width <= 1 or self._height <= 1:
            return
        h, w = frame_bgr.shape[:2]
        scale = min(self._width / w, self._height / h)
        size = (max(1, int(w * scale)), max(1, int(h * scale)))
        resized = cv2.resize(frame_bgr, size, interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        self._photo = ImageTk.PhotoImage(image=Image.fromarray(rgb))
        self.canvas.itemconfig(self._image_id, image=self._photo, state="normal")
        self.canvas.itemconfig(self._text_id, state="hidden")

    def show_message(self, text):
        self.canvas.itemconfig(self._image_id, state="hidden")
        self.canvas.itemconfig(self._text_id, text=text, state="normal")
