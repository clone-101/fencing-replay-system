import json
import logging
import socket
import threading
import time

import pytest

from utils.udp import JSON_KEYS, UDPListener, UDPMessage

LIGHTS = dict.fromkeys(JSON_KEYS, 0)
FULL = dict(
    LIGHTS,
    Green_Light=1,
    Right_Score=3, Left_Score=2,
    Minutes_Remaining=1, Seconds_Remaining=30,
    Yellow_Card_Green=0, Yellow_Card_Red=1,
    Red_Card_Green=0, Red_Card_Red=0,
    Priority_Left=1, Priority_Right=0,
)


def test_full_packet():
    msg = UDPMessage(json.dumps(FULL))
    assert msg.green == 1 and msg.red == 0
    assert msg.right_score == 3 and msg.left_score == 2
    assert msg.minutes_remaining == 1 and msg.seconds_remaining == 30
    assert msg.yellow_card_red == 1
    assert msg.priority_left == 1 and msg.priority_right == 0


def test_missing_light_key():
    data = dict(LIGHTS)
    del data['Red_Light']
    with pytest.raises(ValueError, match='Red_Light'):
        UDPMessage(json.dumps(data))


def test_malformed_json():
    with pytest.raises(ValueError):
        UDPMessage('not json')


def test_light_only_packet_has_none_optionals():
    msg = UDPMessage(json.dumps(LIGHTS))
    assert msg.right_score is None
    assert msg.minutes_remaining is None
    assert msg.priority_right is None


def start_listener(callback, **kwargs):
    listener = UDPListener(port=0, callback=callback, **kwargs)
    listener.start()
    deadline = time.time() + 2
    while listener.bound_port is None and listener.error is None and time.time() < deadline:
        time.sleep(0.01)
    return listener


def send(port, payload):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(payload.encode('utf-8'), ('127.0.0.1', port))


def test_listener_delivers_message():
    got = []
    event = threading.Event()
    listener = start_listener(lambda m: (got.append(m), event.set()))
    try:
        send(listener.bound_port, json.dumps(FULL))
        assert event.wait(2)
        assert isinstance(got[0].received_at, float)
        assert got[0].right_score == 3
    finally:
        listener.stop()
        listener.join(timeout=2)


def test_listener_survives_invalid_datagram():
    got = []
    event = threading.Event()
    listener = start_listener(lambda m: (got.append(m), event.set()))
    try:
        send(listener.bound_port, 'garbage')
        send(listener.bound_port, json.dumps(LIGHTS))
        assert event.wait(2)
        assert listener.is_alive()
    finally:
        listener.stop()
        listener.join(timeout=2)


def test_sender_ip_filter_drops_other_senders():
    got = []
    listener = start_listener(got.append, sender_ip='10.9.9.9')
    try:
        send(listener.bound_port, json.dumps(LIGHTS))
        time.sleep(0.3)
        assert got == []
        assert listener.is_alive()
    finally:
        listener.stop()
        listener.join(timeout=2)


def test_stop_ends_thread_without_packets():
    listener = start_listener(lambda m: None)
    listener.stop()
    listener.join(timeout=2)
    assert not listener.is_alive()


def test_bind_failure_sets_error(caplog):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as busy:
        busy.bind(('0.0.0.0', 0))
        port = busy.getsockname()[1]
        listener = UDPListener(port=port, callback=lambda m: None)
        with caplog.at_level(logging.ERROR):
            listener.start()
            listener.join(timeout=2)
    assert isinstance(listener.error, OSError)
    assert not listener.is_alive()
    assert 'failed to bind' in caplog.text
