import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime
from collections import deque
import cv2
import time
import os


class VideoManager:
	def __init__(self, root=None, canvas=None, camera_index=0, fps=30, buffer_seconds=120, frame_width=1920, frame_height=1080):
		self.running = True
		self.camera_index = camera_index
		self.frame_buffer = deque(maxlen=int(fps * buffer_seconds))
		self.vid = cv2.VideoCapture(camera_index)
		self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
		self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
		self.frame_width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
		self.frame_height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
		self.fps = self.vid.get(cv2.CAP_PROP_FPS)
		self.fps = min(self.fps, fps) if self.fps else fps
		self.canvas = canvas
		self.root = root

	def __del__(self):
		if hasattr(self, 'vid') and self.vid is not None:
			self.vid.release()
	
	def update_frame(self):
		while self.running:
			ret, frame = self.vid.read()
			if ret:
				self.frame_buffer.append(frame.copy())
				self.display_frame(frame)
			time.sleep(1 / self.fps)

	def display_frame(self, frame):
		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		img = Image.fromarray(frame)
		imgtk = ImageTk.PhotoImage(image=img)
		self.root.after(0, self._update_canvas, imgtk)

	def _update_canvas(self, imgtk):
		self.canvas.create_image(0, 0, image=imgtk, anchor=tk.NW)
		self.canvas.image = imgtk

	def save_video(self):
		os.makedirs("recordings", exist_ok=True)
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		filename = f"recordings/{timestamp}.mp4"
		frames = list(self.frame_buffer)
		if not frames:
			print("No frames to save.")
			return
		fourcc = cv2.VideoWriter_fourcc(*'mp4v')
		height, width, _ = frames[0].shape
		out = cv2.VideoWriter(filename, fourcc, self.fps, (width, height))
		for frame in frames:
			out.write(frame)
		out.release()
		print(f"Saved last 10 seconds to {filename}")
	

