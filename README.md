# X-Air Scene Manager

Python tool to copy, export, and import X-Air mixer scenes between mixer scene snapshots and to and from local files.

## Requirements

Python 3.11 or newer. No external dependencies (pure standard library).

Talks to the mixer over its OSC control port (UDP 10024 by default,
override with `-p/--port`) on the local network, so the machine running
this tool needs network access to the mixer.

## Installation

Install the `xair-scene-manager` command from PyPI:

```sh
pip install xair-scene-manager
```

Alternatively, run it straight from a checkout without installing anything:

```sh
./xair-scene-manager ...
# or
python3 xair-scene-manager ...
```

## Usage

### Load current configuration from snapshot

Loads the data in the snapshot (index or name) into the mixer.

```sh
xair-scene-manager -x <ip-or-hostname> load-snapshot <snapshot>
```

### Load current configuration from file

Loads the configuration from the named file.

```sh
xair-scene-manager -x <ip-or-hostname> load-file <filename>
```


### Save current configuration to snapshot

Saves the current mixer setup into the snapshot numbered and named as given.

```sh
xair-scene-manager -x <ip-or-hostname> save-snapshot <snapshot-index> [snapshot-name]
```

### Save current configuration to snapshot

Saves the current mixer setup into the named file.

```sh
xair-scene-manager -x <ip-or-hostname> save-file <filename>
```

Snapshots can be given by index (1-64) or by name; a name is resolved by
scanning the mixer's snapshot list, which takes a moment on a slow link.

## File Format

The file format for scenes is compatible with the `.scn` file format as used by X-Air Edit,
and matches what the classic `XAirGetScene`/`XAirSetScene` community tools produce: one line
per mixer "node" (e.g. `/ch/01/mix   ON   -oo ON +0`), covering channels, buses, returns, FX
sends, main LR, DCAs, FX slots, routing and headamp trim, for the 16-channel/6-bus/4-FX/4-DCA
layout of the XR18/MR18 (the layout used by `sample-scene.scn`). Other X-Air models
(XR12, XR16) have a different channel/bus count and aren't covered by this tool's node table.

Saving reads each node back from the mixer using its own text formatting (via the `/node`
command), so the exact spacing may differ slightly from an X-Air Edit export, but the values
and the file are fully interchangeable with it.

FX effect parameters (`/fx/N/par`) are effect-type-specific and not documented anywhere
public; they're carried through as raw values rather than decoded/encoded like everything
else, so round-tripping them is best-effort.
