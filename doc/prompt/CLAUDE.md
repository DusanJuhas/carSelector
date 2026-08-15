# CLAUDE.md – DriveWise AI (Car Selector)

Tento soubor čte Claude Code (nebo jiný agent) automaticky na začátku práce v tomto repozitáři.
Obsahuje konvence a kontext, aby generovaný kód odpovídal architektuře projektu bez nutnosti to
opakovat v každém promptu.

## O projektu

DriveWise AI je aplikace pro výběr vozidel na základě požadavků, preferencí a rozpočtu uživatele.
Kombinuje AI analýzu požadavků (Claude API) s katalogem vozidel v PostgreSQL databázi.
Plná architektura: viz `doc/arch/architecture.md` (pozor: aktuálně superseded, viz poznámka
na začátku toho souboru).

## Struktura repozitáře

```
/frontend        React + TypeScript aplikace
  /src
    /components  znovupoužitelné UI komponenty (jedna komponenta = jeden soubor + test)
    /pages       routované obrazovky (wizard, chat, výsledky)
    /hooks       vlastní React hooks
    /api         volání backendu (typované, přes Axios klienta v api/client.ts)
    /types       sdílené TS typy (odpovídají Pydantic modelům backendu)
    /store       globální stav (Zustand)
/backend         FastAPI aplikace
  /app
    /api         REST endpointy
    /services    business logika, recommendation engine
    /ai          integrace Claude API (extrakce požadavků, vysvětlení doporučení)
    /models      SQLAlchemy modely
    /schemas     Pydantic schémata (request/response)
/scraper         samostatná Python služba pro sběr dat o vozidlech
/doc             architektura, API kontrakty, poznámky (viz doc/README.md pro přehled)
/storage         všechny lokální DB soubory + PDF kopie pro /backend a /scraper (viz storage/README.md) —
                 ne uvnitř backend/ nebo scraper/
/scripts         průřezové skripty (spouští se z rootu) — např. import_scraper_data.py
                 (storage/scraper.db → storage/drivewise.db, viz storage/README.md)
requirements.txt, requirements-dev.txt   Python závislosti pro /backend + /scraper (jeden sdílený
                 venv v rootu; /frontend má vlastní package.json)
```

## Tech stack (závazně, neměnit bez domluvy)

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Zustand (stav), Axios, react-i18next (i18n),
  Vitest + React Testing Library (testy)
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, PostgreSQL (target; SQLite is the
  current default local DB — see `backend/README.md`'s Database section — schema stays
  dual-dialect, don't add Postgres-only DDL without an SQLite equivalent)
- **AI:** Claude API (Anthropic SDK) pro extrakci požadavků a generování vysvětlení
- **Scraping:** Playwright / BeautifulSoup / Scrapy

## Konvence kódu

### Frontend
- Funkční komponenty, žádné class komponenty
- Jeden export na soubor, název souboru = název komponenty (`CarCard.tsx`)
- Props vždy přes explicitní TS interface (`CarCardProps`), žádné `any`
- Styling výhradně přes Tailwind utility třídy, žádné inline styly ani CSS-in-JS
- Sdílené typy (např. `Car`, `Recommendation`, `UserRequirements`) žijí v `/src/types` a musí
  odpovídat Pydantic schématům v `/backend/app/schemas`
- Side-effecty (API volání) jen v `/src/api` nebo custom hooks, nikdy přímo v komponentě
- UI text uživatele je vždy česky, přes `useTranslation()`/`t()` proti `/src/i18n/locales/cs.json`
  — žádné natvrdo napsané řetězce v komponentách. `en.json` existuje jako druhá jazyková sada
  (příprava na vícejazyčnost), ale zatím se nikde nepoužívá (žádný přepínač jazyka)
- Ceny vždy jako `Money` (`{ amount, currency }`), formátované přes `formatMoney()`
  (`src/utils/money.ts`) — currency je `'CZK'`, nikdy natvrdo `$`/`Kč` v textu

### Backend
- Všechny endpointy typované přes Pydantic, žádné volné dict odpovědi
- Business logika mimo route handlery – handler jen volá service vrstvu
- Přístup k Claude API pouze přes `/app/ai` modul, nikde jinde v kódu

### Testy
- Ke každé nové komponentě/endpointu vznikne aspoň smoke test (render / 200 response)
- Testy spouštět a musí procházet před tím, než je úkol označen za hotový

### Git
- Commit messages v angličtině, konvence `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- Malé, tematické commity – ne jeden commit na celou feature

## Jak zadávat úkoly agentovi (doporučený postup)

1. Jeden úkol = jedna komponenta / jeden endpoint / jeden logický celek
2. Po dokončení nechat agenta spustit dev server / testy a ukázat výstup
3. Review probíhá po celcích, ne po jednotlivých řádcích

## API kontrakt (zdroj pravdy)

Aktuální request/response tvary jsou v `/doc/api-contract.md` — toto je zdroj pravdy, existuje a
je aktuální; `frontend/src/types` a `backend/app/schemas` mu musí odpovídat.

## Design tokeny

Barvy, typografie a spacing viz `/doc/design-tokens.md`.

## Co agent nemá dělat bez domluvy

- Neměnit zvolený tech stack (např. nepřidávat Redux vedle Zustand, nepřepisovat na Vue)
- Nezasahovat do `/scraper` při práci na frontendu a naopak
- Negenerovat mock data přímo do produkčního kódu – mock vrstva patří do `/frontend/src/api/mock`
