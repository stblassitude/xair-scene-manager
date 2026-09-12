from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .client import DEFAULT_PORT, XAirClient, XAirError, XAirTimeout
from .loader import load_scene_text
from .saver import save_scene_lines
from .snapshot import SnapshotNotFound, load_snapshot, save_snapshot


def _connect(args) -> XAirClient:
    client = XAirClient(args.ip, port=args.port, timeout=args.timeout)
    try:
        client.check_connection()
    except XAirError as e:
        client.close()
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1)
    return client


def cmd_load_snapshot(args):
    client = _connect(args)
    try:
        index = load_snapshot(client, args.snapshot)
        print(f"loaded snapshot {index}")
    except (SnapshotNotFound, ValueError, XAirTimeout) as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1)
    finally:
        client.close()


def cmd_load_file(args):
    path = Path(args.filename)
    try:
        text = path.read_text()
    except OSError as e:
        print(f"error: could not read {path}: {e}", file=sys.stderr)
        raise SystemExit(1)

    client = _connect(args)
    try:
        def on_line(addr):
            if args.verbose:
                print(f"set {addr}")

        def on_warning(msg):
            print(f"warning: {msg}", file=sys.stderr)

        applied, skipped = load_scene_text(
            client, text, delay=args.delay_ms / 1000.0, on_line=on_line, on_warning=on_warning
        )
        print(f"applied {applied} node(s), skipped {skipped}")
    finally:
        client.close()


def cmd_save_snapshot(args):
    client = _connect(args)
    try:
        save_snapshot(client, args.snapshot_index, args.snapshot_name)
        if args.snapshot_name:
            print(f"saved current state to snapshot {args.snapshot_index} ({args.snapshot_name!r})")
        else:
            print(f"saved current state to snapshot {args.snapshot_index}")
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1)
    finally:
        client.close()


def cmd_save_file(args):
    client = _connect(args)
    try:
        def on_progress(addr):
            if args.verbose:
                print(f"get {addr}")

        def on_warning(msg):
            print(f"warning: {msg}", file=sys.stderr)

        lines = save_scene_lines(client, on_progress=on_progress, on_warning=on_warning)
    finally:
        client.close()

    path = Path(args.filename)
    try:
        path.write_text("\n".join(lines) + "\n")
    except OSError as e:
        print(f"error: could not write {path}: {e}", file=sys.stderr)
        raise SystemExit(1)
    print(f"saved {len(lines)} node(s) to {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xair-scene-manager",
        description="Copy, export, and import Behringer X-Air mixer scenes.",
    )
    parser.add_argument("-x", "--ip", required=True, help="mixer IP address or hostname")
    parser.add_argument("-p", "--port", type=int, default=DEFAULT_PORT, help=f"mixer OSC port (default {DEFAULT_PORT})")
    parser.add_argument("--timeout", type=float, default=2.0, help="per-request UDP timeout in seconds (default 2.0)")
    parser.add_argument(
        "--delay-ms", type=float, default=2.0,
        help="delay in milliseconds between OSC SET messages while loading a scene (default 2.0)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="print each node as it's sent/fetched")

    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("load-snapshot", help="load a mixer snapshot by index or name")
    p.add_argument("snapshot", help="snapshot index (1-64) or name")
    p.set_defaults(func=cmd_load_snapshot)

    p = sub.add_parser("load-file", help="load a .scn scene file onto the mixer")
    p.add_argument("filename")
    p.set_defaults(func=cmd_load_file)

    p = sub.add_parser("save-snapshot", help="save current mixer state into a snapshot slot")
    p.add_argument("snapshot_index", type=int, help="snapshot index (1-64)")
    p.add_argument("snapshot_name", nargs="?", default=None, help="optional new name for the snapshot")
    p.set_defaults(func=cmd_save_snapshot)

    p = sub.add_parser("save-file", help="save current mixer state to a .scn file")
    p.add_argument("filename")
    p.set_defaults(func=cmd_save_file)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
