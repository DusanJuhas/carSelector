# Car Selector — Brainstorming nových featur (2026-09-24)

Výstup brainstormingu. Obsahuje jen **přijaté** návrhy; zamítnuté jsou pro úplnost vypsané
na konci. Navazuje na [MVP.md](./MVP.md) a [Version2.md](./Version2.md). Z Version2 už je hotová
historie cen, ingestion pipeline (scraper + import) a přihlášení.

Odhad rozsahu: **S** = do dne, **M** = pár dní, **L** = týden a víc.

## Přehled

| # | Featura | Oblast | Rozsah | Závisí na | Stav |
|---|---|---|---|---|---|
| 1 | Porovnání vozů | Rozhodování | M | — | ❌ |
| 2 | Kalkulačka TCO | Rozhodování | M | kvalita dat o spotřebě | ❌ |
| 3 | Oblíbené vozy | Rozhodování | S–M | přihlášení (hotové) | ✅ (0.2.39) |
| 4 | Chat k jednomu vozu | AI | M | — | ❌ |
| 5 | Sdílení a PDF export | AI / výstup | M | — | ❌ |
| 6 | Hlídač cen a akcí | Data | M | 3 (Oblíbené), 8 (Plánovaný scraping) | ❌ |
| 7 | Fotky vozů | Data | L | — | ❌ |
| 8 | Plánovaný scraping | Data | M | persistentní DB na nasazení | ❌ |
| 9 | Analytika poptávky | Platforma | M | — | ❌ |

✅ = hotovo, ❌ = nehotovo.

---

## 1. Porovnání vozů

**Co:** uživatel označí 2–4 vozy (zaškrtnutím na kartě) a otevře porovnání vedle sebe.
Tabulka: cena, výkon, pohon, palivo, spotřeba, emise, kategorie a standardní výbava. Rozdíly jsou
zvýrazněné, shodné řádky jdou skrýt. Nahoře je krátké AI shrnutí „který z nich a proč“, podle
požadavků z konverzace.

**Proč:** poslední krok rozhodování dnes chybí. Uživatel musí přepínat mezi detaily. Ve
Version2.md je to jako odložená funkce.

**Návaznost:** `vehicle_detail_modal.py` už načítá kompletní detail vozu a porovnání ho může
znovu použít. Shrnutí jde přes `app/ai/explanation_generator.py`. Na mobilu (viz 0.2.38)
horizontálně posuvné sloupce, nebo režim „2 vozy“.

**Otevřené otázky:** přežije výběr k porovnání restart relace? Stačí uložit do
`app.storage.user`?

## 2. Kalkulačka TCO (celkové náklady vlastnictví)

**Co:** odhad nákladů za 3–5 let: pořizovací cena (volitelně minus zůstatková hodnota), palivo
nebo elektřina podle spotřeby a ročního nájezdu, servis a pojištění paušálem podle kategorie.
Výsledek v Kč/měsíc na kartě i v detailu, plus řazení „podle měsíčních nákladů“.

**Proč:** levnější benzín a dražší elektromobil se po 5 letech často vymění. Tohle je přesně
otázka, kterou si zákazník klade.

**Návaznost:** spotřeba je v `powertrains`. Roční nájezd jde vytáhnout z konverzace (nové pole
v `StructuredRequirements`), jinak default. Ceny energií a paušály jsou konfigurace, ne natvrdo
v kódu. Výpočet patří do service vrstvy (`app/services/`), UI jen zobrazuje. Částky jako `Money`.

**Rizika:** importovaná data často spotřebu nemají (viz docstring
`scripts/import_scraper_data.py`). U takových vozů TCO nezobrazovat a netvářit se přesně.

## 3. Oblíbené vozy — ✅ hotovo (0.2.39)

**Co je hotové:** srdíčko (like) na každé kartě ve výsledcích.

- **Like platí pro model, ne pro konkrétní vůz.** Když dáte like jedné kartě VW Tiguan,
  vyplní se srdíčko na všech kartách Tiguanu (všechny výbavy a motory). Like vyjadřuje vkus
  pro auto samotné, ne pro jednu výbavu.
- **Přihlášený uživatel:** like se ukládá do účtu a po návratu na web ho uvidí znovu.
- **Nepřihlášený uživatel:** like platí do obnovení stránky. Když se pak přihlásí, jeho liky
  se přidají k těm z účtu. Po odhlášení srdíčka zmizí.
- **Vliv na vyhledávání:** like jen mění pořadí, nikdy žádný vůz neskryje.
  - Při hledání přes chat nebo průvodce dostane likenutý model +15 bodů ke shodě a ostatní
    modely stejné značky +5.
  - V procházení katalogu s řazením „Doporučeno“ jsou likenuté modely nahoře. Řazení podle ceny
    a abecedy like ignoruje.
  - Like se projeví až při dalším hledání nebo změně filtru. Karty na obrazovce se po
    kliknutí nepřeskládají.

**Implementace:** tabulka `liked_models` (migrace `0031bdd2429f`),
`app/services/liked_models.py`, `LikedModelsState` v `app/ui/state.py`, `LikeButtons`
v `app/ui/components/results_grid.py`. Do `VehicleSummary` přibylo pole `model_id`.

**Co z původního návrhu zbývá (případně jako navazující úkol):**

- **Srdíčko v detailu vozu:** zatím je jen na kartě.
- **Seznam „Moje oblíbené“:** samostatný přehled likenutých modelů, dnes je poznáte jen podle
  srdíček ve výsledcích.
