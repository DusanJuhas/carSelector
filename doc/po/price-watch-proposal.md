# Hlídání cen: poklesy a akční ceny od dealerů

*Návrh ze dne 24. 10. 2026, zatím bez implementace*

## Shrnutí

Pokles ceníkové ceny umí DriveWise hlídat už s dnešními daty. Na akční ceny od dealerů potřebuje nový zdroj dat. Upozornění bych dělal v aplikaci hned a e-mail přidal, až bude ověřená doména v Resendu (viz `user-registration-analysis.md` a `vlastni-domena-spf-dkim.md`).

Návrh má tři vrstvy: zdroje cen, detekci změn při importu a doručení upozornění.

## 1. Odkud se ceny berou

| Zdroj | Stav | Co zachytí |
|---|---|---|
| **Ceníky výrobců** (scraper, pak `scripts/import_scraper_data.py`) | existuje | snížení ceníkové ceny, akční slevu z ceníku (`prices.discount_amount`), nejnižší cenu za 30 dní (`prices.lowest_price_30d`) |
| **Skladové vozy na webech výrobců** (vyhledávače skladových vozů u dealerů) | nový scraper | konkrétní auta u konkrétních dealerů se slevou |
| **XML feedy od dealerů** (partnerství) | nový import | akce a sklad přímo od dealera, právně nejčistší cesta |
| **Inzertní portály** (Sauto, TipCars) | nedoporučuji | podmínky portálů scraping obvykle zakazují |

Ceny v `prices` (`backend/app/models/price.py`) se nikdy nepřepisují: každá změna uzavře starý řádek (`valid_to`) a založí nový. `upsert_price` v importu už rozhoduje, jestli se cena změnila. To je přirozené místo, kde vznikne událost „cena se změnila“.

Data od dealerů jsou nová entita: tabulka dealerů a jejich nabídek s vazbou na `configuration`, cenou, platností akce a odkazem. Sběr těchto dat patří do `/scraper`, takže jde o samostatný úkol (podle `CLAUDE.md` se do `/scraper` nezasahuje při práci na backendu a naopak).

## 2. Co uživatel sleduje

- **Sledovaný model nebo konfigurace:** tlačítko „Hlídat cenu“ na kartě vozu, vedle dnešního srdíčka (`liked_models`). Lze i nabídnout „hlídat všechny oblíbené“.
- **Podmínka:**
  - jakýkoli pokles,
  - pokles alespoň o X % nebo o X Kč,
  - cena pod cílovou částkou,
  - nová akce nebo nová nabídka od dealera.
- **Hlídání podle požadavků** (silná funkce): „Upozorni mě, až se objeví auto splňující moje uložené požadavky do 800 000 Kč.“ Využije `saved_requirements` a existující `RecommendationEngine`.

### Datový model

Nová tabulka `price_watches`:

| Sloupec | Význam |
|---|---|
| `user_id` | kdo sleduje |
| `target_type` | `model`, `configuration` nebo `requirements` (řetězec, ne DB enum, kvůli SQLite i Postgres) |
| `target_id` / `requirements_json` | co sleduje |
| `condition` | `any_drop`, `drop_pct`, `drop_amount`, `below_price`, `promo`, `dealer_offer` |
| `threshold` | hodnota podmínky (procenta nebo `Money`) |
| `channels` | `in_app`, `email`, `push` |
| `active`, `created_at`, `last_notified_at` | stav a omezení frekvence |

## 3. Jak se změny vyhodnocují

```
import ceníků / dealerských dat
      ↓
price_events      (jednou na změnu: configuration, stará → nová cena, typ: drop | promo | dealer_offer)
      ↓  vyhodnocení proti price_watches
notifications     (jednou na uživatele a událost, unique (watch_id, event_id) → žádné duplicity)
      ↓
doručení: v aplikaci hned, e-mail okamžitě nebo jako denní souhrn
```

- **`price_events`** vzniká jednou na změnu ceny, nezávisle na tom, kolik lidí ji sleduje. Slouží zároveň jako historie pro graf vývoje ceny.
- **`notifications`**: `user_id`, `event_id`, `watch_id`, `created_at`, `read_at`, `emailed_at`. Unikátní dvojice `(watch_id, event_id)` brání duplicitám při opakovaném importu.
- **Spuštění:** na konci importu, tedy ze stejného místa, odkud admin konzole (`backend/app/ui/admin.py`) dnes import pouští. Na Renderu free plánu nejsou cron joby zdarma a web služba po nečinnosti usíná. Plánované spouštění by proto šlo přes externí cron, třeba GitHub Actions cron, který zavolá chráněný endpoint.
- **Ochrana proti falešným poplachům:** chyba parseru může vypadat jako dramatický pokles (viz oprava ceny Fordu v `0.3.11`, kdy se dvě ceny slepily do jedné). Pokles nad rozumný práh, například 30 %, by měl jít nejdřív adminovi ke kontrole, ne rovnou uživatelům.

## 4. Jak uživatele upozornit

| Kanál | Výhody | Nevýhody | Infrastruktura mimo DriveWise |
|---|---|---|---|
| **V aplikaci:** zvonek s počtem nepřečtených v hlavičce, panel upozornění, odkaz na vůz s grafem vývoje ceny | jednoduché, spolehlivé, bez externích služeb | uživatel ho uvidí až při návštěvě | žádná |
| **E-mail:** okamžitý, nebo denní či týdenní souhrn | dosáhne na uživatele mimo aplikaci | dnes nefunguje (Resend sandbox doručuje jen adminovi); potřeba odkaz na odhlášení a hlavičku `List-Unsubscribe` | ověřená doména v Resendu nebo jiný SMTP poskytovatel |
| **Web push** (notifikace prohlížeče) | okamžité, bez e-mailu, funguje i u účtů bez e-mailu | service worker v NiceGUI, souhlas v prohlížeči, na iOS jen u webové aplikace přidané na plochu | žádná služba; jen VAPID klíče a knihovna `pywebpush` |

### Doporučené pořadí

1. **Fáze 1:** upozornění v aplikaci plus hlídání poklesu ceníkových cen. Žádná nová infrastruktura.
2. **Fáze 2:** e-mail jako denní souhrn, výchozí volba proti zahlcení, s okamžitým e-mailem jako možností. Podmínkou je vyřešené doručování e-mailů.
3. **Fáze 3:** data od dealerů a případně web push.

Web push stojí za zvážení, pokud se projekt rozhodne pro přihlašování bez e-mailu (viz `login-without-email-alternatives.md`). Jinak by takoví uživatelé mimo aplikaci žádná upozornění nedostali.

## 5. Na co nezapomenout

- **Nastavení uživatele:** kanály, frekvence souhrnu, tiché hodiny, jedno tlačítko pro vypnutí všeho.
- **Právo:** upozornění, o které si uživatel sám požádal, je provozní sdělení. Jakmile ale e-mail obsahuje propagaci dealera, může jít o obchodní sdělení (zákon č. 480/2004 Sb.), které vyžaduje souhlas a odhlášení. Doporučuji nechat ověřit.
- **Transparentnost:** u každé ceny uvést zdroj a datum (máme `source_document`) a rozlišit, jestli jde o ceník výrobce, nebo nabídku dealera.
- **i18n:** texty upozornění v `STRINGS` i `STRINGS_EN`. Jazyk e-mailu se musí uložit k uživateli, protože vyhodnocení běží mimo prohlížeč (stejně jako dnes `use_language()` u kódu v `run.io_bound`).
- **Ceny jako `Money`:** částky v upozorněních formátovat přes `format_money()`, nikdy natvrdo `Kč`.
