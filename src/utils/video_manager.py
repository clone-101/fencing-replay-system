import cv2
import numpy as np
import threading
import time

from utils.frame_buffer import FrameBuffer

MAX_BUFFER_BYTES = 1024 ** 3  # per camera
JPEG_QUALITY = 90


def decode(jpeg_bytes):
	"""Decode JPEG bytes from the FrameBuffer back into a BGR frame."""
	return cv2.imdecode(np.frombuffer(jpeg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)


class VideoManager(threading.Thread):
	def __init__(self, camera_index=0, fps=30, buffer_seconds=20, frame_width=1920, frame_height=1080):
		super().__init__()
		self.running = True
		self.camera_index = camera_index
		self.buffer_seconds = buffer_seconds
		self.buffer = FrameBuffer(max_seconds=buffer_seconds, max_bytes=MAX_BUFFER_BYTES)
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
				now = time.monotonic()
				ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
				if ok:
					self.buffer.append(now, jpeg.tobytes())
				with self._latest_lock:
					self._latest = (now, frame)
			time.sleep(1 / self.fps)

	def latest(self):
		"""Return (timestamp, frame) for the most recent frame, or None if none captured yet."""
		with self._latest_lock:
			return self._latest
