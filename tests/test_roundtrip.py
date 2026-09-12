"""End-to-end test: load the real captured sample-scene.scn into a
mock mixer, then save it back out, and check that every node's essential
values (ignoring purely cosmetic formatting) round-trip correctly."""
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mock_mixer import MockMixer  # noqa: E402

from xair_scene_manager.client import XAirClient  # noqa: E402
from xair_scene_manager.loader import load_scene_text  # noqa: E402
from xair_scene_manager.saver import save_scene_lines  # noqa: E402


def main():
    scn_path = Path(__file__).resolve().parent.parent / "sample-scene.scn"
    original_text = scn_path.read_text()

    mixer = MockMixer()
    mixer.start()
    try:
        client = XAirClient("127.0.0.1", port=mixer.port, timeout=1.0)
        client.check_connection()

        warnings = []
        applied, skipped = load_scene_text(
            client, original_text, delay=0.001, on_warning=warnings.append
        )
        print(f"loaded: applied={applied} skipped={skipped}")
        for w in warnings[:20]:
            print("WARN:", w)
        assert skipped == 0, f"{skipped} lines were skipped during load"

        lines = save_scene_lines(client)
        client.close()
    finally:
        mixer.stop()

    saved_text = "\n".join(lines) + "\n"

    orig_lines = {}
    for line in original_text.splitlines():
        line = line.strip()
        if not line:
            continue
        toks = shlex.split(line, posix=True)
        orig_lines[toks[0]] = toks[1:]

    saved_lines = {}
    for line in saved_text.splitlines():
        line = line.strip()
        if not line:
            continue
        toks = shlex.split(line, posix=True)
        saved_lines[toks[0]] = toks[1:]

    from xair_scene_manager.codecs import parse_freq

    def value_key(codec_hint, tok):
        # best-effort "is this the same value" comparator across cosmetic
        # formatting differences (e.g. "+0.0" vs "0.0", "10k02" vs 10020.0)
        t = tok.strip().strip('"')
        if t.upper() in ("ON", "OFF", "-OO"):
            return t.upper()
        try:
            return round(parse_freq(t), 1)
        except ValueError:
            pass
        try:
            return round(float(t), 1)
        except ValueError:
            return t.upper()

    mismatches = []
    missing = []
    for addr, orig_args in orig_lines.items():
        if addr.startswith("/fx/") and addr.endswith("/par"):
            continue  # raw passthrough, not value-checked here
        saved_args = saved_lines.get(addr)
        if saved_args is None:
            missing.append(addr)
            continue
        if len(saved_args) != len(orig_args):
            mismatches.append((addr, "arg count", orig_args, saved_args))
            continue
        for o, s in zip(orig_args, saved_args):
            if value_key(None, o) != value_key(None, s):
                mismatches.append((addr, "value", orig_args, saved_args))
                break

    print(f"compared {len(orig_lines)} lines: missing={len(missing)} mismatches={len(mismatches)}")
    for m in missing[:20]:
        print("MISSING IN SAVE:", m)
    for m in mismatches[:30]:
        print("MISMATCH:", m)

    assert not missing, "some nodes were not present in the saved output"
    assert not mismatches, "some nodes round-tripped to a different value"
    print("ROUNDTRIP OK")


if __name__ == "__main__":
    main()
