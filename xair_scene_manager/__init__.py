"""xair-scene-manager: copy, export, and import Behringer X-Air mixer scenes
between mixer snapshot slots and local .scn files."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("xair-scene-manager")
except PackageNotFoundError:
    __version__ = "0.0.0"
