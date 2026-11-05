"""Tests for import_scraper_data's name-based power/drivetrain inference,
on variant names exactly as the scraper stores them."""

import importlib.util
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "import_scraper_data_inference", Path(__file__).resolve().parents[1] / "import_scraper_data.py"
)
importer_module = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = importer_module
_SPEC.loader.exec_module(importer_module)

from app.models.enums import Drivetrain  # noqa: E402  (importable once the script put backend/ on sys.path)

extract_power_kw = importer_module.extract_power_kw
infer_drivetrain = importer_module.infer_drivetrain


@pytest.mark.parametrize(
    ("variant_name", "power_kw"),
    [
        # Battery capacity before power: must read the power, not the kWh.
        ("Junior Sport Speciale Elettrica 54 kWh 115 kW Elektřina automatická Přední", 115),
        ("e Vitara ELEGANCE 61 kWh 135 kW 4×4", 135),
        ("ID.3 Neo Pure 50 kWh 125 kW", 125),
        ("ID.4 Pro 140 kW, 58 kWh", 140),
        ("Avenger Longitude 1.2 Turbo 100k 74 kW Benzín 6st. manuální Přední", 74),
        ("Yaris 1.5 Hybrid 116k", None),
    ],
)
def test_extract_power_kw_skips_battery_capacity(variant_name: str, power_kw: int | None) -> None:
    assert extract_power_kw(variant_name) == power_kw


@pytest.mark.parametrize(
    ("variant_name", "drivetrain"),
    [
        ("Giulia Quadrifoglio 2.9 V6 BiTurbo 382 kW Benzín 8st. automatická Q2 (RWD)", Drivetrain.rwd),
        ("Giulia Sprint 2.2 JTDm RWD 118 kW Diesel 8st. automatická Zadní (RWD)", Drivetrain.rwd),
        ("Giulia Sprint 2.2 JTDm Q4 154 kW Diesel 8st. automatická Q4 (AWD)", Drivetrain.awd),
        (
            "Tonale Sprint 1.3 Turbo PHEV 197 kW benzín/elektřina 6st. automatická Pohon všech kol Alfa™ eQ4",
            Drivetrain.awd,
        ),
        ("Avenger Upland 1.2 Turbo e-Hybrid 145k 4xe 107 kW Benzín 6st. automatická e-AWD", Drivetrain.awd),
        ("Wrangler Sahara 2.0 Turbo Sahara 200 kW Benzín 8st. automatická 4WD", Drivetrain.awd),
        ("Avenger Altitude Electric 54 kWh 115 kW Elektřina automatická FWD (přední)", Drivetrain.fwd),
    ],
)
def test_infer_drivetrain_reads_stellantis_drive_column(variant_name: str, drivetrain: Drivetrain) -> None:
    assert infer_drivetrain(variant_name) == drivetrain
