"""UDP client for talking to an X-Air family mixer's OSC control port."""
from __future__ import annotations

import socket
import time

from .osc import OscMessage, decode_message, encode_message

DEFAULT_PORT = 10024


class XAirError(Exception):
    pass


class XAirTimeout(XAirError):
    def __init__(self, address: str):
        super().__init__(f"no reply from mixer for {address!r}")
        self.address = address


class XAirClient:
    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 2.0):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(timeout)
        self.timeout = timeout

    def close(self):
        self.sock.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def send_raw(self, address: str, typed_args):
        """typed_args: iterable of (typetag, value) pairs."""
        self.sock.sendto(encode_message(address, typed_args), self.addr)

    def send(self, address: str, *typed_args):
        self.send_raw(address, typed_args)

    def _recv(self, timeout: float) -> OscMessage | None:
        self.sock.settimeout(timeout)
        try:
            data, _ = self.sock.recvfrom(65536)
        except socket.timeout:
            return None
        try:
            return decode_message(data)
        except Exception:
            return None

    def query(self, address: str, retries: int = 4, timeout: float = 0.5) -> list:
        """Send `address` with no arguments (a "get"), and wait for the
        mixer's reply to that same address. Returns the reply's args."""
        deadline_each = timeout
        for _ in range(retries):
            self.send(address)
            end = time.time() + deadline_each
            while True:
                remaining = end - time.time()
                if remaining <= 0:
                    break
                msg = self._recv(remaining)
                if msg is None:
                    break
                if msg.address == address:
                    return msg.args
                # Not the reply we're waiting for (meter stream, other
                # traffic) -- keep waiting for the rest of this attempt.
        raise XAirTimeout(address)

    def node_get(self, node_path: str, retries: int = 4, timeout: float = 0.5) -> str:
        """Ask the mixer for a node's data in scene-file text form (the same
        mechanism XAirGetScene uses): send /node with one string argument,
        the node path *without* its leading slash, and get back a single
        string argument holding the full formatted scene line, e.g.
        '/ch/01/config "Rx 1" 9 In01 U01'."""
        path = node_path.lstrip("/")
        deadline_each = timeout
        for _ in range(retries):
            self.send("/node", ("s", path))
            end = time.time() + deadline_each
            while True:
                remaining = end - time.time()
                if remaining <= 0:
                    break
                msg = self._recv(remaining)
                if msg is None:
                    break
                for arg in msg.args:
                    if isinstance(arg, str) and arg.startswith("/"):
                        return arg.strip()
        raise XAirTimeout(f"/node {path}")

    def check_connection(self):
        try:
            self.query("/xinfo", retries=2, timeout=0.75)
        except XAirTimeout:
            raise XAirError(
                f"could not reach an X-Air mixer at {self.addr[0]}:{self.addr[1]}"
            ) from None
