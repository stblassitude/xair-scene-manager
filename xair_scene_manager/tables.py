"""Enumeration tables for X-Air (XR12/XR16/XR18/MR18) OSC parameters.

Values and orderings are taken from XAirSetScene.h, part of the
Patrick-Gilles Maillot / Ken Mitchell X32-Behringer toolkit
(https://github.com/pmaillot/X32-Behringer), which is the reference C
implementation of the XAirGetScene/XAirSetScene .scn dialect this tool
speaks. Where that header disagreed with the community OSC wiki (e.g. gate
mode ordering), the header was trusted since it's what actually produced
this file format.
"""

XSOURCE = [
    "OFF", "LR", "LRPFL", "LRAFL", "AUX", "U1718",
    "Bus1", "Bus2", "Bus3", "Bus4", "Bus5", "Bus6",
    "Bus12", "Bus34", "Bus56",
]

XGATEMODE = ["GATE", "EXP2", "EXP3", "EXP4", "DUCK"]

XFILTERTYPE = ["LC6", "LC12", "HC6", "HC12", "1.0", "2.0", "3.0", "5.0", "10.0"]

XDYNRATIO = ["1.1", "1.3", "1.5", "2.0", "2.5", "3.0", "4.0", "5.0", "7.0", "10", "20", "100"]

XINSRC = [f"In{i:02d}" for i in range(1, 17)] + ["OFF"]

XCHRTNSRC = [f"U{i:02d}" for i in range(1, 19)]

XRTNRTNSRC = ["U0102", "U0304", "U0506", "U0708", "U0910", "U1112", "U1314", "U1516", "U1718"]

XKEYSRC = ["SELF"] + [f"Ch{i:02d}" for i in range(1, 17)] + [f"Bus{i}" for i in range(1, 7)]

XMAINSRC = ["LR", "MON", "U0102", "U0304", "U0506", "U0708", "U0910", "U1112", "U1314", "U1516", "U1718"]

_AUX_USB_COMMON = (
    [f"Ch{i:02d}" for i in range(1, 17)]
    + ["AuxL", "AuxR"]
    + [f"Fx{n}{ch}" for n in range(1, 5) for ch in "LR"]
    + [f"Bus{i}" for i in range(1, 7)]
    + [f"Send{i}" for i in range(1, 5)]
    + ["L", "R"]
)
XAUXSRC = _AUX_USB_COMMON + [f"U{i:02d}" for i in range(1, 19)]
XUSBSRC = list(_AUX_USB_COMMON)

XSRCPOS = ["AIN", "AIN+M", "IN", "IN+M", "PREEQ", "PREEQ+M", "POSTEQ", "POSTEQ+M", "PRE", "PRE+M", "POST"]

XCHFXSLOT = ["OFF", "Fx1A", "Fx1B", "Fx2A", "Fx2B", "Fx3A", "Fx3B", "Fx4A", "Fx4B"]

XLRFXSLOT = ["OFF", "Fx1", "Fx2", "Fx3", "Fx4"]

XMXTAP = ["IN", "PREEQ", "POSTEQ", "PRE", "POST", "GRP"]

XAMGROUP = ["OFF", "X", "Y"]

XEQMODE = ["PEQ", "GEQ", "TEQ"]

XEQTYP = ["LCut", "LShv", "PEQ", "VEQ", "HShv", "HCut"]

XDET = ["PEAK", "RMS"]

XENV = ["LIN", "LOG"]

XDYNMODE = ["COMP", "EXP"]

XFXTYP4 = [
    "HALL", "AMBI", "RPLT", "ROOM", "CHAM", "PLAT", "VREV", "VRM",
    "GATE", "RVRS", "DLY", "3TAP", "4TAP", "CRS", "FLNG", "PHAS", "DIMC", "FILT",
    "ROTA", "PAN", "SUB", "D/RV", "CR/R", "FL/R", "D/CR", "D/FL", "MODD", "GEQ2",
    "GEQ", "TEQ2", "TEQ", "DES2", "DES", "P1A", "P1A2", "PQ5", "PQ5S", "WAVD",
    "LIM", "CMB", "CMB2", "FAC", "FAC1M", "FAC2", "LEC", "LEC2", "ULC", "ULC2",
    "ENH2", "ENH", "EXC2", "EXC", "IMG", "EDI", "SON", "AMP2", "AMP", "DRV2",
    "DRV", "PIT2", "PIT",
]

# 31-band graphic EQ, in order, mapping to /.../geq/<suffix>
GEQ_BANDS = [
    "20", "25", "31.5", "40", "50", "63", "80", "100", "125",
    "160", "200", "250", "315", "400", "500", "630", "800", "1k",
    "1k25", "1k6", "2k", "2k5", "3k15", "4k", "5k", "6k3", "8k",
    "10k", "12k5", "16k", "20k",
]
