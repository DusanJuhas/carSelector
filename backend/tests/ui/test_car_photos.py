"""Car photos on result cards (see `app/ui/car_photos.py`). The seeded
catalog has no Toyota, so the card test maps a photo onto the seeded
Mazda CX-5 and checks the VW Tiguan keeps its placeholder.
"""

from pathlib import Path

import pytest
from nicegui.testing import User

from app.ai import client as client_module
from app.ui import car_photos
from app.ui.car_photos import CAR_PHOTOS, PHOTOS_DIR, CarPhoto, photo_for

pytestmark = [
    pytest.mark.usefixtures("patch_ui_session"),
    pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py"))),
]


@pytest.fixture(autouse=True)
def _no_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(client_module, "AI_PROVIDER", "groq")
    monkeypatch.setattr(client_module, "GROQ_API_KEY", None)
    client_module.set_runtime_api_key(None)
    yield
    client_module.set_runtime_api_key(None)


def test_every_photo_file_exists_and_has_attribution() -> None:
    assert CAR_PHOTOS
    for photo in CAR_PHOTOS.values():
        assert (PHOTOS_DIR / photo.file).is_file(), photo.file
        assert photo.author and photo.license
        assert photo.source_url.startswith("https://commons.wikimedia.org/wiki/File:")


def test_photo_for_matches_exact_catalog_names() -> None:
    assert photo_for("Toyota", "RAV4") is not None
    assert photo_for("Toyota", "Yaris") is None


async def test_card_shows_photo_with_credit_or_placeholder(user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    photo = CarPhoto(
        file="toyota-rav4.jpg", author="Test Author", license="CC0", source_url="https://example.org/photo"
    )
    monkeypatch.setattr(car_photos, "CAR_PHOTOS", {("Mazda", "CX-5"): photo})

    await user.open("/")
    await user.should_see("v katalogu", retries=100)

    images = [img for img in user.find(marker="car-photo").elements if img.props.get("src") == photo.url]
    assert images and all(img.props.get("alt") == "Mazda CX-5" for img in images)
    await user.should_see("Foto: Test Author, CC0")
    await user.should_see("fotka auta — Volkswagen Tiguan")
    await user.should_not_see("fotka auta — Mazda CX-5")
