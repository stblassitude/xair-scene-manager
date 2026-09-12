"""A minimal mock X-Air mixer for testing: a UDP server that
- stores whatever raw value is SET at any granular OSC address,
- replies to GET (an address sent with no args) with the stored value,
- replies to /node <path> with the corresponding .scn-format text line,
  built by applying the schema's codecs in reverse,
- replies to /xinfo,
- implements a minimal /-snap/index, /-snap/name, /-snap/load, /-snap/save,
so we can test the client/loader/saver against something real, without
needing actual hardware.
"""
from __future__ import annotations

import math
import socket
import threading

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xair_scene_manager.codecs import (
    BitmaskC,
    EnumC,
    EqQC,
    IntC,
    LevelC,
    LinC,
    LogFreqC,
    LogTimeC,
    OnOffC,
    PanC,
    PercentC,
    StrC,
    format_db,
    format_freq,
    format_signed,
    level_get,
    log_get,
)
from xair_scene_manager.osc import decode_message, encode_message
from xair_scene_manager.schema import SCHEMA


def _decode_leaf_value(codec, raw_value) -> str:
    """Inverse of codec.encode(), used by the mock server to turn a stored
    raw OSC value back into scene-file text for a /node reply."""
    if isinstance(codec, OnOffC):
        return codec.on_word if raw_value else "OFF"
    if isinstance(codec, IntC):
        return str(int(round(raw_value)))
    if isinstance(codec, StrC):
        return raw_value
    if isinstance(codec, LinC):
        val = codec.lo + (codec.hi - codec.lo) * raw_value
        return format_signed(val, 1)
    if isinstance(codec, LogFreqC):
        hz = log_get(codec.lo, codec.hi, raw_value)
        return format_freq(hz)
    if isinstance(codec, LogTimeC):
        val = log_get(codec.lo, codec.hi, raw_value)
        return f"{val:.1f}" if val < 100 else f"{val:.0f}"
    if isinstance(codec, LevelC):
        return format_db(level_get(raw_value), 1)
    if isinstance(codec, PanC):
        val = -100.0 + 200.0 * raw_value
        return format_signed(round(val), 0)
    if isinstance(codec, EnumC):
        return codec.options[int(raw_value)]
    if isinstance(codec, BitmaskC):
        return "%" + format(int(raw_value), "04b")
    if isinstance(codec, EqQC):
        val = math.exp(math.log(10.0 / 0.3) * (1.0 - raw_value)) * 0.3
        return format_signed(round(val, 1), 1).lstrip("+")
    if isinstance(codec, PercentC):
        val = raw_value * 100.0
        return str(int(round(val)))
    raise TypeError(f"no reverse formatter for {codec!r}")


class MockMixer:
    def __init__(self, host="127.0.0.1", port=0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.sock.settimeout(0.2)
        self.port = self.sock.getsockname()[1]
        self.values = {}  # address -> raw value (int/float/str)
        self.snap_index = 1
        self.snap_names = {}
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

        # seed defaults so /node has something to report before any SET
        for addr, fields in SCHEMA.items():
            for leaf, codec in fields:
                leaf_addr = f"{addr}/{leaf}"
                if isinstance(codec, StrC):
                    self.values[leaf_addr] = ""
                elif isinstance(codec, (OnOffC, IntC, EnumC, BitmaskC)):
                    self.values[leaf_addr] = 0
                else:
                    self.values[leaf_addr] = 0.0

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)
        self.sock.close()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()

    def _run(self):
        while not self._stop.is_set():
            try:
                data, addr = self.sock.recvfrom(65536)
            except socket.timeout:
                continue
            try:
                msg = decode_message(data)
            except Exception:
                continue
            self._handle(msg, addr)

    def _reply(self, addr, address, typed_args):
        self.sock.sendto(encode_message(address, typed_args), addr)

    def _handle(self, msg, addr):
        a = msg.address
        args = msg.args

        if a == "/xinfo":
            self._reply(addr, "/xinfo", [("s", "127.0.0.1"), ("s", "MOCK"), ("s", "XR18"), ("s", "1.17")])
            return

        if a == "/node":
            if not args:
                return
            path = "/" + str(args[0]).lstrip("/")
            fields = SCHEMA.get(path)
            if fields is None:
                self._reply(addr, "/node", [("s", f"{path} ?")])
                return
            parts = [path]
            for leaf, codec in fields:
                raw = self.values.get(f"{path}/{leaf}")
                text = _decode_leaf_value(codec, raw)
                if isinstance(codec, StrC):
                    parts.append(f'"{text}"')
                else:
                    parts.append(text)
            self._reply(addr, "/node", [("s", " ".join(parts))])
            return

        if a == "/-snap/index":
            if args:
                self.snap_index = int(args[0])
            else:
                self._reply(addr, "/-snap/index", [("i", self.snap_index)])
            return

        if a == "/-snap/name":
            if args:
                self.snap_names[self.snap_index] = str(args[0])
            else:
                self._reply(addr, "/-snap/name", [("s", self.snap_names.get(self.snap_index, ""))])
            return

        if a == "/-snap/load":
            return

        if a == "/-snap/save":
            return

        # Generic granular get/set.
        if args:
            self.values[a] = args[0]
        else:
            val = self.values.get(a)
            if val is None:
                return
            tag = "s" if isinstance(val, str) else ("i" if isinstance(val, int) else "f")
            self._reply(addr, a, [(tag, val)])
