import json
import logging
import socket
import threading
import time

logger = logging.getLogger(__name__)

JSON_KEYS = ['Green_Light', 'Red_Light', 'White_Green_Light', 'White_Red_Light', 'Yellow_Green_Light', 'Yellow_Red_Light']
OPTIONAL_KEYS = [
    'Right_Score', 'Left_Score', 'Minutes_Remaining', 'Seconds_Remaining',
    'Yellow_Card_Green', 'Yellow_Card_Red', 'Red_Card_Green', 'Red_Card_Red',
    'Priority_Left', 'Priority_Right',
]

class UDPListener(threading.Thread):
    def __init__(self, port, callback, sender_ip=None):
        super().__init__(daemon=True)
        self.port = port
        self.callback = callback
        self.sender_ip = sender_ip
        self.running = True
        self.error = None
        self.bound_port = None

    def run(self):
        soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            soc.bind(('0.0.0.0', self.port))
            soc.settimeout(0.5)
            self.bound_port = soc.getsockname()[1]
        except OSError as e:
            self.error = e
            logger.error("UDP listener failed to bind port %s: %s", self.port, e)
            soc.close()
            return

        while self.running:
            try:
                data, addr = soc.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError as e:
                if self.running:
                    logger.error("UDP receive error: %s", e)
                break
            received_at = time.monotonic()

            if self.sender_ip and addr[0] != self.sender_ip:
                continue

            try:
                msg = UDPMessage(data.decode('utf-8'))
            except (ValueError, UnicodeDecodeError) as e:
                logger.warning("Dropping invalid UDP packet from %s: %s", addr[0], e)
                continue

            msg.received_at = received_at
            try:
                self.callback(msg)
            except Exception:
                logger.exception("UDP callback raised")
        soc.close()

    def stop(self):
        self.running = False


class UDPMessage:
    def __init__(self, message):
        data = self.__parse_message(message)

        self.green, self.red, self.white_green, self.white_red, self.yellow_green, self.yellow_red = (
            data[key] for key in JSON_KEYS
        )
        self.right_score = data.get('Right_Score')
        self.left_score = data.get('Left_Score')
        self.minutes_remaining = data.get('Minutes_Remaining')
        self.seconds_remaining = data.get('Seconds_Remaining')
        self.yellow_card_green = data.get('Yellow_Card_Green')
        self.yellow_card_red = data.get('Yellow_Card_Red')
        self.red_card_green = data.get('Red_Card_Green')
        self.red_card_red = data.get('Red_Card_Red')
        self.priority_left = data.get('Priority_Left')
        self.priority_right = data.get('Priority_Right')
        self.received_at = None

    def __str__(self):
        return f"Lights: green={self.green}, red={self.red}, white_green={self.white_green}, white_red={self.white_red}, yellow_green={self.yellow_green}, yellow_red={self.yellow_red}"

    @staticmethod
    def __parse_message(message):
        try:
            data = json.loads(message)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON packet: {e}") from e
        if not isinstance(data, dict):
            raise ValueError("Invalid JSON packet: expected an object")
        missing = [key for key in JSON_KEYS if key not in data]
        if missing:
            raise ValueError(f"JSON packet missing keys: {', '.join(missing)}")
        return data
