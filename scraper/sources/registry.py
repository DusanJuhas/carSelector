"""Loads the source (OEM) registry from config/sources.yaml.

Anyone on the team can add a new brand by editing the YAML file, without
touching the downloader, monitor, or other brands' parsers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "sources.yaml"


@dataclass(frozen=True)
class Source:
    brand: str
    country: str
    source_url: str | None
    pdf_pattern: str | None
    parser_key: str
    active: bool
    # Models belonging to this source. A single brand can have multiple
    # sources with the same source_url but a different parser_key (e.g.
    # Škoda: combustion models and EVs are on the same page, but have a
    # different PDF structure, and thus a different parser) — models then
    # determines which found documents belong to which source.
    models: list[str] = field(default_factory=list)


class SourceRegistry:
    """Loads and provides sources (OEMs) from `config/sources.yaml`."""

    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self._config_path = config_path

    def load_all(self) -> list[Source]:
        data = yaml.safe_load(self._config_path.read_text(encoding="utf-8"))
        return [Source(**entry) for entry in data["sources"]]

    def load_active(self) -> list[Source]:
        return [s for s in self.load_all() if s.active]

    def get_by_parser_key(self, parser_key: str) -> Source | None:
        return next((s for s in self.load_all() if s.parser_key == parser_key), None)
