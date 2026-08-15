"""Downloads a PDF and stores it under its hash, so an existing version is
never overwritten and history can be traced (auditability, see the
architecture doc)."""
from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

import requests

# Repo-root storage/scraper/, not scraper/storage/ - all local data files
# (this module's downloads, scraper.db, backend's drivewise.db, the hand-
# picked fixture PDFs in storage/cars/) live under one top-level storage/
# directory - see storage/README.md.
STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage" / "scraper"


def sha256_of(content: bytes) -> str:
    """Args:
        content: Raw bytes to hash.

    Returns:
        Hex-encoded SHA-256 digest of `content`.
    """
    return hashlib.sha256(content).hexdigest()


class PdfDownloader:
    """Downloads PDFs and stores them under their hash, so an existing
    version is never overwritten and history can be traced (auditability,
    see the architecture doc).

    `storage_root` is injectable (e.g. for tests with a temp directory)."""

    def __init__(self, storage_root: Path = STORAGE_ROOT) -> None:
        self._storage_root = storage_root

    def download(self, url: str, brand: str, *, timeout: int = 30) -> tuple[Path, str]:
        """Downloads the PDF and stores it at storage/scraper/<brand>/<year>/<hash>.pdf.

        Args:
            url: URL of the PDF to download.
            brand: Brand key this PDF belongs to (used as the storage
                subdirectory).
            timeout: HTTP request timeout in seconds.

        Returns:
            `(file_path, sha256_hash)` - `file_path` is where the PDF now
            lives on disk (already existed there if this exact content
            was downloaded before); `sha256_hash` is compared in the
            monitor against the document table so the same content is
            never processed twice.
        """
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        content = response.content

        file_hash = sha256_of(content)
        year_dir = self._storage_root / brand / str(date.today().year)
        year_dir.mkdir(parents=True, exist_ok=True)

        target = year_dir / f"{file_hash}.pdf"
        if not target.exists():
            target.write_bytes(content)

        return target, file_hash
