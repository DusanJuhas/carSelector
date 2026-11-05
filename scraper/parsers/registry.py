"""Maps `parser_key` (from config/sources.yaml) to a parser class.

A new parser = a new entry here + a file in this directory, nothing else
in main.py needs to change.
"""

from __future__ import annotations

from .alfa_romeo import AlfaRomeoParser
from .audi import AudiParser
from .base import BaseParser
from .bmw import BmwParser
from .citroen import CitroenParser
from .cupra import CupraParser
from .dacia import DaciaParser
from .fiat import FiatParser
from .ford import FordParser
from .honda import HondaParser
from .hyundai import HyundaiParser
from .jeep import JeepParser
from .kgm import KgmParser
from .kia import KiaParser
from .lexus import LexusParser
from .mazda import MazdaParser
from .mercedes_benz import MercedesBenzParser
from .mg import MgParser
from .mitsubishi import MitsubishiParser
from .nissan import NissanParser
from .opel import OpelParser
from .peugeot import PeugeotParser
from .renault import RenaultParser
from .seat import SeatParser
from .skoda_ev import SkodaEvParser
from .skoda_ice import SkodaIceParser
from .subaru import SubaruParser
from .suzuki import SuzukiParser
from .tesla import TeslaParser
from .toyota import ToyotaParser
from .volkswagen import VolkswagenParser
from .volkswagen_ev import VolkswagenEvParser
from .volvo import VolvoParser

PARSERS: dict[str, type[BaseParser]] = {
    "skoda_ice": SkodaIceParser,
    "skoda_ev": SkodaEvParser,
    "volkswagen": VolkswagenParser,
    "volkswagen_ev": VolkswagenEvParser,
    "kia": KiaParser,
    "toyota": ToyotaParser,
    "hyundai": HyundaiParser,
    "mercedes-benz": MercedesBenzParser,
    "mazda": MazdaParser,
    "bmw": BmwParser,
    "dacia": DaciaParser,
    "ford": FordParser,
    "cupra": CupraParser,
    "renault": RenaultParser,
    "opel": OpelParser,
    "peugeot": PeugeotParser,
    "mg": MgParser,
    "audi": AudiParser,
    "tesla": TeslaParser,
    "seat": SeatParser,
    "volvo": VolvoParser,
    "mitsubishi": MitsubishiParser,
    "citroen": CitroenParser,
    "suzuki": SuzukiParser,
    "nissan": NissanParser,
    "honda": HondaParser,
    "fiat": FiatParser,
    "subaru": SubaruParser,
    "lexus": LexusParser,
    "jeep": JeepParser,
    "alfa-romeo": AlfaRomeoParser,
    "kgm": KgmParser,
}
