from VideoManager import VideoManager
from tkinter import ttk
import tkinter as tk
import threading
import socket
import json

# constants
DEFAULT_FPS = 30
BUFFER_SECONDS = 120
DEFAULT_FRAME_WIDTH = 1920
DEFAULT_FRAME_HEIGHT = 1080
DEFAULT_PORT = 5050

# global variables
running = True

# UDP global variables
port = DEFAULT_PORT
wemos_ip = ''
udp_message = None

# tkinter global variables
root = None
canvas = None

def listen_for_udp():
    global running, port, wemos_ip, udp_message
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soc.bind(('0.0.0.0', port))

    while running:
        try:
            data, _ = soc.recvfrom(1024)
            udp_message = parse_message(data.decode('utf-8'))
            video.save_video()
        except socket.error as e:
            if not running:
                break
            print(f"Socket error: {e}")
    
    soc.close()

def parse_message(message):
	try:
		data = json.loads(message)
		# FIXME: remove print in production
		print(data)
	except json.JSONDecodeError:
		print("Failed to decode JSON packet")
		data = None
	return data

def on_close():
	global running, root, video
	running = False
	video.running = False
	root.destroy()

def main():
	global root, canvas, video

	root = tk.Tk()
	root.title("Fencing Replay System")
	video = VideoManager(root=root)

    # canvas for video
	canvas = tk.Canvas(root, width=video.frame_width, height=video.frame_height)
	canvas.bind("<Configure>", lambda event: video.resize_canvas(event))
	video.canvas = canvas
	canvas.pack()

	# controls
	controls = ttk.Frame(root)
	controls.pack()
	btn_save = ttk.Button(controls, text="Save Last 10s", command=video.save_video)
	# btn_save.grid(row=0, column=0, padx=10, pady=5)
	btn_save.pack()

	# start video thread
	threading.Thread(target=video.update_frame, daemon=True).start()

	# start UDP listener thread
	threading.Thread(target=listen_for_udp, daemon=True).start()

	# handle window close
	root.protocol("WM_DELETE_WINDOW", on_close)
	root.mainloop()

if __name__ == "__main__":
    main()