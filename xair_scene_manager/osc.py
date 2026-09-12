"""Minimal OSC 1.0 message encode/decode (UDP wire format only, no bundles).

Only the subset needed to talk to a Behringer X-Air mixer: string ('s'),
int32 ('i') and float32 ('f') arguments.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass


def _pad_len(n: int) -> int:
    """Number of zero bytes needed to pad n bytes to a 4-byte boundary."""
    return (4 - (n % 4)) % 4


def encode_osc_string(s: str) -> bytes:
    b = s.encode("utf-8") + b"\x00"
    return b + b"\x00" * _pad_len(len(b))


def encode_message(address: str, args) -> bytes:
    """args: iterable of (typetag_char, value) pairs, typetag in 'i'/'f'/'s'."""
    typetags = ","
    payload = b""
    for tag, val in args:
        if tag == "i":
            typetags += "i"
            payload += struct.pack(">i", int(val))
        elif tag == "f":
            typetags += "f"
            payload += struct.pack(">f", float(val))
        elif tag == "s":
            typetags += "s"
            payload += encode_osc_string(str(val))
        else:
            raise ValueError(f"unsupported OSC typetag {tag!r}")
    return encode_osc_string(address) + encode_osc_string(typetags) + payload


def _read_osc_string(data: bytes, offset: int):
    end = data.index(b"\x00", offset)
    s = data[offset:end].decode("utf-8", errors="replace")
    total = end - offset + 1
    total += _pad_len(total)
    return s, offset + total


@dataclass
class OscMessage:
    address: str
    args: list


def decode_message(data: bytes) -> OscMessage:
    if data.startswith(b"#bundle\x00"):
        raise ValueError("OSC bundles are not supported")
    address, offset = _read_osc_string(data, 0)
    if offset >= len(data):
        return OscMessage(address, [])
    typetags, offset = _read_osc_string(data, offset)
    if not typetags.startswith(","):
        raise ValueError("malformed OSC typetag string")
    args = []
    for tag in typetags[1:]:
        if tag == "i":
            (val,) = struct.unpack_from(">i", data, offset)
            offset += 4
            args.append(val)
        elif tag == "f":
            (val,) = struct.unpack_from(">f", data, offset)
            offset += 4
            args.append(val)
        elif tag == "s":
            val, offset = _read_osc_string(data, offset)
            args.append(val)
        else:
            # Unknown/unsupported type tag (e.g. blobs on meter messages);
            # stop decoding further args rather than guessing their size.
            break
    return OscMessage(address, args)