- **Poznámka k vozu:** volitelný text u oblíbeného modelu.
- **Výzva k přihlášení u anonyma:** dnes like funguje i bez přihlášení, jen se neuloží.
  Nápověda typu „Přihlaste se, ať o oblíbené nepřijdete“ zatím chybí.

## 4. Chat k jednomu vozu

**Co:** v detailu vozu pole „Zeptejte se na tento vůz“. Příklady: „Má vyhřívaný volant ve
standardu?“, „Kolik stojí tažné zařízení?“. AI odpovídá **jen z dat daného vozu** (výbava,
příplatky, powertrain). Když údaj chybí, řekne „v ceníku to není“.

**Proč:** detail je dlouhý seznam výbavy, dotaz je rychlejší než hledání.

**Návaznost:** nová schopnost v `app/ai/` přes rozhraní `LlmClient`. Kontext se sestaví z
detailu vozu, stejně jako to dělá `explanation_generator`. Nutný test, že model nevymýšlí údaje
mimo dodaná data.

## 5. Sdílení a PDF export

**Co:** tlačítko „Sdílet výsledek“ vytvoří odkaz (read-only snapshot: požadavky, top N vozů,
AI vysvětlení) a nabídne stažení PDF se stejným obsahem.

**Proč:** o autě se rozhoduje v rodině a výsledek se nosí do autosalonu.

**Návaznost:** snapshot jako nová tabulka s náhodným ID (ne sekvenčním) a expirací. PDF se
generuje server-side v Pythonu (bez Node.js, viz tech stack). Sdílený odkaz nesmí prozradit
e-mail ani identitu autora.

## 6. Hlídač cen a akcí

**Co:** u oblíbeného vozu (#3) zapnout hlídání. Když import zaznamená nižší cenu nebo novou
akci, uživatel dostane e-mail („Škoda Kodiaq Style: −35 000 Kč od 1. 10.“). Hlídání jde
vypnout jedním kliknutím z e-mailu.

**Proč:** důvod se k aplikaci vracet. Využívá data, která už máme.

**Návaznost:** append-only historie cen (`prices` s platností) a `app/services/mailer.py`
existují. Spouští se po importu (#8). Chce to rate-limit a souhrnný e-mail místo jednoho e-mailu
za každou změnu.

**Otevřená otázka (po dokončení #3):** oblíbené jsou uložené po *modelech*, ceny ale po
konfiguracích (výbava × motor). Hlídač tedy buď upozorní na změnu u kterékoli konfigurace
likenutého modelu (jednodušší, ale víc e-mailů), nebo si uživatel u modelu vybere konkrétní
konfigurace ke hlídání.

## 7. Fotky vozů

**Co:** nahradit šrafovaný placeholder skutečnou fotkou, ideálně podle modelu a barvy.
Fallback je fotka modelu, pak placeholder.

**Proč:** výrazně zvedne důvěryhodnost a čitelnost výsledků.

**Návaznost / rizika:** největší otázka je **zdroj a licence**. Fotky výrobců jsou chráněné,
takže potřebujeme press/media kit s licencí, nebo ruční upload v adminu. Soubory do úložiště
(ne blob v DB, viz Version2.md „Object storage“), v DB jen reference. Vyžaduje persistentní
úložiště i na nasazení.

## 8. Plánovaný scraping

**Co:** automatický běh scraperu a importu (např. týdně). V adminu report posledního běhu:
nové modely, změny cen, chyby parserů. E-mail adminovi při selhání.

**Proč:** dnes se katalog aktualizuje jen ručně přes `/admin`. Je to i předpoklad pro #6.

**Návaznost:** admin konzole už spouští scraper i import jako subprocess (`app/ui/admin.py`).
Plánovač je buď cron na hostingu (Render Cron Job), nebo interní scheduler. **Podmínka:**
persistentní DB, jinak se výsledek při restartu ztratí (viz
[../db/troubleshooting-few-models.md](../db/troubleshooting-few-models.md)).

## 9. Analytika poptávky

**Co:** anonymní agregace toho, co lidé hledají: rozložení rozpočtů, požadované pohony a
kategorie, nejčastější požadavky a hlavně **neuspokojené dotazy** (0 výsledků). Zobrazuje se v
admin dashboardu po týdnech.

**Proč:** ukazuje, která data v katalogu chybí. Do budoucna jde o potenciální produkt pro
dealery.

**Návaznost:** zdrojem jsou `StructuredRequirements` po každém doporučení, ukládané bez vazby
na uživatele (bez e-mailu, IP, volného textu zpráv). Grafy v admin stránce.

**Pozor:** nutné GDPR ošetření: agregovat, neukládat volný text, informovat v zásadách.

---

## Doporučené pořadí

1. **#8 Plánovaný scraping**: předpokladem je persistentní DB. Odblokuje #6 a vyřeší
   aktuálnost dat.
2. ~~**#3 Oblíbené vozy**: malé a je základem pro #6.~~ Hotovo v 0.2.39.
3. **#1 Porovnání vozů**: největší přínos pro rozhodování.
4. **#6 Hlídač cen**: staví na #3 a #8.
5. **#4 Chat k vozu** a **#2 TCO**: AI a výpočetní vrstva, nezávislé.
6. **#5 Sdílení/PDF**, **#9 Analytika**.
7. **#7 Fotky**: až bude vyřešená licence a úložiště.

## Zamítnuté návrhy (pro historii)

Konfigurátor ceny (barva + výbava → cena), „Proč ne?“ a téměř shody, hlasové zadávání,
dashboard kvality dat, kalkulačka financování/leasingu, anglická verze UI, Render blueprint +
Postgres.
