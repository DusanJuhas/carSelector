"""Maps `parser_key` (from config/sources.yaml) to a discoverer class.

A new discoverer = a new entry here + a file in this directory, nothing
else in source_monitor.py needs to change. Same pattern as
`parsers/registry.py`.
"""

from __future__ import annotations

from .alfa_romeo import AlfaRomeoDiscoverer
from .audi import AudiDiscoverer
from .base import BaseDiscoverer
from .bmw import BmwDiscoverer
from .citroen import CitroenDiscoverer
from .cupra import CupraDiscoverer
from .dacia import DaciaDiscoverer
from .fiat import FiatDiscoverer
from .ford import FordDiscoverer
from .honda import HondaDiscoverer
from .hyundai import HyundaiDiscoverer
from .jeep import JeepDiscoverer
from .kgm import KgmDiscoverer
from .kia import KiaDiscoverer
from .lexus import LexusDiscoverer
from .mazda import MazdaDiscoverer
from .mercedes_benz import MercedesBenzDiscoverer
from .mg import MgDiscoverer
from .mitsubishi import MitsubishiDiscoverer
from .nissan import NissanDiscoverer
from .opel import OpelDiscoverer
from .peugeot import PeugeotDiscoverer
from .renault import RenaultDiscoverer
from .seat import SeatDiscoverer
from .skoda import SkodaDiscoverer
from .subaru import SubaruDiscoverer
from .suzuki import SuzukiDiscoverer
from .tesla import TeslaDiscoverer
from .toyota import ToyotaDiscoverer
from .volkswagen import VolkswagenDiscoverer
from .volvo import VolvoDiscoverer

DISCOVERERS: dict[str, type[BaseDiscoverer]] = {
    "skoda_ice": SkodaDiscoverer,
    "skoda_ev": SkodaDiscoverer,
    "volkswagen": VolkswagenDiscoverer,
    "volkswagen_ev": VolkswagenDiscoverer,
    "kia": KiaDiscoverer,
    "toyota": ToyotaDiscoverer,
    "hyundai": HyundaiDiscoverer,
    "mercedes-benz": MercedesBenzDiscoverer,
    "mazda": MazdaDiscoverer,
    "bmw": BmwDiscoverer,
    "dacia": DaciaDiscoverer,
    "ford": FordDiscoverer,
    "cupra": CupraDiscoverer,
    "renault": RenaultDiscoverer,
    "opel": OpelDiscoverer,
    "peugeot": PeugeotDiscoverer,
    "mg": MgDiscoverer,
    "audi": AudiDiscoverer,
    "tesla": TeslaDiscoverer,
    "seat": SeatDiscoverer,
    "volvo": VolvoDiscoverer,
    "mitsubishi": MitsubishiDiscoverer,
    "citroen": CitroenDiscoverer,
    "suzuki": SuzukiDiscoverer,
    "nissan": NissanDiscoverer,
    "honda": HondaDiscoverer,
    "fiat": FiatDiscoverer,
    "subaru": SubaruDiscoverer,
    "lexus": LexusDiscoverer,
    "jeep": JeepDiscoverer,
    "alfa-romeo": AlfaRomeoDiscoverer,
    "kgm": KgmDiscoverer,
}
