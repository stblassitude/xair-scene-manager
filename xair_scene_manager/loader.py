"""Apply a .scn scene file's lines to a live mixer, by decomposing each line
into the granular OSC SET messages the mixer actually understands."""
from __future__ import annotations

import re
import shlex
import time

from .client import XAirClient
from .codecs import RawC
from .schema import SCHEMA

_FX_PAR_RE = re.compile(r"^/fx/([1-4])/par$")


def parse_scene_line(line: str):
    """Returns (address, tokens) or None for a blank/comment/header line."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    tokens = shlex.split(line, posix=True)
    if not tokens or not tokens[0].startswith("/"):
        return None
    return tokens[0], tokens[1:]


def apply_line(client: XAirClient, address: str, args, delay: float = 0.0, on_warning=None):
    """Send the granular OSC SET messages for one scene line. Returns True
    if the line was understood and applied, False if it was skipped."""

    def warn(msg):
        if on_warning:
            on_warning(msg)

    m = _FX_PAR_RE.match(address)
    if m:
        n = m.group(1)
        for i, tok in enumerate(args, start=1):
            tag, val = RawC().encode(tok)
            client.send(f"/fx/{n}/par/{i:02d}", (tag, val))
            if delay:
                time.sleep(delay)
        return True

    fields = SCHEMA.get(address)
    if fields is None:
        warn(f"skipping unrecognized node {address!r}")
        return False
    if len(fields) != len(args):
        warn(
            f"skipping {address!r}: expected {len(fields)} value(s), "
            f"line has {len(args)}: {args!r}"
        )
        return False

    for (leaf, codec), tok in zip(fields, args):
        try:
            tag, val = codec.encode(tok)
        except ValueError as e:
            warn(f"skipping {address}/{leaf}: {e}")
            continue
        client.send(f"{address}/{leaf}", (tag, val))
        if delay:
            time.sleep(delay)
    return True


def load_scene_text(client: XAirClient, text: str, delay: float = 0.0, on_line=None, on_warning=None):
    applied = 0
    skipped = 0
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        parsed = parse_scene_line(raw_line)
        if parsed is None:
            continue
        address, args = parsed

        def warn(msg, _lineno=lineno):
            if on_warning:
                on_warning(f"line {_lineno}: {msg}")

        if apply_line(client, address, args, delay=delay, on_warning=warn):
            applied += 1
            if on_line:
                on_line(address)
        else:
            skipped += 1
    return applied, skipped
