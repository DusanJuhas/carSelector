# Diagnostika: v UI jsou jen 4 modely (nasazení z klonu, např. Render)

Situace: někdo naklonoval repozitář, nasadil ho (např. na https://carselector.onrender.com) a v UI
vidí jen 4 vozy.

**Nejpravděpodobnější příčina:** v katalogu je jen demo seed a chybí import scraperových dat.
`python -m app.db.seed` vloží 2 modely (Mazda CX-5 a VW Tiguan), každý ve 2 výbavách, a to jsou
přesně 4 karty v UI. Plně naplněný katalog má zhruba 169 modelů a 1354 konfigurací.

`storage/drivewise.db` je v `.gitignore`, takže se do klonu nedostane. Klon obsahuje jen surová
data (`storage/scraper.db`, zhruba 1534 variant) a ta se do katalogu musí zvlášť naimportovat
skriptem `scripts/import_scraper_data.py` (viz `storage/README.md`).

## 1. Je v katalogu jen seed?

- **Titulek výsledků:** bez chatu by měl být nadpis „N vozů v katalogu“. Pokud tam je 4 a jde o
  Mazdu CX-5 Prime-Line/Centre-Line a Tiguan People/R-Line People, je to čistý seed.
- **Zúžení přes AI:** pokud nadpis zní „4 shody pro vás“, výsledky zúžil chat nebo průvodce. Pak
  to není chyba dat. Stačí kliknout na Restartovat, případně zkontrolovat filtry Výrobce, Druh
  motoru a Pohon.

## 2. Proběhl import scraperových dat?

- **Start/build command:** podívejte se, co v Render dashboardu (Settings → Build & Start Command)
  skutečně běží. Nejspíš tam je jen `alembic upgrade head` a `python -m app.db.seed`. Chybí
  `python scripts/import_scraper_data.py`, který se spouští z rootu repozitáře.
- **Deploy logy:** projděte je. Import na konci vypisuje souhrn (počty značek, modelů,
  konfigurací). Když tam souhrn není, import neproběhl.
- **Ruční spuštění přes `/admin`:** import jde spustit i tlačítkem v admin konzoli. Je k tomu
  potřeba nastavit `ADMIN_EMAILS` a funkční odesílání e-mailů (`EMAIL_BACKEND`, `SMTP_*`). S
  výchozím `EMAIL_BACKEND=console` se přihlašovací kód vypíše jen do logu Renderu.

## 3. Přežijí data restart? (nejčastější past na Renderu)

- **Dočasný disk:** Render má dočasný souborový systém. Pokud `DATABASE_URL` není nastavená,
  aplikace používá SQLite v `storage/drivewise.db`. Ta se při každém deployi zahodí a na free
  plánu i při uspání služby. Import provedený ručně přes `/admin` proto po restartu zmizí a zbude
  jen to, co spouští start command, tedy seed.
- **Řešení:** buď Render Postgres a `DATABASE_URL` mezi Environment variables, nebo Persistent
  Disk (placený plán). Druhá možnost je spouštět import v každém start commandu. Je bezpečné ho
  spouštět opakovaně.

## 4. Pokud se používá Postgres

- **Tvar URL:** Render dává URL ve tvaru `postgres://…` nebo `postgresql://…`. `requirements.txt`
  ale instaluje jen driver `psycopg` (verze 3), takže URL musí začínat `postgresql+psycopg://`.
  Kód v `backend/app/core/config.py` ji nepřepisuje. Se špatnou URL by ale aplikace spíš vůbec
  nenastartovala, než aby ukázala 4 modely.
- **Stejná databáze:** ověřte, že import i aplikace míří na stejnou DB, tedy že `DATABASE_URL` je
  nastavená pro start command i pro běžící službu (nebo u jobu, kde import běží).
- **Kontrola přímo v DB** (Render psql) — mělo by to vrátit zhruba 169 a 1354:

  ```sql
  select count(*) from models;
  select count(*) from configurations;
  ```

## 5. Je v klonu `storage/scraper.db` celý?

- **Soubor:** ověřte, že `storage/scraper.db` na Renderu existuje a má zhruba 2,3 MB. Git LFS se
  nepoužívá, takže běžný klon ho obsahuje. Chybět ale může, pokud někdo klonoval fork se změněným
  `.gitignore` nebo nastavil Root Directory na `backend/`.
- **Root Directory:** měl by zůstat prázdný (root repozitáře). Import i admin konzole hledají
  `storage/` a `scripts/` relativně ke kořeni repozitáře.
- **Zkušební běh** ukáže, kolik dat by se naimportovalo, aniž by cokoli zapsal:

  ```bash
  python scripts/import_scraper_data.py --dry-run
  ```

## 6. Drobnosti

- **Proměnné prostředí:** `AI_PROVIDER` a `ANTHROPIC_API_KEY`/`GROQ_API_KEY` na počet vozů
  v katalogu vliv nemají, ovlivňují jen chat. `NICEGUI_STORAGE_SECRET` a `AUTH_SECRET` by na
  veřejném nasazení neměly zůstat na výchozí hodnotě.
- **Po změně env proměnných:** udělejte Manual Deploy → „Clear build cache & deploy“, ať běží
  aktuální start command.

## Nejrychlejší ověření

V Render Shellu (nebo v logu) spustit:

```bash
python scripts/import_scraper_data.py
```

a obnovit stránku. Když se počet vozů zvýší a po dalším deployi zase spadne na 4, je to bod 3,
tedy dočasný disk.
