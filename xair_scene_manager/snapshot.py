"""Snapshot (scene memory slot) load/save, by index or by name.

Per the X-Air OSC command reference:
  /-snap/index  i 1-64   currently selected slot (does not recall it)
  /-snap/load   i 1-64   recall (load) that slot into the live mixer state
  /-snap/save   i 1-64   store the live mixer state into that slot
  /-snap/name   s        name of the currently *selected* slot (get/set)
"""
from __future__ import annotations

from .client import XAirClient, XAirTimeout

MAX_SNAPSHOTS = 64


class SnapshotNotFound(Exception):
    def __init__(self, name: str):
        super().__init__(f"no snapshot named {name!r} found (scanned 1-{MAX_SNAPSHOTS})")
        self.name = name


def find_snapshot_index_by_name(client: XAirClient, name: str, max_slots: int = MAX_SNAPSHOTS):
    target = name.strip().lower()
    for i in range(1, max_slots + 1):
        client.send("/-snap/index", ("i", i))
        try:
            args = client.query("/-snap/name", retries=2, timeout=0.3)
        except XAirTimeout:
            continue
        if args and isinstance(args[0], str) and args[0].strip().lower() == target:
            return i
    return None


def resolve_snapshot(client: XAirClient, snapshot: str) -> int:
    """snapshot is either a 1-64 index (as a string) or a snapshot name."""
    try:
        index = int(snapshot)
    except ValueError:
        index = None
    if index is not None:
        if not (1 <= index <= MAX_SNAPSHOTS):
            raise ValueError(f"snapshot index must be between 1 and {MAX_SNAPSHOTS}, got {index}")
        return index
    found = find_snapshot_index_by_name(client, snapshot)
    if found is None:
        raise SnapshotNotFound(snapshot)
    return found


def load_snapshot(client: XAirClient, snapshot: str) -> int:
    index = resolve_snapshot(client, snapshot)
    client.send("/-snap/load", ("i", index))
    return index


def save_snapshot(client: XAirClient, index: int, name: str | None = None):
    if not (1 <= index <= MAX_SNAPSHOTS):
        raise ValueError(f"snapshot index must be between 1 and {MAX_SNAPSHOTS}, got {index}")
    client.send("/-snap/save", ("i", index))
    if name:
        client.send("/-snap/index", ("i", index))
        client.send("/-snap/name", ("s", name))
