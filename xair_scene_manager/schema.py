"""Declarative map of every node address that appears in an X-Air .scn scene
file, to the ordered list of granular OSC leaf fields it decomposes into.

This is used only for *loading* (a scene line's tokens are converted through
each field's codec and sent to the corresponding granular OSC address).
Saving does not need this table: the mixer's `/node` command returns each
node already formatted as scene-file text (see client.py), so saving just
needs the list of node addresses, which is `SCHEMA.keys()`.

Address ordering matches sample-scene.scn / XAirGetScene's own output
order, so a round-tripped file reads naturally.
"""
from __future__ import annotations

from .codecs import (
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
)
from .tables import (
    GEQ_BANDS,
    XAMGROUP,
    XAUXSRC,
    XCHFXSLOT,
    XCHRTNSRC,
    XDET,
    XDYNMODE,
    XDYNRATIO,
    XENV,
    XEQMODE,
    XEQTYP,
    XFILTERTYPE,
    XFXTYP4,
    XGATEMODE,
    XINSRC,
    XKEYSRC,
    XMAINSRC,
    XMXTAP,
    XRTNRTNSRC,
    XSOURCE,
    XSRCPOS,
    XUSBSRC,
)

NUM_CH = 16
NUM_BUS = 6
NUM_RTN = 4
NUM_FXSEND = 4
NUM_FX = 4
NUM_DCA = 4
NUM_P16 = 16
NUM_USB = 18
NUM_AUX = 6


def _gate_fields():
    return [
        ("on", OnOffC()),
        ("mode", EnumC(XGATEMODE)),
        ("thr", LinC(-80.0, 0.0)),
        ("range", LinC(3.0, 60.0)),
        ("attack", LinC(0.0, 120.0)),
        ("hold", LogTimeC(0.02, 2000.0)),
        ("release", LogTimeC(5.0, 4000.0)),
        ("keysrc", EnumC(XKEYSRC)),
    ]


def _filter_fields():
    return [("on", OnOffC()), ("type", EnumC(XFILTERTYPE)), ("f", LogFreqC())]


def _dyn_fields(keysrc: bool):
    fields = [
        ("on", OnOffC()),
        ("mode", EnumC(XDYNMODE)),
        ("det", EnumC(XDET)),
        ("env", EnumC(XENV)),
        ("thr", LinC(-60.0, 0.0)),
        ("ratio", EnumC(XDYNRATIO)),
        ("knee", LinC(0.0, 5.0)),
        ("mgain", LinC(0.0, 24.0)),
        ("attack", LinC(0.0, 120.0)),
        ("hold", LogTimeC(0.02, 2000.0)),
        ("release", LogTimeC(5.0, 4000.0)),
        ("mix", PercentC()),
    ]
    if keysrc:
        fields.append(("keysrc", EnumC(XKEYSRC)))
    fields.append(("auto", OnOffC()))
    return fields


def _insert_fields(fxslot_options):
    return [("on", OnOffC()), ("fxslot", EnumC(fxslot_options))]


def _eq_band_fields():
    return [("type", EnumC(XEQTYP)), ("f", LogFreqC()), ("g", LinC(-15.0, 15.0)), ("q", EqQC())]


def _geq_fields():
    return [(f"geq/{band}", LinC(-15.0, 15.0)) for band in GEQ_BANDS]


def _grp_fields():
    return [("dca", BitmaskC()), ("mute", BitmaskC())]


def _send_fields_with_pan():
    return [("level", LevelC()), ("grpon", OnOffC()), ("tap", EnumC(XMXTAP)), ("pan", PanC())]


def _send_fields_no_pan():
    return [("level", LevelC()), ("grpon", OnOffC()), ("tap", EnumC(XMXTAP))]


def _sends_for(prefix, num_sends):
    """Yield (address, fields) for the /mix/NN send sub-nodes of a strip.
    Sends 01, 03, 05 carry a pan control; the rest don't."""
    for i in range(1, num_sends + 1):
        addr = f"{prefix}/mix/{i:02d}"
        if i in (1, 3, 5):
            yield addr, _send_fields_with_pan()
        else:
            yield addr, _send_fields_no_pan()


