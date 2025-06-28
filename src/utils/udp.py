import json
import socket
import threading

JSON_KEYS = ['Green_Light', 'Red_light', 'White_Green_Light', 'White_Red_Light', 'Yellow_Green_Light', 'Yellow_Red_Light']

class UdpListener(threading.Thread):
    def __init__(self, port, callback):
        super().__init__(daemon=True)
        self.port = port
        self.callback = callback
        self.running = True

    def run(self):
        soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        soc.bind(('0.0.0.0', self.port))
        while self.running:
            try:
                data, _ = soc.recvfrom(1024)
                msg = UDPMessage(data.decode('utf-8'))
                if msg:
                    self.callback(msg)
            except Exception:
                if not self.running:
                    break
        soc.close()

    def stop(self):
        self.running = False


class UDPMessage:
	def __init__(self, message):

		message = self.__parse_message(message)

		if message:
			self.green, self.red, self.white_green, self.white_red, self.yellow_green, self.yellow_red = message
		else:
			raise ValueError("Invalid message")
		
	
	def __parse_message(self, message):
		try:
			data = json.loads(message)
			# print(data)
			if not all(key in data for key in JSON_KEYS):
				print("Incorrect JSON packet format")
		except json.JSONDecodeError:
			print("Failed to decode JSON packet")
			data = None
		
		return tuple(data[key] for key in JSON_KEYS) if data else None