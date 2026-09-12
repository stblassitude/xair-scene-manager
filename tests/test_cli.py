"""Exercises the real `xair-scene-manager` executable as a subprocess
against the mock mixer, covering all four subcommands."""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mock_mixer import MockMixer  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "xair-scene-manager"
SCN = ROOT / "sample-scene.scn"


def run(*args):
    result = subprocess.run(
        [sys.executable, str(EXE), *args],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result


def main():
    mixer = MockMixer()
    mixer.start()
    try:
        base = ["-x", "127.0.0.1", "-p", str(mixer.port), "--timeout", "1.0", "--delay-ms", "1"]

        r = run(*base, "load-file", str(SCN))
        print("load-file:", r.returncode, r.stdout.strip().splitlines()[-1] if r.stdout else "", r.stderr[-500:])
        assert r.returncode == 0, r.stderr
        assert "applied 693 node(s), skipped 0" in r.stdout

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.scn"
            r = run(*base, "save-file", str(out))
            print("save-file:", r.returncode, r.stdout.strip())
            assert r.returncode == 0, r.stderr
            assert out.exists()
            saved = out.read_text().splitlines()
            assert len(saved) == 693, len(saved)

        r = run(*base, "save-snapshot", "5", "Test Scene")
        print("save-snapshot:", r.returncode, r.stdout.strip())
        assert r.returncode == 0, r.stderr
        assert mixer.snap_names.get(5) == "Test Scene"

        r = run(*base, "load-snapshot", "5")
        print("load-snapshot by index:", r.returncode, r.stdout.strip())
        assert r.returncode == 0, r.stderr

        r = run(*base, "load-snapshot", "Test Scene")
        print("load-snapshot by name:", r.returncode, r.stdout.strip())
        assert r.returncode == 0, r.stderr
        assert "loaded snapshot 5" in r.stdout

        r = run(*base, "load-snapshot", "Does Not Exist")
        print("load-snapshot missing name:", r.returncode, r.stderr.strip())
        assert r.returncode != 0

        r = run("-x", "127.0.0.1", "-p", "9", "--timeout", "0.3", "load-snapshot", "1")
        print("bad connection:", r.returncode, r.stderr.strip())
        assert r.returncode != 0

        print("CLI TESTS OK")
    finally:
        mixer.stop()


if __name__ == "__main__":
    main()
