"""Pipeline orchestration: registry -> monitor -> downloader -> parser -> DB.

For each active source it finds new PDF price lists
(SourceMonitor.fetch_new_documents), parses them with the parser matching
`parser_key` (parsers/registry.py), and stores the resulting variants and
prices in the DB (VariantRepository).
"""
from __future__ import annotations

from pathlib import Path

import pdfplumber
from sqlalchemy.orm import Session

from scraper.database.db import get_session, init_db
from scraper.database.models import Document
from scraper.database.repositories import VariantRepository
from scraper.monitors.source_monitor import SourceMonitor
from scraper.parsers._pdf_layout import extract_release_date
from scraper.parsers.registry import PARSERS
from scraper.sources.registry import Source, SourceRegistry


class ScraperPipeline:
    """Orchestrator: for each active source, downloads new documents, parses
    them, and stores them. Each step (registry/monitor/parsers/repository)
    is injectable, so the pipeline can be tested with stand-ins for the
    network/DB."""

    def __init__(
        self,
        session: Session | None = None,
        source_registry: SourceRegistry | None = None,
        monitor: SourceMonitor | None = None,
        variant_repository: VariantRepository | None = None,
    ) -> None:
        self._session = session or get_session()
        self._source_registry = source_registry or SourceRegistry()
        self._monitor = monitor or SourceMonitor(self._session)
        self._variants = variant_repository or VariantRepository(self._session)

    def _process_document(self, source: Source, document: Document) -> None:
        parser_cls = PARSERS.get(source.parser_key)
        if parser_cls is None:
            print(f"  skipped (unknown parser_key {source.parser_key!r}): {document.document_url}")
            return

        pdf_path = Path(document.file_path)

        with pdfplumber.open(pdf_path) as pdf:
            document.release_date = extract_release_date(pdf)
        self._session.commit()

        try:
            variants = parser_cls().parse(pdf_path)
        except NotImplementedError as exc:
            print(f"  skipped ({exc}): {document.document_url}")
            return

        saved = self._variants.save(document, source.brand, variants)
        print(f"  {document.document_url}: saved {len(saved)} variants (valid from {document.release_date})")

    def run(self) -> None:
        init_db()

        for source in self._source_registry.load_active():
            print(f"Active source: {source.parser_key} ({source.source_url})")
            new_documents = self._monitor.fetch_new_documents(source)
            print(f"  new documents: {len(new_documents)}")
            for document in new_documents:
                self._process_document(source, document)

        self._session.close()


if __name__ == "__main__":
    ScraperPipeline().run()
