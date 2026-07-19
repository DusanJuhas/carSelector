---
name: drivewise-scraper
description: The web-scraping data-collection service for DriveWise AI that gathers vehicle models, specs, features, and pricing from external sources and writes cleaned records into PostgreSQL. Use this whenever building or changing anything that ingests vehicle data from outside the system — scrapers, parsers, data-cleaning steps, scheduled collection jobs, or the pipeline that feeds the catalog. Reach for it any time a task involves pulling car data from manufacturer sites, dealer portals, or marketplaces, or preparing raw external data for the database, even if it's just called "the data pipeline" or "getting car data."
---

# DriveWise AI — Web Scraping Service

A dedicated, standalone Python service that populates the vehicle catalog. It runs **offline, outside the request path** — user requests never trigger or wait on scraping. Its only output is cleaned rows written to PostgreSQL.

## Pipeline

```
Data sources → Scraper → Data cleaning → PostgreSQL → (Recommendation engine reads later)
```

1. **Collect** from external sources.
2. **Clean/normalize** raw fields into the catalog's shape.
3. **Write** into `cars`, `car_specs`, `car_prices`, `car_features` (see `drivewise-data-model` for the schema — the scraper is the write-owner of `car_prices.last_updated`).

## Sources

- Manufacturer websites
- Dealer websites / portals
- Vehicle marketplaces
- Public price lists

## Collected data

Vehicle models, technical specifications, features, pricing information, and vehicle descriptions — mapped onto the four catalog tables.

## Tooling

Pick per source, cheapest that works:
- **BeautifulSoup** — static HTML pages.
- **Scrapy** — larger crawls, many pages, built-in throttling/pipelines.
- **Playwright** — JS-rendered pages that need a real browser.

## Cleaning conventions

- Normalize units before writing: consumption, power, trunk capacity, currency — don't store whatever string the source used.
- Deduplicate on a stable natural key (brand + model + year + trim) so re-runs update rather than duplicate.
- Keep `price` and `currency` together; stamp `last_updated` on every price write.
- Map source-specific attributes without a dedicated column into `car_features` rows rather than widening tables.
- Fail soft per-record: a malformed listing should be logged and skipped, not abort the whole run.

## Operational notes

- Be a good citizen: respect robots.txt and rate limits, set a real User-Agent, back off on errors.
- Make runs idempotent and re-runnable (upsert, don't blind-insert).
- The service is decoupled and independently scalable — keep it free of backend/API imports so it can run as its own container or scheduled job.
