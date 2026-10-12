import cv2

from utils.video_manager import decode

DEFAULT_FPS = 30.0


def effective_fps(timestamps, fallback=DEFAULT_FPS):
	"""Frame rate (n-1)/(t_last - t_first), or fallback if it cannot be measured."""
	if len(timestamps) < 2:
		return fallback
	duration = timestamps[-1] - timestamps[0]
	if duration <= 0:
		return fallback
	return (len(timestamps) - 1) / duration


def save_clip(frames, path):
	"""Write (timestamp, jpeg_bytes) pairs to an MP4 at path, at real-time speed."""
	if not frames:
		return
	fps = effective_fps([t for t, _ in frames])
	first = decode(frames[0][1])
	height, width = first.shape[:2]
	out = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
	try:
		out.write(first)
		for _, data in frames[1:]:
			out.write(decode(data))
	finally:
		out.release()
