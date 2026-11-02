"""ScraperPipeline keeps going when one source, model or document fails:
a failed download skips just that model, a source whose discovery raises
is skipped, a document whose parsing raises is rolled back and deleted
(so the next run retries it), and everything skipped is summarized at
the end. Network, discoverers and parsers are stand-ins; the DB is an
in-memory SQLite with the real schema."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import scraper.main as pipeline_module
import scraper.monitors.source_monitor as monitor_module
from scraper.database.models import Base, Document, Variant
from scraper.main import ScraperPipeline
from scraper.monitors.source_monitor import SourceMonitor
from scraper.parsers.base import ExtractedVariant
from scraper.sources.registry import Source


class _StubDownloader:
    """Writes the URL itself as the file content; "bad" URLs raise an HTTP error."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def download(self, url: str, brand: str) -> tuple[Path, str]:
        if "bad" in url:
            raise requests.HTTPError(f"404 Client Error: Not Found for url: {url}")
        content = url.encode()
        path = self._root / f"{hashlib.sha256(content).hexdigest()}.json"
        path.write_bytes(content)
        return path, hashlib.sha256(content).hexdigest()


class _TwoModelDiscoverer:
    def discover(self, source: Source) -> dict[str, str]:
        return {
            "Broken": "https://oem.test/bad.pdf",
            "Good": "https://oem.test/good.pdf",
            "Boom": "https://oem.test/boom.pdf",
        }


class _UnreachableDiscoverer:
    def discover(self, source: Source) -> dict[str, str]:
        raise requests.ConnectionError("listing page unreachable")


class _StubParser:
    def parse(self, path: Path) -> list[ExtractedVariant]:
        if "boom" in path.read_text():
            raise ValueError("unexpected table layout")
        return [
            ExtractedVariant(
                model="Good",
                trim="Base",
                variant_name="Good Base",
                price=500_000.0,
                currency="CZK",
                source_page=1,
                raw_text="Good Base 500 000 Kč",
                powertrain="ICE",
            )
        ]


class _StubRegistry:
    def load_active(self) -> list[Source]:
        common = {"country": "cz", "source_url": None, "pdf_pattern": None, "active": True, "content_type": "json"}
        return [
            Source(brand="unreachable", parser_key="unreachable", **common),
            Source(brand="flaky", parser_key="flaky", **common),
        ]


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.fixture
def pipeline(session, tmp_path, monkeypatch) -> ScraperPipeline:
    monkeypatch.setattr(pipeline_module, "init_db", lambda: None)
    monkeypatch.setattr(
        monitor_module, "DISCOVERERS", {"flaky": _TwoModelDiscoverer, "unreachable": _UnreachableDiscoverer}
    )
    monkeypatch.setattr(pipeline_module, "PARSERS", {"flaky": _StubParser, "unreachable": _StubParser})

    monitor = SourceMonitor(session, json_downloader=_StubDownloader(tmp_path))
    return ScraperPipeline(session=session, source_registry=_StubRegistry(), monitor=monitor)


def test_pipeline_skips_failures_and_keeps_processing(pipeline, session, capsys) -> None:
    pipeline.run()

    # Only the good model's document and variant survive.
    assert [d.document_url for d in session.query(Document).all()] == ["https://oem.test/good.pdf"]
    assert [v.variant_name for v in session.query(Variant).all()] == ["Good Base"]

    assert [(f.parser_key, f.item) for f in pipeline.failures] == [
        ("unreachable", "discovery"),
        ("flaky", "https://oem.test/boom.pdf"),
        ("flaky", "Broken"),
    ]
    assert pipeline.failures[0].error == "ConnectionError: listing page unreachable"
    assert pipeline.failures[1].error == "ValueError: unexpected table layout"
    assert pipeline.failures[2].error.startswith("HTTPError: 404 Client Error")

    out = capsys.readouterr().out
    assert "Finished with 3 skipped item(s):" in out
    assert "flaky / Broken: HTTPError: 404 Client Error" in out


def test_failed_document_is_retried_on_next_run(pipeline, session, monkeypatch) -> None:
    pipeline.run()

    # The parser is fixed before the next run: the previously failing
    # document must be picked up again rather than deduplicated away.
    monkeypatch.setattr(_StubParser, "parse", lambda self, path: [])
    pipeline.run()

    urls = sorted(d.document_url for d in session.query(Document).all())
    assert urls == ["https://oem.test/boom.pdf", "https://oem.test/good.pdf"]
