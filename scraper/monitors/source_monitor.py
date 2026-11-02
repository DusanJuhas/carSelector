"""Checks whether there's a new price-list document (by SHA256 hash), and
if so, downloads it and writes a record to the `document` table.

Finding the specific document links (how many pages to fetch, where the
links are) is per-brand logic — see `discovery/` (Škoda: a single listing
page with all models; VW: a separate page per model). The fetch is part of
the discoverer; `SourceMonitor` just passes it the `source`.

A model whose download fails (HTTP error, timeout, connection error) is
skipped and recorded in `SourceMonitor.failures` rather than aborting the
whole source - one broken link (e.g. an OEM briefly serving a 404 for one
model's PDF) shouldn't cost every other model of that brand, or every
brand after it, its run.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests
from sqlalchemy.orm import Session

from scraper.database.models import Document
from scraper.downloaders.html_downloader import HtmlDownloader
from scraper.downloaders.json_downloader import JsonDownloader
from scraper.downloaders.pdf_downloader import PdfDownloader
from scraper.monitors.discovery.registry import DISCOVERERS
from scraper.sources.registry import Source


@dataclass(frozen=True)
class ScrapeFailure:
    """One unit of work skipped after an error, for the end-of-run summary.

    `parser_key` names the source, `item` what was being processed (a
    model name, a document URL, or "discovery" for the source as a whole),
    and `error` a one-line description of the exception.
    """

    parser_key: str
    item: str
    error: str


def describe_error(exc: BaseException) -> str:
    """Args:
        exc: The exception that caused a skip.

    Returns:
        "<ExceptionType>: <message>", on one line.
    """
    message = " ".join(str(exc).split())
    return f"{type(exc).__name__}: {message}" if message else type(exc).__name__


class SourceMonitor:
    """Finds new documents for a given source and stores them in the DB.

    `failures` accumulates every model skipped by `fetch_new_documents`
    across all sources this monitor has processed.
    """

    def __init__(
        self,
        session: Session,
        downloader: PdfDownloader | None = None,
        json_downloader: JsonDownloader | None = None,
        html_downloader: HtmlDownloader | None = None,
    ) -> None:
        self._session = session
        self._downloader = downloader or PdfDownloader()
        self._json_downloader = json_downloader or JsonDownloader()
        self._html_downloader = html_downloader or HtmlDownloader()
        self.failures: list[ScrapeFailure] = []

    def check_and_store(self, source: Source, pdf_url: str) -> Document | None:
        """Downloads the document, and if its hash isn't in the DB yet, creates a new Document.

        Args:
            source: The source this document belongs to (for
                `source.brand`/`source.content_type`).
            pdf_url: URL of the document to download and check (a PDF for
                every brand except Audi, whose own `content_type` is
                "json", and Tesla, whose own is "html" - see
                `sources/registry.py`'s own docstring).

        Returns:
            The newly created `Document`, or `None` if a document with
            this exact content (same brand + SHA256 hash) already exists.
        """
        if source.content_type == "json":
            downloader = self._json_downloader
        elif source.content_type == "html":
            downloader = self._html_downloader
        else:
            downloader = self._downloader
        path, file_hash = downloader.download(pdf_url, brand=source.brand)

        existing = self._session.query(Document).filter_by(source_brand=source.brand, sha256_hash=file_hash).first()
        if existing:
            return None  # already processed, nothing new

        document = Document(
            source_brand=source.brand,
            document_url=pdf_url,
            sha256_hash=file_hash,
            file_path=str(path),
        )
        self._session.add(document)
        self._session.commit()
        return document

    def fetch_new_documents(self, source: Source) -> list[Document]:
        """Uses the matching Discoverer to find price list links for the
        models in `source.models` and creates a Document for each new one
        (by SHA256). Returns only newly created records (already-processed
        PDFs are skipped, see check_and_store). A model whose download
        fails with a network/HTTP error is skipped, printed, and recorded
        in `self.failures`; the remaining models are still processed.
        Errors from discovery itself propagate - the caller decides what
        to do about a source it can't list at all (see `ScraperPipeline`).

        Args:
            source: Source to find and store new documents for.

        Returns:
            Newly created `Document` rows (empty if none are new, or if
            `source.parser_key` has no registered discoverer).
        """
        discoverer_cls = DISCOVERERS.get(source.parser_key)
        if discoverer_cls is None:
            return []

        price_list_urls = discoverer_cls().discover(source)

        new_documents = []
        for model, pdf_url in price_list_urls.items():
            try:
                document = self.check_and_store(source, pdf_url)
            except requests.RequestException as exc:
                self._session.rollback()
                failure = ScrapeFailure(source.parser_key, model, describe_error(exc))
                self.failures.append(failure)
                print(f"  skipped {model} ({failure.error}): {pdf_url}", flush=True)
                continue
            if document is not None:
                new_documents.append(document)
        return new_documents
