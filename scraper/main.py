"""Pipeline orchestration: registry -> monitor -> downloader -> parser -> DB.

For each active source it finds new price-list documents
(SourceMonitor.fetch_new_documents - a PDF for every brand except Audi
(`content_type` "json") and Tesla (`content_type` "html"), see
sources/registry.py), parses them
with the parser matching `parser_key` (parsers/registry.py), and stores
the resulting variants and prices in the DB (VariantRepository).

One failing source, model or document never stops the run: a source whose
discovery raises is skipped, a model whose download fails is skipped (see
SourceMonitor), and a document whose parsing raises is rolled back and
deleted again so the next run retries it instead of treating it as
already processed. Everything skipped is listed at the end of the run;
the exit code stays 0, since the run itself completed - check that
summary (also visible in the admin console's log) for what was missed.
"""

from __future__ import annotations

from pathlib import Path

import pdfplumber
from sqlalchemy.orm import Session

from scraper.database.db import get_session, init_db
from scraper.database.models import Document
from scraper.database.repositories import VariantRepository
from scraper.monitors.source_monitor import ScrapeFailure, SourceMonitor, describe_error
from scraper.parsers._pdf_layout import extract_release_date
from scraper.parsers.registry import PARSERS
from scraper.progress import report_progress
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
        """Args:
        session: DB session to use. Defaults to a new session from
            `database.db.get_session()`.
        source_registry: Provides the sources to process. Defaults to
            a `SourceRegistry` reading `config/sources.yaml`.
        monitor: Finds/downloads new documents. Defaults to a
            `SourceMonitor` bound to `session`.
        variant_repository: Persists parsed variants/prices/equipment.
            Defaults to a `VariantRepository` bound to `session`.
        """
        self._session = session or get_session()
        self._source_registry = source_registry or SourceRegistry()
        self._monitor = monitor or SourceMonitor(self._session)
        self._variants = variant_repository or VariantRepository(self._session)
        # Sources/documents skipped by the pipeline itself; per-model
        # download failures live in `self._monitor.failures`.
        self._failures: list[ScrapeFailure] = []

    @property
    def failures(self) -> list[ScrapeFailure]:
        """Everything skipped during `run`, in the order it happened
        (sources and documents from the pipeline, models from the monitor)."""
        return [*self._failures, *self._monitor.failures]

    def _process_document(self, source: Source, document: Document) -> None:
        """Parses one newly-discovered document and persists its variants.

        Args:
            source: The source `document` was discovered under (gives
                `parser_key`/`brand`/`content_type`).
            document: The document to parse - `document.release_date` is
                set here from the PDF itself before parsing, for `pdf`
                sources only (see `source.content_type`'s own docstring -
                Audi's own JSON API has no comparable "valid from" field
                to read, so its documents just keep the download date).
        """
        parser_cls = PARSERS.get(source.parser_key)
        if parser_cls is None:
            print(f"  skipped (unknown parser_key {source.parser_key!r}): {document.document_url}")
            return

        document_path = Path(document.file_path)

        if source.content_type == "pdf":
            with pdfplumber.open(document_path) as pdf:
                document.release_date = extract_release_date(pdf)
            self._session.commit()

        try:
            parser = parser_cls()
            parser.document_url = document.document_url
            variants = parser.parse(document_path)
        except NotImplementedError as exc:
            print(f"  skipped ({exc}): {document.document_url}")
            return

        saved = self._variants.save(document, source.brand, variants)
        print(f"  {document.document_url}: saved {len(saved)} variants (valid from {document.release_date})")

    def run(self) -> None:
        """Runs one full pass: for every active source, discovers and
        downloads new documents, parses each, and persists the result.
        Prints progress per source/document to stdout (human-readable
        lines plus `scraper/progress.py`'s `PROGRESS` lines); closes the DB
        session before returning.
        """
        init_db()

        sources = self._source_registry.load_active()
        for index, source in enumerate(sources, start=1):
            report_progress(index, len(sources), source.parser_key)
            print(f"Active source: {source.parser_key} ({source.source_url})")
            try:
                new_documents = self._monitor.fetch_new_documents(source)
            except Exception as exc:  # noqa: BLE001 - one broken source must not stop the others
                self._session.rollback()
                self._record_failure(source, "discovery", exc)
                continue
            print(f"  new documents: {len(new_documents)}")
            report_progress(index, len(sources), source.parser_key, 0, len(new_documents))
            for done, document in enumerate(new_documents, start=1):
                try:
                    self._process_document(source, document)
                except Exception as exc:  # noqa: BLE001 - one broken document must not stop the others
                    self._discard_document(document)
                    self._record_failure(source, document.document_url, exc)
                report_progress(index, len(sources), source.parser_key, done, len(new_documents))

        self._print_summary()
        self._session.close()

    def _record_failure(self, source: Source, item: str, exc: Exception) -> None:
        """Logs and remembers one skipped unit of work.

        Args:
            source: The source being processed.
            item: What failed ("discovery" or a document URL).
            exc: The exception raised.
        """
        failure = ScrapeFailure(source.parser_key, item, describe_error(exc))
        self._failures.append(failure)
        print(f"  skipped {item} ({failure.error})", flush=True)

    def _discard_document(self, document: Document) -> None:
        """Rolls back a failed parse and deletes its `Document` row, so the
        next run sees the file as new and retries it (otherwise the hash
        dedup in `SourceMonitor.check_and_store` would skip it forever with
        no variants saved). `VariantRepository.save` commits only at its
        very end, so nothing partial survives the rollback.

        Args:
            document: The document whose processing failed.
        """
        self._session.rollback()
        self._session.delete(document)
        self._session.commit()

    def _print_summary(self) -> None:
        """Prints every skipped source/model/document, or nothing if the
        run had no failures."""
        failures = self.failures
        if not failures:
            return
        print(f"Finished with {len(failures)} skipped item(s):")
        for failure in failures:
            print(f"  {failure.parser_key} / {failure.item}: {failure.error}")


if __name__ == "__main__":
    ScraperPipeline().run()
