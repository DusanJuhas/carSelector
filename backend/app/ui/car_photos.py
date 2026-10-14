"""Car photos shown on result cards, served as static files from
`storage/car_photos/` (see storage/README.md). A hand-picked set of freely licensed images
from Wikimedia Commons - the catalog itself has no image source (see
doc/api-contract.md's `thumbnail_url` note), so a model without an entry
here keeps the card's striped placeholder.

Every entry carries its attribution: Creative Commons licences (CC BY,
CC BY-SA) require showing the author, licence and source next to the
image, which `results_grid.car_card` does. Files are Commons' small
(~320px) thumbnails - enough for a 230px-wide card.
"""

from dataclasses import dataclass

from nicegui import app

from app.core.config import CAR_PHOTOS_DIR as PHOTOS_DIR

PHOTOS_URL = "/car-photos"


@dataclass(frozen=True)
class CarPhoto:
    """One photo and its attribution.

    Attributes:
        file: File name inside `PHOTOS_DIR`.
        author: Author as named on the Commons file page.
        license: Short licence name, e.g. "CC0" or "CC BY-SA 4.0".
        source_url: The Commons file page (author, licence, original).
    """

    file: str
    author: str
    license: str
    source_url: str

    @property
    def url(self) -> str:
        """The URL the browser loads the image from."""
        return f"{PHOTOS_URL}/{self.file}"


# Keyed by the catalog's exact (brand, model) names.
CAR_PHOTOS: dict[tuple[str, str], CarPhoto] = {
    ("Audi", "A3 Limuzína"): CarPhoto(
        file="audi-a3-limuzina.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Audi_A3_8Y_Sedan_IMG_1019.jpg",
    ),
    ("Audi", "Q5"): CarPhoto(
        file="audi-q5.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q5_FY_50_TFSI_e_Facelift_IMG_5284.jpg",
    ),
    ("BMW", "3 Series Sedan"): CarPhoto(
        file="bmw-3-series-sedan.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G20_(2022)_IMG_7316.jpg",
    ),
    ("BMW", "X1"): CarPhoto(
        file="bmw-x1.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_U11_1X7A6826.jpg",
    ),
    ("CUPRA", "Formentor"): CarPhoto(
        file="cupra-formentor.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Cupra_Formentor_VZ5_1X7A7000.jpg",
    ),
    ("Dacia", "Duster"): CarPhoto(
        file="dacia-duster.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Dacia_Duster_III_IMG_8961.jpg",
    ),
    ("Dacia", "Sandero"): CarPhoto(
        file="dacia-sandero.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Dacia_Sandero_III_1X7A6451.jpg",
    ),
    ("Ford", "Puma"): CarPhoto(
        file="ford-puma.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Ford_Puma_(2019)_IMG_9475.jpg",
    ),
    ("Hyundai", "i30"): CarPhoto(
        file="hyundai-i30.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Hyundai_i30_(PD)_DSC_8543.jpg",
    ),
    ("Hyundai", "Tucson"): CarPhoto(
        file="hyundai-tucson.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Hyundai_Tucson_(NX4)_1X7A0424.jpg",
    ),
    ("Kia", "Niro"): CarPhoto(
        file="kia-niro.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Kia_Niro_(SG2)_PHEV_1X7A6014.jpg",
    ),
    ("Kia", "Sportage"): CarPhoto(
        file="kia-sportage.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Kia_Sportage_(NQ5)_1X7A0326.jpg",
    ),
    ("Mazda", "3"): CarPhoto(
        file="mazda-3.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Mazda3_(BP)_1X7A7264.jpg",
    ),
    ("Mazda", "CX-5"): CarPhoto(
        file="mazda-cx-5.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Mazda_CX-5_(KF)_Facelift_1X7A0331_(2).jpg",
    ),
    ("MG", "ZS"): CarPhoto(
        file="mg-zs.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:MG_ZS_Facelift_1X7A6412.jpg",
    ),
    ("Opel", "Corsa"): CarPhoto(
        file="opel-corsa.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Opel_Corsa_F_IMG_5815.jpg",
    ),
    ("Peugeot", "208"): CarPhoto(
        file="peugeot-208.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2020_Peugeot_208_GT_Line_PureTech_1.2_Front.jpg",
    ),
    ("Renault", "Clio"): CarPhoto(
        file="renault-clio.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_Clio_V_1X7A0393.jpg",
    ),
    ("Škoda", "Elroq"): CarPhoto(
        file="skoda-elroq.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Škoda_Elroq_DSC_9260.jpg",
    ),
    ("Škoda", "Enyaq"): CarPhoto(
        file="skoda-enyaq.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Skoda_Enyaq_Sportline_1X7A0316.jpg",
    ),
    ("Škoda", "Fabia"): CarPhoto(
        file="skoda-fabia.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Skoda_Fabia_IV_1X7A6155.jpg",
    ),
    ("Škoda", "Kodiaq"): CarPhoto(
        file="skoda-kodiaq.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Škoda_Kodiaq_II_IMG_9433.jpg",
    ),
    ("Škoda", "Octavia"): CarPhoto(
        file="skoda-octavia.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Skoda_Octavia_IV_Combi_RS_1X7A0352.jpg",
    ),
    ("Tesla", "Model Y"): CarPhoto(
        file="tesla-model-y.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Tesla_Model_Y_1X7A6211.jpg",
    ),
    ("Toyota", "RAV4"): CarPhoto(
        file="toyota-rav4.jpg",
        author="TTTNIS",
        license="CC0",
        source_url="https://commons.wikimedia.org/wiki/File:2021_Toyota_RAV4_PHV.jpg",
    ),
    ("Toyota", "Yaris"): CarPhoto(
        file="toyota-yaris.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Toyota_Yaris_Hybrid_(XP210)_1X7A0353.jpg",
    ),
    ("Volkswagen", "Golf"): CarPhoto(
        file="volkswagen-golf.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volkswagen_Golf_VIII_GTI_Clubsport_45_IMG_4884.jpg",
    ),
    ("Volkswagen", "ID.4"): CarPhoto(
        file="volkswagen-id-4.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volkswagen_ID.4_GTX_1X7A0301.jpg",
    ),
    ("Volkswagen", "Tiguan"): CarPhoto(
        file="volkswagen-tiguan.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volkswagen_Tiguan_III_IMG_8388.jpg",
    ),
}


def photo_for(brand: str, model: str) -> CarPhoto | None:
    """Looks up a model's photo.

    Args:
        brand: Catalog brand name, e.g. "Toyota".
        model: Catalog model name, e.g. "RAV4".

    Returns:
        The photo, or `None` if the model has none (the card shows a
        placeholder).
    """
    return CAR_PHOTOS.get((brand, model))


def register_car_photos() -> None:
    """Serves `PHOTOS_DIR` at `PHOTOS_URL`. Called once at startup (see
    `app/main.py`)."""
    app.add_static_files(PHOTOS_URL, PHOTOS_DIR)
