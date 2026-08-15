# Local data storage

All local database files and PDF copies for the project live under this one directory, instead of
scattered inside `backend/` and `scraper/`. What's here and where it comes from:

```
storage/
├── drivewise.db     backend's SQLite dev DB — gitignored, regenerate with:
│                     cd backend && alembic upgrade head && python -m app.db.seed
├── scraper.db        scraper's SQLite DB — committed on purpose (a reproducible scraped-data
│                     baseline so you don't need to run a live scrape just to browse/verify data)
├── cars/              hand-picked source price-list PDFs used to hand-seed backend/'s demo data
│   ├── mazda/cx-5/*.pdf         (see backend/app/db/seed.py, backend/README.md's Tests section)
│   └── vw/tiguan/*.pdf
└── scraper/            PDFs scraper/ has downloaded, organized <brand>/<year>/<sha256>.pdf —
    ├── kia/2026/*.pdf   committed alongside scraper.db (same reproducibility reason); re-running
    ├── skoda/2026/*.pdf  the scraper against live sources adds to this, never overwrites (hash-
    ├── toyota/2026/*.pdf  named, see scraper/downloaders/pdf_downloader.py)
    └── volkswagen/2026/*.pdf
```

`storage/cars/` and `storage/scraper/` serve different purposes despite both holding PDFs: `cars/`
is a small, manually curated set used as backend test/demo fixtures (their content was hand-
transcribed and verified — see `backend/README.md`); `scraper/` is the scraper module's own
downloaded corpus, discovered and parsed automatically.

## Why one shared directory

`backend/` and `scraper/` are still independent services (see `doc/arch/webScraping/` and the
`drivewise-scraper` skill for why) — this is purely about where their *data* physically lives, not
about coupling the services. Both `backend/app/core/config.py`'s `DATABASE_URL` default and
`scraper/database/db.py`'s `DEFAULT_SQLITE_PATH` / `scraper/downloaders/pdf_downloader.py`'s
`STORAGE_ROOT` point here relative to the repo root, so this is the one place to look for (or
delete, to reset) any local Python-side data file.