def build_schema():
    schema = {}

    def add(addr, fields):
        schema[addr] = fields

    # ---- top-level /config ----
    add("/config/chlink", [(f"{i}-{i + 1}", OnOffC()) for i in range(1, NUM_CH, 2)])
    add("/config/buslink", [(f"{i}-{i + 1}", OnOffC()) for i in range(1, NUM_BUS, 2)])
    add(
        "/config/linkcfg",
        [("preamp", OnOffC()), ("eq", OnOffC()), ("dyn", OnOffC()), ("fdrmute", OnOffC())],
    )
    add(
        "/config/solo",
        [
            ("level", LevelC()),
            ("source", EnumC(XSOURCE)),
            ("sourcetrim", LinC(-18.0, 18.0)),
            ("chmode", OnOffC("PFL")),
            ("busmode", OnOffC("PFL")),
            ("dimatt", LinC(-40.0, 0.0)),
            ("dim", OnOffC()),
            ("mono", OnOffC()),
            ("mute", OnOffC()),
            ("dimplf", OnOffC()),
        ],
    )
    add("/config/amixenable", [("X", OnOffC()), ("Y", OnOffC())])
    add("/config/amixlock", [("X", OnOffC()), ("Y", OnOffC())])
    add("/config/mute", [(str(i), OnOffC()) for i in range(1, 5)])

    # ---- channels ----
    for ch in range(1, NUM_CH + 1):
        p = f"/ch/{ch:02d}"
        add(f"{p}/config", [("name", StrC()), ("color", IntC()), ("insrc", EnumC(XINSRC)), ("rtnsrc", EnumC(XCHRTNSRC))])
        add(f"{p}/preamp", [("rtntrim", LinC(-18.0, 18.0)), ("rtnsw", OnOffC()), ("invert", OnOffC()), ("hpon", OnOffC()), ("hpf", LogFreqC(20.0, 400.0))])
        add(f"{p}/gate", _gate_fields())
        add(f"{p}/gate/filter", _filter_fields())
        add(f"{p}/dyn", _dyn_fields(keysrc=True))
        add(f"{p}/dyn/filter", _filter_fields())
        add(f"{p}/insert", _insert_fields(XCHFXSLOT))
        add(f"{p}/eq", [("on", OnOffC())])
        for band in (1, 2, 3, 4):
            add(f"{p}/eq/{band}", _eq_band_fields())
        add(f"{p}/mix", [("on", OnOffC()), ("fader", LevelC()), ("lr", OnOffC()), ("pan", PanC())])
        for addr, fields in _sends_for(p, NUM_BUS + NUM_FX):
            add(addr, fields)
        add(f"{p}/grp", _grp_fields())
        add(f"{p}/automix", [("group", EnumC(XAMGROUP)), ("weight", LinC(-12.0, 12.0))])

    # ---- aux return ----
    add("/rtn/aux/config", [("name", StrC()), ("color", IntC()), ("rtnsrc", EnumC(["U1718"]))])
    add("/rtn/aux/preamp", [("rtntrim", LinC(-18.0, 18.0)), ("rtnsw", OnOffC())])
    add("/rtn/aux/eq", [("on", OnOffC())])
    for band in (1, 2, 3, 4):
        add(f"/rtn/aux/eq/{band}", _eq_band_fields())
    add("/rtn/aux/mix", [("on", OnOffC()), ("fader", LevelC()), ("lr", OnOffC()), ("pan", PanC())])
    for addr, fields in _sends_for("/rtn/aux", NUM_BUS + NUM_FX):
        add(addr, fields)
    add("/rtn/aux/grp", _grp_fields())

    # ---- fx returns 1-4 ----
    for rt in range(1, NUM_RTN + 1):
        p = f"/rtn/{rt}"
        add(f"{p}/config", [("name", StrC()), ("color", IntC()), ("rtnsrc", EnumC(XRTNRTNSRC))])
        add(f"{p}/preamp", [("rtntrim", LinC(-18.0, 18.0)), ("rtnsw", OnOffC())])
        add(f"{p}/eq", [("on", OnOffC())])
        for band in (1, 2, 3, 4):
            add(f"{p}/eq/{band}", _eq_band_fields())
        add(f"{p}/mix", [("on", OnOffC()), ("fader", LevelC()), ("lr", OnOffC()), ("pan", PanC())])
        for addr, fields in _sends_for(p, NUM_BUS + NUM_FX):
            add(addr, fields)
        add(f"{p}/grp", _grp_fields())

    # ---- buses ----
    for bus in range(1, NUM_BUS + 1):
        p = f"/bus/{bus}"
        add(f"{p}/config", [("name", StrC()), ("color", IntC())])
        add(f"{p}/dyn", _dyn_fields(keysrc=True))
        add(f"{p}/dyn/filter", _filter_fields())
        add(f"{p}/insert", _insert_fields(XCHFXSLOT))
        add(f"{p}/eq", [("on", OnOffC()), ("mode", EnumC(XEQMODE))])
        for band in range(1, 7):
            add(f"{p}/eq/{band}", _eq_band_fields())
        add(f"{p}/geq", _geq_fields())
        add(f"{p}/mix", [("on", OnOffC()), ("fader", LevelC()), ("lr", OnOffC()), ("pan", PanC())])
        add(f"{p}/grp", _grp_fields())

    # ---- fx sends ----
    for fs in range(1, NUM_FXSEND + 1):
        p = f"/fxsend/{fs}"
        add(f"{p}/config", [("name", StrC()), ("color", IntC())])
        add(f"{p}/mix", [("on", OnOffC()), ("fader", LevelC())])
        add(f"{p}/grp", _grp_fields())

    # ---- main LR ----
    add("/lr/config", [("name", StrC()), ("color", IntC())])
    add("/lr/dyn", _dyn_fields(keysrc=False))
    add("/lr/dyn/filter", _filter_fields())
    add("/lr/insert", _insert_fields(["OFF", "Fx1", "Fx2", "Fx3", "Fx4"]))
    add("/lr/eq", [("on", OnOffC()), ("mode", EnumC(XEQMODE))])
    for band in range(1, 7):
        add(f"/lr/eq/{band}", _eq_band_fields())
    add("/lr/geq", _geq_fields())
    add("/lr/mix", [("on", OnOffC()), ("fader", LevelC()), ("pan", PanC())])

    # ---- dca ----
    for dca in range(1, NUM_DCA + 1):
        add(f"/dca/{dca}", [("on", OnOffC()), ("fader", LevelC())])
        add(f"/dca/{dca}/config", [("name", StrC()), ("color", IntC())])

    # ---- fx slots (type/insert handled via schema; /fx/N/par is special-cased) ----
    for fx in range(1, NUM_FX + 1):
        add(f"/fx/{fx}", [("type", EnumC(XFXTYP4)), ("insert", OnOffC())])
        # /fx/{fx}/par is handled specially in loader.py (variable-length, raw passthrough)

    # ---- routing ----
    add("/routing/main/01", [("src", EnumC(XMAINSRC))])
    add("/routing/main/02", [("src", EnumC(XMAINSRC))])
    for i in range(1, NUM_AUX + 1):
        add(f"/routing/aux/{i:02d}", [("src", EnumC(XAUXSRC)), ("pos", EnumC(XSRCPOS))])
    for i in range(1, NUM_P16 + 1):
        add(f"/routing/p16/{i:02d}", [("src", EnumC(XAUXSRC)), ("pos", EnumC(XSRCPOS))])
    for i in range(1, NUM_USB + 1):
        add(f"/routing/usb/{i:02d}", [("src", EnumC(XUSBSRC)), ("pos", EnumC(XSRCPOS))])

    # ---- headamps ----
    for i in range(1, 17):
        add(f"/headamp/{i:02d}", [("gain", LinC(-12.0, 60.0)), ("phantom", OnOffC())])
    for i in range(17, 25):
        add(f"/headamp/{i:02d}", [("gain", LinC(-12.0, 32.0))])

    return schema


SCHEMA = build_schema()
