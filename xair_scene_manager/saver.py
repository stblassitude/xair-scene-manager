"""Read a full scene dump back from a live mixer, using the mixer's own
`/node` text format (see XAirClient.node_get) -- no value decoding needed,
the mixer hands back each node already formatted the way a .scn file wants
it."""
from __future__ import annotations

import re

from .client import XAirClient, XAirTimeout
from .schema import SCHEMA

_FX_SLOT_RE = re.compile(r"^/fx/([1-4])$")


def iter_node_addresses():
    """All node addresses to include in a full scene dump, in a natural
    reading order (matching XAirGetScene's own output order). /fx/N/par is
    injected right after /fx/N, since it isn't in SCHEMA (its field count is
    variable and effect-type dependent)."""
    for addr in SCHEMA:
        yield addr
        m = _FX_SLOT_RE.match(addr)
        if m:
            yield f"/fx/{m.group(1)}/par"


def save_scene_lines(client: XAirClient, addresses=None, on_progress=None, on_warning=None):
    lines = []
    for addr in addresses if addresses is not None else iter_node_addresses():
        try:
            text = client.node_get(addr)
        except XAirTimeout:
            if on_warning:
                on_warning(f"no reply for {addr}, skipping")
            continue
        lines.append(text)
        if on_progress:
            on_progress(addr)
    return lines
