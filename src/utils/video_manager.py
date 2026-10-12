from datetime import datetime
from collections import deque
import cv2
import threading
import time
import os


class VideoManager(threading.Thread):
	def __init__(self, camera_index=0, fps=30, buffer_seconds=120, frame_width=1920, frame_height=1080):
		super().__init__()
		self.running = True
		self.camera_index = camera_index
		self.buffer_seconds = buffer_seconds
		self.frame_buffer = deque(maxlen=int(fps * buffer_seconds))
		self.frame_timestamps = deque(maxlen=int(fps * buffer_seconds))
		self.vid = cv2.VideoCapture(camera_index)
		self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
		self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
		self.frame_width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
		self.frame_height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
		self.fps = self.vid.get(cv2.CAP_PROP_FPS)
		self.fps = min(self.fps, fps) if self.fps else fps
		self.data = None
		self._latest = None
		self._latest_lock = threading.Lock()

	def __del__(self):
		self.running = False
		if hasattr(self, 'vid') and self.vid is not None:
			self.vid.release()

	def run(self):
		self.update_frame()

	def stop(self):
		self.running = False
	
	def update_frame(self):
		while self.running:
			ret, frame = self.vid.read()
			if ret:
				now = time.time()
				self.frame_buffer.append(frame.copy())
				self.frame_timestamps.append(now)
				with self._latest_lock:
					self._latest = (now, frame)
			time.sleep(1 / self.fps)

	def latest(self):
		"""Return (timestamp, frame) for the most recent frame, or None if none captured yet."""
		with self._latest_lock:
			return self._latest

	def save_video(self):
		os.makedirs("recordings", exist_ok=True)
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		filename = f"recordings/{timestamp}.mp4"
		now = time.time()
		frames = [f for f, t in zip(self.frame_buffer, self.frame_timestamps) if now - t <= self.buffer_seconds]
		if not frames:
			print("No frames to save.")
			return
		# Calculate actual FPS
		actual_fps = self.fps
		if hasattr(self, 'frame_timestamps') and len(self.frame_timestamps) > 1:
			duration = self.frame_timestamps[-1] - self.frame_timestamps[0]
			actual_fps = len(self.frame_timestamps) / duration if duration > 0 else self.fps
		fourcc = cv2.VideoWriter_fourcc(*'mp4v')
		height, width, _ = frames[0].shape
		out = cv2.VideoWriter(filename, fourcc, actual_fps, (width, height))
		for frame in frames:
			out.write(frame)
		out.release()
		print(f"Saved last 10 seconds to {filename}")
