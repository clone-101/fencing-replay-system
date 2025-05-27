import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime
import os
import cv2 # type: ignore
import threading
from collections import deque
import time
import socket

# constants
DEFAULT_FPS = 30
BUFFER_SECONDS = 120
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
DEFAULT_PORT = 5050

# global variables
running = True
frame_buffer = None
vid = None
fps = DEFAULT_FPS
camera_index = 0

# UDP global variables
port = DEFAULT_PORT
wemos_ip = ''
udp_message = None

# tkinter global variables
root = None
canvas = None

def update_frame():
    global running, frame_buffer, vid, fps
    while running:
        ret, frame = vid.read()
        if ret:
            frame_buffer.append(frame.copy())
            display_frame(frame)
        time.sleep(1 / fps)

def display_frame(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame)
    imgtk = ImageTk.PhotoImage(image=img)
    root.after(0, _update_canvas, imgtk)

def _update_canvas(imgtk):
    canvas.create_image(0, 0, image=imgtk, anchor=tk.NW)
    canvas.image = imgtk

def save_video():
    global frame_buffer, fps
    os.makedirs("recordings", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recordings/{timestamp}.mp4"
    frames = list(frame_buffer)
    if not frames:
        print("No frames to save.")
        return
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    height, width, _ = frames[0].shape
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    for frame in frames:
        out.write(frame)
    out.release()
    print(f"Saved last 10 seconds to {filename}")

def listen_for_udp():
    global running, port, wemos_ip, udp_message
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soc.bind(('0.0.0.0', port))

    while running:
        try:
            data, addr = soc.recvfrom(1024)
            #if addr[0] == wemos_ip:
            udp_message = data.decode('utf-8')
            save_video()
        except socket.error as e:
            if not running:
                break
            print(f"Socket error: {e}")
    
    soc.close()

def on_close():
    global running, vid, root
    running = False
    if vid is not None:
        vid.release()
    root.destroy()

def main(buffer_seconds=BUFFER_SECONDS, port=DEFAULT_PORT, wemos_ip=''):
    global root, canvas, frame_buffer, vid, fps, camera_index

    root = tk.Tk()
    root.title("Fencing Replay System")

    # video source
    vid = cv2.VideoCapture(camera_index)
    vid.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    vid.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    fps = vid.get(cv2.CAP_PROP_FPS) or DEFAULT_FPS
    frame_buffer = deque(maxlen=int(fps * buffer_seconds))

    # canvas for video
    canvas = tk.Canvas(root, width=FRAME_WIDTH, height=FRAME_HEIGHT)
    canvas.pack()

    # controls
    controls = ttk.Frame(root)
    controls.pack()
    btn_save = ttk.Button(controls, text="Save Last 10s", command=save_video)
    btn_save.grid(row=0, column=0, padx=10, pady=5)

    # start video thread
    threading.Thread(target=update_frame, daemon=True).start()

    # start UDP listener thread
    threading.Thread(target=listen_for_udp, daemon=True).start()

    # handle window close
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main(buffer_seconds=10, port=DEFAULT_PORT)