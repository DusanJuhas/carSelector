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
/backend         FastAPI aplikace + UI (jeden proces, jeden Python balíček)
  /app
    /api         REST endpointy
    /services    business logika, recommendation engine
    /ai          integrace Claude API (extrakce požadavků, vysvětlení doporučení)
    /models      SQLAlchemy modely
    /schemas     Pydantic schémata (request/response)
    /ui          UI vrstva (NiceGUI, mountnutá na stejnou FastAPI app v app/main.py) — volá
                 service vrstvu přímo (in-process), ne přes HTTP
      /components  jedna obrazovková sekce = jeden soubor + jedna funkce (žádný routing,
                   jedna stránka — viz pages.py)
      state.py     per-connection stav (ConversationState/CatalogState dataclasses) — NiceGUI dává
                   každému browser připojení vlastní volání pages.index(), takže lokální
                   proměnné/uzávěry jsou už samy o sobě per-connection, žádný globální store netřeba
      i18n.py, money.py, sort.py, styles.py   pomocné moduly (viz jejich docstringy)
/scraper         samostatná Python služba pro sběr dat o vozidlech
/doc             architektura, API kontrakty, poznámky (viz doc/README.md pro přehled)
/storage         všechny lokální DB soubory + PDF kopie pro /backend a /scraper (viz storage/README.md) —
                 ne uvnitř backend/ nebo scraper/
/scripts         průřezové skripty (spouští se z rootu) — např. import_scraper_data.py
                 (storage/scraper.db → storage/drivewise.db, viz storage/README.md)
requirements.txt, requirements-dev.txt   Python závislosti pro /backend (včetně UI) + /scraper —
                 jeden sdílený venv v rootu, žádný Node.js/npm v repozitáři
```

## Tech stack (závazně, neměnit bez domluvy)

- **UI:** NiceGUI (Python), mountnutá přímo na FastAPI app (`ui.run_with`) — žádný samostatný
  frontend proces, žádný Node.js/npm. Stylování přes Tailwind utility třídy (NiceGUI je má
  vestavěné), design tokeny viz `doc/design-tokens.md`
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, PostgreSQL (target; SQLite is the
  current default local DB — see `backend/README.md`'s Database section — schema stays
  dual-dialect, don't add Postgres-only DDL without an SQLite equivalent)
- **AI:** Claude API (Anthropic SDK, výchozí) nebo Groq, volitelné přes `AI_PROVIDER` - obojí za
  jedním rozhraním `LlmClient` (`app/ai/llm.py`) - pro extrakci požadavků a generování vysvětlení
- **Scraping:** Playwright / BeautifulSoup / Scrapy
- **Testy:** pytest (backend i UI — UI testy v `backend/tests/ui/`, viz `backend/README.md`)

## Konvence kódu

Platí jednotně pro celý `/backend` (API, services, AI vrstva, i UI) — viz
`.claude/skills/drivewise-architecture/SKILL.md`'s "Code style" sekci pro OOP/docstring konvenci.
UI vrstva se řídí stejnými pravidly jako zbytek Pythonu níže, ne zvláštní výjimkou (dokud šlo o
React, měla frontend vrstva vlastní konvence — ty teď odpadají, protože UI je Python jako všechno
ostatní):

- Sdílené typy jsou Pydantic modely v `/backend/app/schemas` — UI vrstva je konzumuje přímo
  (žádný zvláštní DTO/wire-format překlad, na rozdíl od bývalého `frontend/src/types`)
- Side-effecty (DB/service volání) v UI vrstvě jdou přes `app/ui/db.py`'s `get_session()` +
  `nicegui.run.io_bound`, nikdy přímo synchronně v event handleru (viz `app/ui/state.py`)
- UI text uživatele je vždy česky, přes `t()`/`t_count()` proti `app/ui/i18n.py`'s `STRINGS`
  slovníku — žádné natvrdo napsané řetězce v komponentách
- Ceny vždy jako `Money` (`{ amount, currency }`), formátované přes `format_money()`
  (`app/ui/money.py`) — currency je `'CZK'`, nikdy natvrdo `$`/`Kč` v textu

### Backend (API, services, AI vrstva)
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

Aktuální request/response tvary jsou v `/doc/api-contract.md` — toto je zdroj pravdy pro REST API
`/api/*` (existuje a je aktuální, zůstává v platnosti pro budoucí klienty mimo tuto appku);
`backend/app/schemas` mu musí odpovídat. UI vrstva (`app/ui/`) konzumuje tyto Pydantic modely přímo
in-process, ne přes `/api/*`, takže na ni se tato "musí odpovídat" věta nevztahuje.

## Design tokeny

Barvy, typografie a spacing viz `/doc/design-tokens.md`.

## Co agent nemá dělat bez domluvy

- Neměnit zvolený tech stack (např. nepřepisovat UI vrstvu na jiný framework, nepřidávat Node.js)
- Nezasahovat do `/scraper` při práci na UI/backendu a naopak
- Negenerovat mock data přímo do produkčního kódu
