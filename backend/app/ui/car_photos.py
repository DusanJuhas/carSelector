"""Car photos shown on result cards, served as static files from
`storage/car_photos/` (see storage/README.md). A hand-picked set of freely licensed images
from Wikimedia Commons - the catalog itself has no image source (see
doc/api-contract.md's `thumbnail_url` note), so a model without an entry
here keeps the card's striped placeholder.

Every entry carries its attribution: Creative Commons licences (CC BY,
CC BY-SA) require showing the author, licence and source next to the
image, which `results_grid.car_card` does. Files are Commons' small
(~320px) thumbnails - enough for a 230px-wide card.

Most entries were found via the model's English Wikipedia lead image
(usually the current generation) and every one was checked by eye. Body
or performance variants without a free photo of their own share their
base model's file (e.g. "A6 Avant e-tron" / "A6 Sportback e-tron", "S5"
/ "RS 5" show the A5). A model sold as a rebadged twin is left on the
placeholder rather than shown with the twin's badge (Mitsubishi Grandis
= Renault Symbioz; Fiat Qubo L; MG S9 PHEV) - Commons had no correctly
badged free photo of those as of 2026-11-02.
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
    ("Audi", "A2 e-tron"): CarPhoto(
        file="audi-a2-e-tron.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A2_e-tron_IMG_20261009.jpg",
    ),
    ("Audi", "A3 Limuzína"): CarPhoto(
        file="audi-a3-limuzina.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Audi_A3_8Y_Sedan_IMG_1019.jpg",
    ),
    ("Audi", "A3 Sportback"): CarPhoto(
        file="audi-a3-sportback.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A3_8Y_Sedan_IMG_5936.jpg",
    ),
    ("Audi", "A3 allstreet"): CarPhoto(
        file="audi-a3-sportback.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A3_8Y_Sedan_IMG_5936.jpg",
    ),
    ("Audi", "A5 Avant"): CarPhoto(
        file="audi-a5-avant.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A5_B10_DSC_7314.jpg",
    ),
    ("Audi", "A5 Limuzína"): CarPhoto(
        file="audi-a5-avant.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A5_B10_DSC_7314.jpg",
    ),
    ("Audi", "A6 Avant"): CarPhoto(
        file="audi-a6-avant.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A6_C9_IAA_2025_DSC_1920.jpg",
    ),
    ("Audi", "A6 Avant e-tron"): CarPhoto(
        file="audi-a6-avant-e-tron.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A6_Avant_e-tron_–_f_18042025.jpg",
    ),
    ("Audi", "A6 Limuzína"): CarPhoto(
        file="audi-a6-avant.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A6_C9_IAA_2025_DSC_1920.jpg",
    ),
    ("Audi", "A6 Sportback e-tron"): CarPhoto(
        file="audi-a6-avant-e-tron.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A6_Avant_e-tron_–_f_18042025.jpg",
    ),
    ("Audi", "A6 allroad"): CarPhoto(
        file="audi-a6-avant.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A6_C9_IAA_2025_DSC_1920.jpg",
    ),
    ("Audi", "Q3"): CarPhoto(
        file="audi-q3.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q3_F3_DSC_7494.jpg",
    ),
    ("Audi", "Q3 Sportback"): CarPhoto(
        file="audi-q3.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q3_F3_DSC_7494.jpg",
    ),
    ("Audi", "Q4 Sportback e-tron"): CarPhoto(
        file="audi-q4-sportback-e-tron.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2021_Audi_Q4_e-tron_Sport_35.jpg",
    ),
    ("Audi", "Q4 e-tron"): CarPhoto(
        file="audi-q4-sportback-e-tron.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2021_Audi_Q4_e-tron_Sport_35.jpg",
    ),
    ("Audi", "Q5"): CarPhoto(
        file="audi-q5.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q5_FY_50_TFSI_e_Facelift_IMG_5284.jpg",
    ),
    ("Audi", "Q5 Sportback"): CarPhoto(
        file="audi-q5-sportback.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q5_2.0_TDI_quattro_S_line_(GU)_–_f_13102025.jpg",
    ),
    ("Audi", "Q6 Sportback e-tron"): CarPhoto(
        file="audi-q6-sportback-e-tron.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q6_e-tron_DSC_7829.jpg",
    ),
    ("Audi", "Q6 e-tron"): CarPhoto(
        file="audi-q6-sportback-e-tron.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q6_e-tron_DSC_7829.jpg",
    ),
    ("Audi", "Q7 SUV"): CarPhoto(
        file="audi-q7-suv.jpg",
        author="Ethan Llamas",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q7_4M_FL2_3.0_V6_MHEV_quattro_Satellite_Silver_Metallic_01_(cropped).jpg",
    ),
    ("Audi", "Q8 SUV"): CarPhoto(
        file="audi-q8-suv.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_Audi_Q8_S_Line_50_TDi_Quattro_3.0_Front.jpg",
    ),
    ("Audi", "Q9 SUV"): CarPhoto(
        file="audi-q9-suv.jpg",
        author="Autowizja",
        license="CC BY 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2026_Audi_Q9_right_front_-_Autowizja_(cropped)_(cropped).jpg",
    ),
    ("Audi", "RS 5 Avant"): CarPhoto(
        file="audi-a5-avant.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A5_B10_DSC_7314.jpg",
    ),
    ("Audi", "RS 5 Limuzína"): CarPhoto(
        file="audi-a5-avant.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A5_B10_DSC_7314.jpg",
    ),
    ("Audi", "RS Q8 SUV"): CarPhoto(
        file="audi-q8-suv.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_Audi_Q8_S_Line_50_TDi_Quattro_3.0_Front.jpg",
    ),
    ("Audi", "RS e-tron GT"): CarPhoto(
        file="audi-rs-e-tron-gt.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_e-tron_GT_IMG_5689.jpg",
    ),
    ("Audi", "RS e-tron GT performance"): CarPhoto(
        file="audi-rs-e-tron-gt.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_e-tron_GT_IMG_5689.jpg",
    ),
    ("Audi", "RS3 Limuzína"): CarPhoto(
        file="audi-a3-sportback.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A3_8Y_Sedan_IMG_5936.jpg",
    ),
    ("Audi", "RS3 Sportback"): CarPhoto(
        file="audi-a3-sportback.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A3_8Y_Sedan_IMG_5936.jpg",
    ),
    ("Audi", "S e-tron GT"): CarPhoto(
        file="audi-rs-e-tron-gt.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_e-tron_GT_IMG_5689.jpg",
    ),
    ("Audi", "S3 Limuzína"): CarPhoto(
        file="audi-a3-sportback.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A3_8Y_Sedan_IMG_5936.jpg",
    ),
    ("Audi", "S3 Sportback"): CarPhoto(
        file="audi-a3-sportback.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A3_8Y_Sedan_IMG_5936.jpg",
    ),
    ("Audi", "S5 Avant"): CarPhoto(
        file="audi-a5-avant.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A5_B10_DSC_7314.jpg",
    ),
    ("Audi", "S5 Limuzína"): CarPhoto(
        file="audi-a5-avant.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_A5_B10_DSC_7314.jpg",
    ),
    ("Audi", "S6 Avant"): CarPhoto(
        file="audi-s6-avant.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_S6_Avant_C8_IMG_4309.jpg",
    ),
    ("Audi", "S6 Sportback"): CarPhoto(
        file="audi-s6-avant.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_S6_Avant_C8_IMG_4309.jpg",
    ),
    ("Audi", "SQ5"): CarPhoto(
        file="audi-q5-sportback.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q5_2.0_TDI_quattro_S_line_(GU)_–_f_13102025.jpg",
    ),
    ("Audi", "SQ5 Sportback"): CarPhoto(
        file="audi-q5-sportback.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q5_2.0_TDI_quattro_S_line_(GU)_–_f_13102025.jpg",
    ),
    ("Audi", "SQ6 e-tron"): CarPhoto(
        file="audi-q6-sportback-e-tron.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q6_e-tron_DSC_7829.jpg",
    ),
    ("Audi", "SQ6 e-tron Sportback"): CarPhoto(
        file="audi-q6-sportback-e-tron.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_Q6_e-tron_DSC_7829.jpg",
    ),
    ("Audi", "SQ8 SUV"): CarPhoto(
        file="audi-q8-suv.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_Audi_Q8_S_Line_50_TDi_Quattro_3.0_Front.jpg",
    ),
    ("Audi", "e-tron GT"): CarPhoto(
        file="audi-rs-e-tron-gt.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Audi_e-tron_GT_IMG_5689.jpg",
    ),
    ("BMW", "1 Series"): CarPhoto(
        file="bmw-1-series.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_120_(F70)_Leonberg_2024_IMG_1068.jpg",
    ),
    ("BMW", "2 Series Active Tourer"): CarPhoto(
        file="bmw-2-series-active-tourer.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2022_BMW_220i_Active_Tourer_Luxury_MHEV_Automatic_1.5_Front.jpg",
    ),
    ("BMW", "2 Series Coupé"): CarPhoto(
        file="bmw-2-series-coupe.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G42_1X7A0370.jpg",
    ),
    ("BMW", "2 Series Gran Coupé"): CarPhoto(
        file="bmw-2-series-gran-coupe.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_F44_1X7A6109.jpg",
    ),
    ("BMW", "3 Series Sedan"): CarPhoto(
        file="bmw-3-series-sedan.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G20_(2022)_IMG_7316.jpg",
    ),
    ("BMW", "3 Series Touring"): CarPhoto(
        file="bmw-3-series-touring.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2019_BMW_318d_SE_Automatic_2.0_Front.jpg",
    ),
    ("BMW", "4 Series Cabrio"): CarPhoto(
        file="bmw-4-series-cabrio.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2020_BMW_420i_Sport_Automatic_2.0.jpg",
    ),
    ("BMW", "4 Series Coupé"): CarPhoto(
        file="bmw-4-series-cabrio.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2020_BMW_420i_Sport_Automatic_2.0.jpg",
    ),
    ("BMW", "4 Series Gran Coupé"): CarPhoto(
        file="bmw-4-series-gran-coupe.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2021_BMW_420i_M_Sport_Automatic_2.0.jpg",
    ),
    ("BMW", "5 Series Sedan"): CarPhoto(
        file="bmw-5-series-sedan.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G60_520i_1X7A2443.jpg",
    ),
    ("BMW", "5 Series Touring"): CarPhoto(
        file="bmw-5-series-sedan.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G60_520i_1X7A2443.jpg",
    ),
    ("BMW", "7 Series"): CarPhoto(
        file="bmw-7-series.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_7-Series_(G70)_750e_IMG_9358.jpg",
    ),
    ("BMW", "M2 Coupé"): CarPhoto(
        file="bmw-m2-coupe.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G87_M2_1X7A1838.jpg",
    ),
    ("BMW", "X1"): CarPhoto(
        file="bmw-x1.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_U11_1X7A6826.jpg",
    ),
    ("BMW", "X2"): CarPhoto(
        file="bmw-x2.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_U10_1X7A2456.jpg",
    ),
    ("BMW", "X3"): CarPhoto(
        file="bmw-x3.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G45_20_DSC_7119.jpg",
    ),
    ("BMW", "X5"): CarPhoto(
        file="bmw-x5.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G05_45e_IMG_3714.jpg",
    ),
    ("BMW", "X6"): CarPhoto(
        file="bmw-x6.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G06_IMG_3142.jpg",
    ),
    ("BMW", "X7"): CarPhoto(
        file="bmw-x7.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G07_1X7A1696.jpg",
    ),
    ("BMW", "XM"): CarPhoto(
        file="bmw-xm.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_XM_(G09)_IMG_7778.jpg",
    ),
    ("BMW", "i3 Sedan"): CarPhoto(
        file="bmw-i3-sedan.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_i3_50_xDrive_First_Edition_(NA0)_–_f2_20082026.jpg",
    ),
    ("BMW", "i4 Gran Coupé"): CarPhoto(
        file="bmw-i4-gran-coupe.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_i4_IMG_6695.jpg",
    ),
    ("BMW", "i5 Sedan"): CarPhoto(
        file="bmw-5-series-sedan.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G60_520i_1X7A2443.jpg",
    ),
    ("BMW", "i5 Touring"): CarPhoto(
        file="bmw-5-series-sedan.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_G60_520i_1X7A2443.jpg",
    ),
    ("BMW", "i7"): CarPhoto(
        file="bmw-7-series.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_7-Series_(G70)_750e_IMG_9358.jpg",
    ),
    ("BMW", "iX"): CarPhoto(
        file="bmw-ix.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_iX_IAA_2021_1X7A0204.jpg",
    ),
    ("BMW", "iX1"): CarPhoto(
        file="bmw-ix1.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2022_BMW_X1_sDrive18d_M_Sport_MHEV_Automatic_2.0.jpg",
    ),
    ("BMW", "iX2"): CarPhoto(
        file="bmw-x2.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_U10_1X7A2456.jpg",
    ),
    ("BMW", "iX3"): CarPhoto(
        file="bmw-ix3.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:BMW_iX3_50_xDrive_M_Sportpaket_Pro_(NA5)_–_f_17052026.jpg",
    ),
    ("CUPRA", "Born"): CarPhoto(
        file="cupra-born.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Cupra_Born_–_f_03042026.jpg",
    ),
    ("CUPRA", "Formentor"): CarPhoto(
        file="cupra-formentor.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Cupra_Formentor_VZ5_1X7A7000.jpg",
    ),
    ("CUPRA", "Leon"): CarPhoto(
        file="cupra-leon.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Cupra_Leon_Mk4_Facelift_IMG_0392.jpg",
    ),
    ("CUPRA", "Leon Sportstourer"): CarPhoto(
        file="cupra-leon-sportstourer.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Cupra_Leon_Mk4_ST_Facelift_DSC_7065.jpg",
    ),
    ("CUPRA", "Raval"): CarPhoto(
        file="cupra-raval.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Cupra_Raval_VZ_IMG_6967_(cropped).jpg",
    ),
    ("CUPRA", "Terramar"): CarPhoto(
        file="cupra-terramar.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Cupra_Terramar_VZ_DSC_8241.jpg",
    ),
    ("Citroën", "Berlingo"): CarPhoto(
        file="citroen-berlingo.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Citroën_Berlingo_XL_BlueHDi_130_EAT8_Shine_XTR_(III)_–_f_02012021.jpg",
    ),
    ("Citroën", "Berlingo XL"): CarPhoto(
        file="citroen-berlingo.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Citroën_Berlingo_XL_BlueHDi_130_EAT8_Shine_XTR_(III)_–_f_02012021.jpg",
    ),
    ("Citroën", "C3"): CarPhoto(
        file="citroen-c3.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Citroën_C3_Hybrid_110_ë-DSC6_Max_(IV)_–_f_05042026.jpg",
    ),
    ("Citroën", "C3 Aircross"): CarPhoto(
        file="citroen-c3-aircross.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Citroën_ë-C3_Aircross_IMG_3525.jpg",
    ),
    ("Citroën", "C4"): CarPhoto(
        file="citroen-c4.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Citroen_C4_(2020)_1X7A5851.jpg",
    ),
    ("Citroën", "C4 X"): CarPhoto(
        file="citroen-c4-x.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Citroën_e-C4_X_Automesse_Ludwigsburg_2023_1X7A0016.jpg",
    ),
    ("Citroën", "C5 Aircross"): CarPhoto(
        file="citroen-c5-aircross.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2022_Citroën_C5_Aircross_Automesse_Ludwigsburg_2024_IMG_1342.jpg",
    ),
    ("Dacia", "Bigster"): CarPhoto(
        file="dacia-bigster.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Dacia_Bigster_DSC_8686.jpg",
    ),
    ("Dacia", "Duster"): CarPhoto(
        file="dacia-duster.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Dacia_Duster_III_IMG_8961.jpg",
    ),
    ("Dacia", "Jogger"): CarPhoto(
        file="dacia-jogger.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2023_Dacia_Jogger_DSC_7288.jpg",
    ),
    ("Dacia", "Sandero"): CarPhoto(
        file="dacia-sandero.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Dacia_Sandero_III_1X7A6451.jpg",
    ),
    ("Dacia", "Sandero Stepway"): CarPhoto(
        file="dacia-sandero-stepway.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2023_Dacia_Sandero_III_DSC_6012.jpg",
    ),
    ("Dacia", "Spring"): CarPhoto(
        file="dacia-spring.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Dacia_Spring_DSC_7939.jpg",
    ),
    ("Fiat", "500"): CarPhoto(
        file="fiat-500.jpg",
        author="Daniel Przygoda",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Fiat-500-vorne2.jpg",
    ),
    ("Fiat", "600"): CarPhoto(
        file="fiat-600.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Fiat_600_Hybrid_1.2_T3_Pop_(III)_–_f_24032026.jpg",
    ),
    ("Fiat", "Grande Panda"): CarPhoto(
        file="fiat-grande-panda.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Fiat_Grande_Panda_Elektro_La_Prima_–_f_01062025.jpg",
    ),
    ("Fiat", "Pandina"): CarPhoto(
        file="fiat-pandina.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Fiat_Pandina_IMG_0743.jpg",
    ),
    ("Fiat", "Tipo Sedan"): CarPhoto(
        file="fiat-tipo-sedan.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Fiat_Tipo_Sedan_Facelift_Leonberg_2022_1X7A0412.jpg",
    ),
    ("Ford", "Bronco"): CarPhoto(
        file="ford-bronco.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Ford_Bronco_(6th_generation)_Outer_Banks_1X7A0384.jpg",
    ),
    ("Ford", "Kuga"): CarPhoto(
        file="ford-kuga.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2020_Ford_Kuga_Titanium_First_Edition_EcoBlue_1.5.jpg",
    ),
    ("Ford", "Mustang"): CarPhoto(
        file="ford-mustang.jpg",
        author="WMrapids",
        license="CC0",
        source_url="https://commons.wikimedia.org/wiki/File:Seventh_generation_2024_Ford_Mustang_(cropped).jpg",
    ),
    ("Ford", "Puma"): CarPhoto(
        file="ford-puma.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Ford_Puma_(2019)_IMG_9475.jpg",
    ),
    ("Honda", "CR-V"): CarPhoto(
        file="honda-cr-v.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Honda_CR-V_e-HEV_Elegance_AWD_(VI)_–_f_14072024.jpg",
    ),
    ("Honda", "Civic"): CarPhoto(
        file="honda-civic.jpg",
        author="Elise240SX",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2022_Honda_Civic_Touring_in_Lunar_Silver_Metallic,_Front_Left,_05-10-2022.jpg",
    ),
    ("Honda", "HR-V"): CarPhoto(
        file="honda-hr-v.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2023_Honda_HR-V_Advance_i-MMD_CVT_1.5.jpg",
    ),
    ("Honda", "Jazz"): CarPhoto(
        file="honda-jazz.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Honda_Jazz_Hybrid_Executive_(IV)_–_f_18102020.jpg",
    ),
    ("Honda", "Prelude"): CarPhoto(
        file="honda-prelude.jpg",
        author="Calreyn88",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Honda_Prelude_2025.jpg",
    ),
    ("Honda", "ZR-V"): CarPhoto(
        file="honda-zr-v.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Honda_ZR-V_e-HEV_Advance_–_f_14072024.jpg",
    ),
    ("Hyundai", "Kona"): CarPhoto(
        file="hyundai-kona.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Hyundai_Kona_N_Line_(SX2)_DSC_8250.jpg",
    ),
    ("Hyundai", "Santa Fe"): CarPhoto(
        file="hyundai-santa-fe.jpg",
        author="Elise240SX",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Hyundai_Santa_Fe_Luxury_AWD_in_Hampton_Grey,_front_left,_2024-06-30.jpg",
    ),
    ("Hyundai", "Tucson"): CarPhoto(
        file="hyundai-tucson.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Hyundai_Tucson_(NX4)_1X7A0424.jpg",
    ),
    ("Hyundai", "i20"): CarPhoto(
        file="hyundai-i20.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Hyundai_i20_(III,_Facelift)_–_f_11102025.jpg",
    ),
    ("Hyundai", "i30"): CarPhoto(
        file="hyundai-i30.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Hyundai_i30_(PD)_DSC_8543.jpg",
    ),
    ("Kia", "Ceed SW"): CarPhoto(
        file="kia-ceed-sw.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Kia_Ceed_Sportswagon_1.5_T-GDI_48V_DCT_Ultimate_Edition_(III,_Facelift)_–_f_07062026.jpg",
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
    ("Lexus", "ES"): CarPhoto(
        file="lexus-es.jpg",
        author="Ohcock",
        license="CC0",
        source_url="https://commons.wikimedia.org/wiki/File:Lexus-ES-2026.jpg",
    ),
    ("Lexus", "LBX"): CarPhoto(
        file="lexus-lbx.jpg",
        author="Mr.choppers",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Lexus_LBX_Relax_in_Sonic_Quartz,_front_right.jpg",
    ),
    ("Lexus", "LM"): CarPhoto(
        file="lexus-lm.jpg",
        author="Ethan Llamas",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Lexus_LM_350h_AWD_AAWH15_Sonic_Quartz_with_cargo_box_+_roof_rack_01_(cropped).jpg",
    ),
    ("Lexus", "NX"): CarPhoto(
        file="lexus-nx.jpg",
        author="Kevauto",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2023_Lexus_NX_450h,_front_4.5.23.jpg",
    ),
    ("Lexus", "RX"): CarPhoto(
        file="lexus-rx.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Lexus_RX_500h_F_SPORT+_(V)_–_f_14072024.jpg",
    ),
    ("Lexus", "RZ"): CarPhoto(
        file="lexus-rz.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Lexus_RZ_300e_(XEBM10)_IMG_6622.jpg",
    ),
    ("Lexus", "UX"): CarPhoto(
        file="lexus-ux.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Lexus_UX_250h_IMG_2810.jpg",
    ),
    ("MG", "3"): CarPhoto(
        file="mg-3.jpg",
        author="Rutger van der Maar",
        license="CC BY 2.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_MG3_1.5_Hybrid+.jpg",
    ),
    ("MG", "4 EV Urban"): CarPhoto(
        file="mg-4-ev-urban.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:MG4_Electric_–_f_21042025.jpg",
    ),
    ("MG", "Cyberster"): CarPhoto(
        file="mg-cyberster.jpg",
        author="MrWalkr",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_MG_Cyberster.jpg",
    ),
    ("MG", "HS"): CarPhoto(
        file="mg-hs.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:MG_HS_Hybrid+_Luxury_(II)_–_f_12032026.jpg",
    ),
    ("MG", "S5 EV"): CarPhoto(
        file="mg-s5-ev.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:MGS5_EV_Automesse_Ludwigsburg_2025_DSC_2557.jpg",
    ),
    ("MG", "ZS"): CarPhoto(
        file="mg-zs.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:MG_ZS_Facelift_1X7A6412.jpg",
    ),
    ("Mazda", "3"): CarPhoto(
        file="mazda-3.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Mazda3_(BP)_1X7A7264.jpg",
    ),
    ("Mazda", "3 Sedan"): CarPhoto(
        file="mazda-3-sedan.jpg",
        author="TTTNIS",
        license="CC0",
        source_url="https://commons.wikimedia.org/wiki/File:Mazda3_SKYACTIV-G.jpg",
    ),
    ("Mazda", "CX-30"): CarPhoto(
        file="mazda-cx-30.jpg",
        author="EurovisionNim",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Mazda_CX-30_Touring,_2020_front.jpg",
    ),
    ("Mazda", "CX-5"): CarPhoto(
        file="mazda-cx-5.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Mazda_CX-5_(KF)_Facelift_1X7A0331_(2).jpg",
    ),
    ("Mercedes-Benz", "C-Class"): CarPhoto(
        file="mercedes-benz-c-class.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Mercedes-Benz_W206_IMG_5796.jpg",
    ),
    ("Mercedes-Benz", "C-Class Estate"): CarPhoto(
        file="mercedes-benz-c-class.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Mercedes-Benz_W206_IMG_5796.jpg",
    ),
    ("Mercedes-Benz", "E-Class"): CarPhoto(
        file="mercedes-benz-e-class.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Mercedes-Benz_W214_1X7A1841.jpg",
    ),
    ("Mercedes-Benz", "E-Class Estate"): CarPhoto(
        file="mercedes-benz-e-class.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Mercedes-Benz_W214_1X7A1841.jpg",
    ),
    ("Mitsubishi", "ASX"): CarPhoto(
        file="mitsubishi-asx.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Mitsubishi_ASX_(2nd_generation)_1X7A7067.jpg",
    ),
    ("Mitsubishi", "Colt"): CarPhoto(
        file="mitsubishi-colt.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Mitsubishi_Colt_(2023)_1X7A1657.jpg",
    ),
    ("Mitsubishi", "Eclipse Cross"): CarPhoto(
        file="mitsubishi-eclipse-cross.jpg",
        author="MercurySable99",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2023_Mitsubishi_Eclipse_Cross_SEL_Touring,_front_left.jpg",
    ),
    ("Mitsubishi", "Outlander PHEV"): CarPhoto(
        file="mitsubishi-outlander-phev.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2025_Mitsubishi_Outlander_PHEV_(fourth_generation)_IMG_3129.jpg",
    ),
    ("Nissan", "Juke"): CarPhoto(
        file="nissan-juke.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Nissan_Juke_(F16)_IMG_4903.jpg",
    ),
    ("Nissan", "Micra"): CarPhoto(
        file="nissan-micra.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Nissan_Micra_EV_IMG_4978.jpg",
    ),
    ("Nissan", "Qashqai"): CarPhoto(
        file="nissan-qashqai.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Nissan_Qashqai_e-Power_IMG_2187.jpg",
    ),
    ("Nissan", "X-Trail"): CarPhoto(
        file="nissan-x-trail.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Nissan_X-Trail_(T33)_1X7A7179.jpg",
    ),
    ("Opel", "Astra"): CarPhoto(
        file="opel-astra.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Opel_Astra_1.2_Turbo_Ultimate_(L)_–_f_13122024.jpg",
    ),
    ("Opel", "Astra Sports Tourer"): CarPhoto(
        file="opel-astra.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Opel_Astra_1.2_Turbo_Ultimate_(L)_–_f_13122024.jpg",
    ),
    ("Opel", "Corsa"): CarPhoto(
        file="opel-corsa.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Opel_Corsa_F_IMG_5815.jpg",
    ),
    ("Opel", "Frontera"): CarPhoto(
        file="opel-frontera.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Opel_Frontera_1.2_DIT_Hybrid_Ultimate_(C)_–_f_03042026.jpg",
    ),
    ("Opel", "Grandland"): CarPhoto(
        file="opel-grandland.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Opel_Grandland_B_DSC_7224.jpg",
    ),
    ("Opel", "Mokka"): CarPhoto(
        file="opel-mokka.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Opel_Mokka-e_IMG_6111.jpg",
    ),
    ("Peugeot", "2008"): CarPhoto(
        file="peugeot-2008.jpg",
        author="Cutlass",
        license="CC0",
        source_url="https://commons.wikimedia.org/wiki/File:2023_Peugeot_2008_in_Vertigo_Blue,_front_left,_06-08-2025.jpg",
    ),
    ("Peugeot", "208"): CarPhoto(
        file="peugeot-208.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2020_Peugeot_208_GT_Line_PureTech_1.2_Front.jpg",
    ),
    ("Peugeot", "3008"): CarPhoto(
        file="peugeot-3008.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Peugeot_e-3008_Automesse_Ludwigsburg_2024_IMG_1537.jpg",
    ),
    ("Peugeot", "308 SW"): CarPhoto(
        file="peugeot-308-sw.jpg",
        author="A.BourgeoisP",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2022_-_Peugeot_308_III_(C)_-_121.jpg",
    ),
    ("Peugeot", "408"): CarPhoto(
        file="peugeot-408.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Peugeot_408_(crossover)_1X7A7195.jpg",
    ),
    ("Peugeot", "5008"): CarPhoto(
        file="peugeot-5008.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Peugeot_5008_C_DSC_2949.jpg",
    ),
    ("Peugeot", "Rifter"): CarPhoto(
        file="peugeot-rifter.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Peugeot_Rifter_IMG_9556.jpg",
    ),
    ("Peugeot", "Rifter LONG"): CarPhoto(
        file="peugeot-rifter.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Peugeot_Rifter_IMG_9556.jpg",
    ),
    ("Renault", "4"): CarPhoto(
        file="renault-4.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_4_E-Tech_150_Comfort_Range_Techno_–_f_22062025.jpg",
    ),
    ("Renault", "5"): CarPhoto(
        file="renault-5.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_5_E-Tech_Electric_DSC_7279.jpg",
    ),
    ("Renault", "Arkana"): CarPhoto(
        file="renault-arkana.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_Arkana_(CMF-B)_Facelift_IMG_9961.jpg",
    ),
    ("Renault", "Austral"): CarPhoto(
        file="renault-austral.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_Austral_1X7A6753.jpg",
    ),
    ("Renault", "Captur"): CarPhoto(
        file="renault-captur.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Renault_Captur_II_Automesse_Ludwigsburg_2024_IMG_1506.jpg",
    ),
    ("Renault", "Clio"): CarPhoto(
        file="renault-clio.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_Clio_V_1X7A0393.jpg",
    ),
    ("Renault", "Espace"): CarPhoto(
        file="renault-espace.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_Espace_VI_IMG_9423.jpg",
    ),
    ("Renault", "Megane"): CarPhoto(
        file="renault-megane.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_Mégane_E-Tech_IMG_4064.jpg",
    ),
    ("Renault", "Rafale"): CarPhoto(
        file="renault-rafale.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_Rafale_E-Tech_Plug-in_Hybrid_300_4x4_Atelier_Alpine_–_f_30032025.jpg",
    ),
    ("Renault", "Scenic"): CarPhoto(
        file="renault-scenic.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_Scénic_E-Tech_IMG_9977.jpg",
    ),
    ("Renault", "Symbioz"): CarPhoto(
        file="renault-symbioz.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_Symbioz_IMG_0676.jpg",
    ),
    ("Renault", "Twingo"): CarPhoto(
        file="renault-twingo.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Renault_Twingo_E-Tech_IMG_6605.jpg",
    ),
    ("SEAT", "Arona"): CarPhoto(
        file="seat-arona.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_SEAT_Arona_SE_Technology_TSi_1.0_Front_(1).jpg",
    ),
    ("SEAT", "Ibiza"): CarPhoto(
        file="seat-ibiza.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_SEAT_Ibiza_SE_Technology_MPi_1.0_Front.jpg",
    ),
    ("SEAT", "Leon"): CarPhoto(
        file="seat-leon.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2020_SEAT_Leon_FR_TSi_Evo_1.5_Front.jpg",
    ),
    ("SEAT", "Leon Sportstourer"): CarPhoto(
        file="seat-leon.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2020_SEAT_Leon_FR_TSi_Evo_1.5_Front.jpg",
    ),
    ("Subaru", "Forester"): CarPhoto(
        file="subaru-forester.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Subaru_Forester_(SL)_e-BOXER_DSC_8811.jpg",
    ),
    ("Subaru", "Impreza"): CarPhoto(
        file="subaru-impreza.jpg",
        author="MercurySable99",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2024_Subaru_Impreza_Base,_front_right,_03-02-2024.jpg",
    ),
    ("Subaru", "Solterra"): CarPhoto(
        file="subaru-solterra.jpg",
        author="TTTNIS",
        license="CC0",
        source_url="https://commons.wikimedia.org/wiki/File:2025_Subaru_Solterra_ET-HS.jpg",
    ),
    ("Subaru", "Uncharted"): CarPhoto(
        file="subaru-uncharted.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Subaru_Uncharted_Auto_Zuerich_2025_DSC_3071.jpg",
    ),
    ("Subaru", "e-Outback"): CarPhoto(
        file="subaru-e-outback.jpg",
        author="TTTNIS",
        license="CC0",
        source_url="https://commons.wikimedia.org/wiki/File:2026_Subaru_Trailseeker_ET-HS.jpg",
    ),
    ("Suzuki", "S-Cross"): CarPhoto(
        file="suzuki-s-cross.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Suzuki_SX4_(3rd_generation)_1X7A6968.jpg",
    ),
    ("Suzuki", "Swift"): CarPhoto(
        file="suzuki-swift.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Suzuki_Swift_(2024)_hybrid_DSC_6076.jpg",
    ),
    ("Suzuki", "Vitara"): CarPhoto(
        file="suzuki-vitara.jpg",
        author="EurovisionNim",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_Suzuki_Vitara_(LY)_S_Turbo_wagon_(2018-11-02)_01.jpg",
    ),
    ("Suzuki", "e Vitara"): CarPhoto(
        file="suzuki-e-vitara.jpg",
        author="IXTA9839",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Suzuki_e_Vitara_in_Hamamatsu_Sta_front.jpg",
    ),
    ("Tesla", "Model 3"): CarPhoto(
        file="tesla-model-3.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Tesla_Model_3_(2023)_Autofrühling_Ulm_IMG_9282.jpg",
    ),
    ("Tesla", "Model Y"): CarPhoto(
        file="tesla-model-y.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Tesla_Model_Y_1X7A6211.jpg",
    ),
    ("Toyota", "C-HR"): CarPhoto(
        file="toyota-c-hr.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Toyota_C-HR_Hybrid_(AX20)_DSC_7239.jpg",
    ),
    ("Toyota", "Corolla Hatchback"): CarPhoto(
        file="toyota-corolla-hatchback.jpg",
        author="EurovisionNim",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_Toyota_Corolla_(MZEA12R)_Ascent_Sport_hatchback_(2018-11-02)_01.jpg",
    ),
    ("Toyota", "Corolla Sedan"): CarPhoto(
        file="toyota-corolla-hatchback.jpg",
        author="EurovisionNim",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_Toyota_Corolla_(MZEA12R)_Ascent_Sport_hatchback_(2018-11-02)_01.jpg",
    ),
    ("Toyota", "Corolla Touring Sports"): CarPhoto(
        file="toyota-corolla-hatchback.jpg",
        author="EurovisionNim",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_Toyota_Corolla_(MZEA12R)_Ascent_Sport_hatchback_(2018-11-02)_01.jpg",
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
    ("Toyota", "Yaris Cross"): CarPhoto(
        file="toyota-yaris-cross.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Toyota_Yaris_Cross_Hybrid_(XP210)_1X7A1846.jpg",
    ),
    ("Volkswagen", "Golf"): CarPhoto(
        file="volkswagen-golf.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volkswagen_Golf_VIII_GTI_Clubsport_45_IMG_4884.jpg",
    ),
    ("Volkswagen", "Golf Variant"): CarPhoto(
        file="volkswagen-golf-variant.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2020_Volkswagen_Golf_Style_1.5_Front.jpg",
    ),
    ("Volkswagen", "ID. Polo"): CarPhoto(
        file="volkswagen-id-polo.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volkswagen_ID.Polo_IMG_8361.jpg",
    ),
    ("Volkswagen", "ID.3 Neo"): CarPhoto(
        file="volkswagen-id-3-neo.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2020_Volkswagen_ID.3_1st_Front.jpg",
    ),
    ("Volkswagen", "ID.4"): CarPhoto(
        file="volkswagen-id-4.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volkswagen_ID.4_GTX_1X7A0301.jpg",
    ),
    ("Volkswagen", "ID.7"): CarPhoto(
        file="volkswagen-id-7.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volkswagen_ID.7_DSC_7879_(cropped).jpg",
    ),
    ("Volkswagen", "ID.7 Tourer"): CarPhoto(
        file="volkswagen-id-7.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volkswagen_ID.7_DSC_7879_(cropped).jpg",
    ),
    ("Volkswagen", "Passat"): CarPhoto(
        file="volkswagen-passat.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:VW_Passat_Variant_Elegance_(B9)_–_f_18052025.jpg",
    ),
    ("Volkswagen", "Polo"): CarPhoto(
        file="volkswagen-polo.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_Volkswagen_Polo_SE_1.0_Front.jpg",
    ),
    ("Volkswagen", "T-Cross"): CarPhoto(
        file="volkswagen-t-cross.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:VW_T-Cross_Style_(Facelift)_–_f_22022025.jpg",
    ),
    ("Volkswagen", "T-Roc"): CarPhoto(
        file="volkswagen-t-roc.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:VW_T-Roc_1.5_eTSI_Style_(II)_–_f_05052026.jpg",
    ),
    ("Volkswagen", "Taigo"): CarPhoto(
        file="volkswagen-taigo.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volkswagen_Taigo_1X7A0350.jpg",
    ),
    ("Volkswagen", "Tayron"): CarPhoto(
        file="volkswagen-tayron.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:VW_Tayron_1.5_eTSI_Elegance_–_f_28022026.jpg",
    ),
    ("Volkswagen", "Tiguan"): CarPhoto(
        file="volkswagen-tiguan.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volkswagen_Tiguan_III_IMG_8388.jpg",
    ),
    ("Volkswagen", "Touran"): CarPhoto(
        file="volkswagen-touran.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_Volkswagen_Touran_1.6.jpg",
    ),
    ("Volvo", "EC40"): CarPhoto(
        file="volvo-ec40.jpg",
        author="Ethan Llamas",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volvo_EC40_Crystal_White_Pearl_-_front.jpg",
    ),
    ("Volvo", "ES90"): CarPhoto(
        file="volvo-es90.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Volvo_ES90_Ultra_–_f_29032026.jpg",
    ),
    ("Volvo", "EX30"): CarPhoto(
        file="volvo-ex30.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volvo_EX30_IMG_8923.jpg",
    ),
    ("Volvo", "EX40"): CarPhoto(
        file="volvo-ex40.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volvo_XC40_Recharge_Facelift_IMG_8127.jpg",
    ),
    ("Volvo", "EX60"): CarPhoto(
        file="volvo-ex60.jpg",
        author="Herranderssvensson",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volvo_EX60_fl.jpg",
    ),
    ("Volvo", "EX90"): CarPhoto(
        file="volvo-ex90.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Volvo_EX90_autoMOBIL_Tübingen_2025_DSC_2740.jpg",
    ),
    ("Volvo", "V60"): CarPhoto(
        file="volvo-v60.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_Volvo_V60_Inscription_PRO_D4_Automatic_2.0.jpg",
    ),
    ("Volvo", "XC40"): CarPhoto(
        file="volvo-xc40.jpg",
        author="Elise240SX",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2019_Volvo_XC40_T5_Momentum_in_Bright_Silver_Metallic,_front_left,_2025-09-22.jpg",
    ),
    ("Volvo", "XC60"): CarPhoto(
        file="volvo-xc60.jpg",
        author="Vauxford",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:2018_Volvo_XC60_R-Design_D5_P-Pulse_2.0_Front.jpg",
    ),
    ("Volvo", "XC90"): CarPhoto(
        file="volvo-xc90.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Volvo_XC90_T8_AWD_Plug-in_Hybrid_Plus_(II,_2._Facelift)_–_f_03102025.jpg",
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
    ("Škoda", "Epiq"): CarPhoto(
        file="skoda-epiq.jpg",
        author="Alexander-93",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Škoda_Epiq_Showcar_IAA_2025_DSC_1378_(cropped).jpg",
    ),
    ("Škoda", "Fabia"): CarPhoto(
        file="skoda-fabia.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Skoda_Fabia_IV_1X7A6155.jpg",
    ),
    ("Škoda", "Kamiq"): CarPhoto(
        file="skoda-kamiq.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Skoda_Kamiq_(2019)_Monte_Carlo_1X7A6165.jpg",
    ),
    ("Škoda", "Karoq"): CarPhoto(
        file="skoda-karoq.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Skoda_Karoq_–_f_18042025.jpg",
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
    ("Škoda", "Peaq"): CarPhoto(
        file="skoda-peaq.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Škoda_Peaq_Sindelfingen_2026_IMG_8235.jpg",
    ),
    ("Škoda", "Scala"): CarPhoto(
        file="skoda-scala.jpg",
        author="Alexander Migl",
        license="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Skoda_Scala_IMG_3560.jpg",
    ),
    ("Škoda", "Superb"): CarPhoto(
        file="skoda-superb.jpg",
        author="M 93",
        license="CC BY-SA 3.0 de",
        source_url="https://commons.wikimedia.org/wiki/File:Skoda_Superb_L&K_(IV)_–_f_12042026.jpg",
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
