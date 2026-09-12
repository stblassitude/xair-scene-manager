"""Conversions between the human-readable text used in .scn scene files and
the normalized values the X-Air mixer expects on its granular OSC control
addresses (e.g. /ch/01/mix/fader is a float in [0.0, 1.0]).

The linear/log/fader-level formulas below are the same ones used by the
xair-api-python project (MIT-licensed, actively maintained, used against
real X-Air/Midas hardware) and match the ranges documented on the
Behringer World OSC wiki. The scene-line *tokens* (things like "10k02",
"-oo", quoted names, "%0000" bitmasks) match the format produced by the
Patrick-Gilles Maillot / Ken Mitchell XAirGetScene/XAirSetScene C tools,
which are the tools that originally defined this .scn dialect.
"""
from __future__ import annotations

import math
import re


def lin_get(lo: float, hi: float, val: float) -> float:
    return lo + (hi - lo) * val


def lin_set(lo: float, hi: float, val: float) -> float:
    return (val - lo) / (hi - lo)


def log_get(lo: float, hi: float, val: float) -> float:
    return lo * math.exp(math.log(hi / lo) * val)


def log_set(lo: float, hi: float, val: float) -> float:
    return math.log(val / lo) / math.log(hi / lo)


def level_get(val: float) -> float:
    """Raw [0,1] fader/send value -> dB, using the X-Air non-linear taper."""
    if val >= 1:
        return 10.0
    elif val >= 0.5:
        return round((40 * val) - 30, 1)
    elif val >= 0.25:
        return round((80 * val) - 50, 1)
    elif val >= 0.0625:
        return round((160 * val) - 70, 1)
    elif val >= 0:
        return round((480 * val) - 90, 1)
    return -90.0


def level_set(db: float) -> float:
    """dB -> raw [0,1] fader/send value, using the X-Air non-linear taper."""
    if db >= 10:
        return 1.0
    elif db >= -10:
        return (db + 30) / 40
    elif db >= -30:
        return (db + 50) / 80
    elif db >= -60:
        return (db + 70) / 160
    elif db >= -90:
        return (db + 90) / 480
    return 0.0


_FREQ_K_RE = re.compile(r"^[+-]?\d+[kK]\d*$")


def parse_freq(token: str) -> float:
    """Parse a frequency token: plain Hz ("124.7") or X-Air "10k02" kHz form."""
    t = token.strip()
    if _FREQ_K_RE.match(t):
        return float(t.lower().replace("k", ".")) * 1000.0
    return float(t)


def format_freq(hz: float) -> str:
    """Render a Hz value using the same "10k02" style X-Air Edit uses."""
    if hz >= 1000:
        s = f"{hz / 1000:.2f}"
        if s.endswith("0"):
            s = s[:-1]
        return s.replace(".", "k")
    return f"{hz:.1f}"


def format_db(db: float, decimals: int = 1) -> str:
    if db <= -90:
        return "-oo"
    sign = "+" if db >= 0 else ""
    return f"{sign}{db:.{decimals}f}"


def format_signed(val: float, decimals: int = 1) -> str:
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.{decimals}f}"


class Codec:
    """Encodes a scene-file text token into a typed OSC argument for SET,
    and (optionally) decodes a raw OSC reply value back into scene-file text
    for building a synthetic scene line (used only as a fallback -- normal
    saving relies on the mixer's own /node text reply instead)."""

    def encode(self, token: str):
        raise NotImplementedError


class OnOffC(Codec):
    """Boolean field. `on_word` is the literal text meaning "true"; any other
    token (including the usual "OFF") is treated as false. This matches the
    X-Air scene format, where a few fields use a non-"ON" true-word (e.g.
    solo chmode/busmode use "PFL")."""

    def __init__(self, on_word: str = "ON"):
        self.on_word = on_word

    def encode(self, token: str):
        return "i", 1 if token.strip().upper() == self.on_word.upper() else 0


class IntC(Codec):
    def encode(self, token: str):
        return "i", int(round(float(token)))


class StrC(Codec):
    def encode(self, token: str):
        return "s", token


class LinC(Codec):
    def __init__(self, lo: float, hi: float):
        self.lo, self.hi = lo, hi

    def encode(self, token: str):
        return "f", lin_set(self.lo, self.hi, float(token))


class LogFreqC(Codec):
    def __init__(self, lo: float = 20.0, hi: float = 20000.0):
        self.lo, self.hi = lo, hi

    def encode(self, token: str):
        return "f", log_set(self.lo, self.hi, parse_freq(token))


class LogTimeC(Codec):
    def __init__(self, lo: float, hi: float):
        self.lo, self.hi = lo, hi

    def encode(self, token: str):
        return "f", log_set(self.lo, self.hi, float(token))


class LevelC(Codec):
    def encode(self, token: str):
        t = token.strip().lower()
        db = -90.0 if t in ("-oo", "-inf") else float(token)
        return "f", level_set(db)


class PanC(Codec):
    def encode(self, token: str):
        return "f", lin_set(-100.0, 100.0, float(token))


class EnumC(Codec):
    def __init__(self, options):
        self.options = list(options)

    def encode(self, token: str):
        t = token.strip()
        for i, opt in enumerate(self.options):
            if opt.lower() == t.lower():
                return "i", i
        try:
            return "i", int(t)
        except ValueError:
            raise ValueError(
                f"unrecognized value {token!r}, expected one of {self.options}"
            ) from None


class BitmaskC(Codec):
    def encode(self, token: str):
        t = token.strip().lstrip("%")
        return "i", int(t, 2) if t else 0


class EqQC(Codec):
    """EQ band Q: displayed 0.3-10 (inverted log scale on the wire)."""

    def encode(self, token: str):
        return "f", 1.0 - log_set(0.3, 10.0, float(token))


class PercentC(Codec):
    def encode(self, token: str):
        return "f", lin_set(0.0, 100.0, float(token))


class RawC(Codec):
    """Best-effort passthrough: infer int/float/string from the token's own
    syntax. Used only for /fx/N/par, whose per-slot meaning depends on the
    effect type and isn't otherwise documented."""

    _INT_RE = re.compile(r"^[+-]?\d+$")
    _FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")

    def encode(self, token: str):
        t = token.strip()
        if self._INT_RE.match(t):
            return "i", int(t)
        if self._FLOAT_RE.match(t):
            return "f", float(t)
        return "s", t
