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


drivetrain_text = importer_module.drivetrain_text


@pytest.mark.parametrize(
    ("variant_name", "raw_text", "drivetrain"),
    [
        # Škoda prints the drivetrain only in the row's "Pohon" column, never
        # in variant_name - raw_text is that one row, as the parser stores it.
        (
            "Kodiaq 2,0 TDI/142 kW Laurin & Klement",
            "2,0 TDI/142 kW | Nafta 7stupňová automatická DSG 4×4 1 215 000 1 315 000 1 480 000 1 340 000 –",
            Drivetrain.awd,
        ),
        (
            "Kodiaq 2,0 TDI/110 kW Selection",
            "2,0 TDI/110 kW | Nafta 7stupňová automatická DSG přední 1 070 000 1 170 000 1 335 000 1 195 000 –",
            Drivetrain.fwd,
        ),
        ("Elroq 85 210 kW 77 kWh Selection", "85 210 kW 77 kWh | zadní 560-583 km 1 139 000", Drivetrain.rwd),
    ],
)
def test_infer_drivetrain_reads_skoda_pohon_column_from_raw_text(
    variant_name: str, raw_text: str, drivetrain: Drivetrain
) -> None:
    assert infer_drivetrain(variant_name) == Drivetrain.fwd  # the name alone says nothing
    assert infer_drivetrain(drivetrain_text("skoda", variant_name, raw_text)) == drivetrain


def test_drivetrain_text_ignores_raw_text_of_other_brands() -> None:
    # Lexus' raw_text carries the whole table header, other rows' "4X4"
    # included - it must not turn this FWD row into an AWD one.
    raw_text = "350h FWD 350h 4X4 E-FOUR SFX | COMFORT 1 440 000 Kč 1 490 000 Kč AK"
    assert infer_drivetrain(drivetrain_text("lexus", "NX COMFORT 350h FWD", raw_text)) == Drivetrain.fwd
    assert drivetrain_text("skoda", "Fabia 1,0 TSI/70 kW Selection", None) == "Fabia 1,0 TSI/70 kW Selection"


@pytest.mark.parametrize(
    ("brand", "variant_name", "raw_text", "drivetrain"),
    [
        # Volkswagen's "Pohon" column, left out of the name without "4MOTION"
        (
            "volkswagen",
            "Tiguan Elegance 2,0 TDI / 142 kW",
            "2,0 TDI / 142 kW CT1D7T02 Diesel 142/193 Aut. DSG7 Všech kol 1 190 909 Kč 1 441 000 Kč",
            Drivetrain.awd,
        ),
        (
            "volkswagen",
            "ID.3 Neo Trend 50 kWh 125 kW",
            "ID.3 Neo Trend 50 kWh 125 kW E132HBA2 Automatický Zadní 619 008 Kč 749 000 Kč",
            Drivetrain.rwd,
        ),
        # "4MOTION" in the name wins over a contradicting "Přední" cell
        (
            "volkswagen",
            "Passat Style 2,0 TSI 4MOTION / 150 kW",
            "2,0 TSI 4MOTION / 150 kW CJ5DMZ02 Benzin 150/204 Aut. DSG7 Přední 1 101 653 Kč 1 333 000 Kč",
            Drivetrain.awd,
        ),
        # BMW's parser drops "M xDrive" from the M4 Competition's name
        (
            "bmw",
            "4 Series Cabrio M4 Competition M 62993cm3 390/530kW",
            "M4 Competition M xDrive 6 2993 390/530 239 10,5 2 442 066 2 954 900",
            Drivetrain.awd,
        ),
    ],
)
def test_infer_drivetrain_reads_vw_and_bmw_row_from_raw_text(
    brand: str, variant_name: str, raw_text: str, drivetrain: Drivetrain
) -> None:
    assert infer_drivetrain(drivetrain_text(brand, variant_name, raw_text)) == drivetrain
