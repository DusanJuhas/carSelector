"""Maps `parser_key` (from config/sources.yaml) to a discoverer class.

A new discoverer = a new entry here + a file in this directory, nothing
else in source_monitor.py needs to change. Same pattern as
`parsers/registry.py`.
"""
from __future__ import annotations

from .base import BaseDiscoverer
from .skoda import SkodaDiscoverer
from .volkswagen import VolkswagenDiscoverer

DISCOVERERS: dict[str, type[BaseDiscoverer]] = {
    "skoda_ice": SkodaDiscoverer,
    "skoda_ev": SkodaDiscoverer,
    "volkswagen": VolkswagenDiscoverer,
    "volkswagen_ev": VolkswagenDiscoverer,
}
