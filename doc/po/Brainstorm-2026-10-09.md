# Car Selector — Brainstorming nových featur (aktualizace 2026-10-09)

Aktualizovaná verze [Brainstorm-2026-09.md](./Brainstorm-2026-09.md) (brainstorming z 2026-09-24).
Návrhy zůstávají stejné, aktualizovaný je **stav hotových funkcí** k verzi 0.3.2. Přibyla sekce
[Hotovo mimo původní seznam](#hotovo-mimo-původní-seznam) a nové doporučené pořadí. Navazuje na
[MVP.md](./MVP.md) a [Version2.md](./Version2.md). Z Version2 už je hotová historie cen, ingestion
pipeline (scraper + import), přihlášení a porovnání vozů.

Odhad rozsahu: **S** = do dne, **M** = pár dní, **L** = týden a víc.

## Přehled

| # | Featura | Oblast | Rozsah | Závisí na | Stav |
|---|---|---|---|---|---|
| 1 | Porovnání vozů | Rozhodování | M | — | ✅ (0.2.51), bez AI shrnutí |
| 2 | Kalkulačka TCO | Rozhodování | M | kvalita dat o spotřebě | ❌ |
| 3 | Oblíbené vozy | Rozhodování | S–M | přihlášení (hotové) | ✅ (0.2.39) |
| 4 | Chat k jednomu vozu | AI | M | — | ❌ |
| 5 | Sdílení a PDF export | AI / výstup | M | — | ✅ (0.2.40 PDF, 0.2.42 sdílení A + F, 0.2.51 porovnání) |
| 6 | Hlídač cen a akcí | Data | M | 3 (Oblíbené), 8 (Plánovaný scraping) | ❌ |
| 7 | Fotky vozů | Data | L | — | ❌ |
| 8 | Plánovaný scraping | Data | M | persistentní DB na nasazení | ❌ (připraveno: průběh jobů v adminu, 0.2.49) |
| 9 | Analytika poptávky | Platforma | M | — | ❌ |

✅ = hotovo, ❌ = nehotovo.

Mimo původní seznam přibylo: **články a role autora** (0.3.0, 0.3.2), **anglická verze UI**
(0.2.47, původně zamítnutá), **záznam komunikace s AI** (0.2.44) a **záložka „Ovládání“ s průběhem
jobů** (0.2.48–0.2.49). Podrobnosti jsou v [sekci níže](#hotovo-mimo-původní-seznam).

---

## 1. Porovnání vozů — ✅ hotovo (0.2.51)

**Původní návrh:** uživatel označí 2–4 vozy a otevře porovnání vedle sebe. Rozdíly jsou
zvýrazněné, shodné řádky jdou skrýt. Nahoře je AI shrnutí „který z nich a proč“.

**Proč:** na konci výběru obvykle zbývá jen několik málo kandidátů, na které stojí za to se
podívat detailněji. Dřív musel uživatel přepínat mezi detaily.

**Co je hotové:**

- Zaškrtávátko „Porovnat“ na každé kartě. Vybrané vozy se sbírají v liště pod výsledky
  („Porovnat (n)“, odebrání jednotlivých vozů, „Vymazat“).
- Dialog porovnání: jeden sloupec na vůz. Sekce přehled (cena, AI skóre shody, pokud existuje
  doporučení), motor a pohon, výbava, barvy. Nejlepší hodnota v řádku je zvýrazněná. Přepínač
  „Zobrazit jen rozdíly“ je ve výchozím stavu zapnutý.
- Výbava se u vozů jedné značky páruje řádek po řádku („✓ v ceně“ / příplatek / „—“). U různých
  značek má každý vůz vlastní seznam, protože každá značka pojmenovává výbavu jinak.
- Hlavičky vozů a popisky řádků zůstávají při posouvání připnuté. Na mobilu jsou vidět dva vozy
  najednou.
- Z detailu vozu „Přidat k porovnání“ a „Porovnat výbavy“: výběr výbavových stupňů jednoho
  modelu.
- „Sdílet“ (přes existující odkaz z #5) a „Stáhnout PDF“ (A4 na šířku, respektuje „jen
  rozdíly“).

**Odpověď na otevřenou otázku:** výběr k porovnání se pamatuje v prohlížeči (`CompareState` v
`app/ui/state.py`, klíč `compare_selection`), přežije tedy obnovení stránky.

**Implementace:** `app/ui/compare.py` (řádky porovnání, sdílené s PDF),
`app/ui/components/compare_dialog.py`, `catalog.list_trim_alternatives`.

**Co zbývá (případně jako navazující úkol):**

- **AI shrnutí „který z nich a proč“** podle požadavků z konverzace, přes
  `app/ai/explanation_generator.py`. Dnes porovnání ukazuje jen AI skóre shody.

## 2. Kalkulačka TCO (celkové náklady vlastnictví)

**Co:** odhad nákladů za 3–5 let: pořizovací cena (volitelně minus zůstatková hodnota), palivo
nebo elektřina podle spotřeby a ročního nájezdu, servis a pojištění paušálem podle kategorie.
Výsledek v Kč/měsíc na kartě i v detailu, plus řazení „podle měsíčních nákladů“.

**Proč:** levnější benzín a dražší elektromobil se po 5 letech často vymění. Tohle je přesně
otázka, kterou si zákazník klade.

**Návaznost:** spotřeba je v `powertrains`. Roční nájezd už průvodce sbírá (otázka 7, výchozí
hodnota 15 000 km od 0.2.43), z konverzace by šel vytáhnout jako nové pole v
`StructuredRequirements`, jinak default. Ceny energií a paušály jsou konfigurace, ne natvrdo v
kódu. Výpočet patří do service vrstvy (`app/services/`), UI jen zobrazuje. Částky jako `Money`.
Nově by se TCO hodilo i jako řádek v porovnání vozů (#1).

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
  srdíček ve výsledcích. Nabízí se tlačítko „Porovnat oblíbené“ (#1).
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
mimo dodaná data. Ladění usnadní záznam komunikace s AI v adminu (0.2.44). Odpovídat musí v
jazyce UI (0.2.47).

## 5. Sdílení a PDF export — ✅ hotovo (varianty A + F)

**Co:** tlačítko „Sdílet výsledek“ vytvoří odkaz (read-only snapshot: požadavky, top N vozů,
AI vysvětlení) a nabídne stažení PDF se stejným obsahem.

**Proč:** o autě se rozhoduje v rodině a výsledek se nosí do autosalonu.

**Návaznost:** snapshot jako nová tabulka s náhodným ID (ne sekvenčním) a expirací. PDF se
generuje server-side v Pythonu (bez Node.js, viz tech stack). Sdílený odkaz nesmí prozradit
e-mail ani identitu autora.

**Stav:** PDF export jednoho vozu hotový (0.2.40). Sdílení variantami A + F hotové (0.2.42).
Porovnání vozů (0.2.51) jde sdílet stejným odkazem a stáhnout jako PDF. Zbývá: C („Pokračuj
odsud“), D (společný seznam), přehled „Moje sdílení“ se zrušením odkazu.

### Varianty sdílení (rozpracováno 2026-09-25)

Co se dá sdílet: konkrétní vůz (detail/PDF), výsledek hledání (požadavky + top N vozů +
vysvětlení), porovnání vozů, oblíbené modely, požadavky jako výchozí bod pro další hledání.

| | Varianta | Pro koho | Rozsah | Rozhodnutí |
|---|---|---|---|---|
| A | Odkaz jen pro čtení (snapshot) | kdokoli, bez účtu | S–M | ✅ hotovo (0.2.42) |
| B | Živý odkaz na seznam | kdokoli | M | ❌ pokryje ho D |
| C | „Pokračuj odsud“ | kdokoli, bez účtu | S | později, jako tlačítko na stránce z A |
| D | Společný seznam („garáž“) | účty, pozvánka e-mailem | L | až po #6 Hlídač cen |
| E | Odeslat e-mailem z aplikace | kdokoli | S–M | jen při poptávce |
| F | Sdílení přes systém telefonu + QR kód | kdokoli | XS–S | ✅ hotovo (0.2.42) |

- **A) Snapshot:** tlačítko „Sdílet“ uloží zmrazenou kopii (požadavky, vozy a ceny k danému
  dni, vysvětlení) a vrátí odkaz `/s/<token>`. Ceny jsou zmrazené i s datem, což se hodí do
  autosalonu. Snapshot má expiraci.
- **B) Živý odkaz:** ukazuje aktuální stav (např. oblíbené). Je vždy aktuální, ale autor musí
  vědět, že sdílí průběžně, a potřebuje přehled odkazů s možností je zrušit.
- **C) „Pokračuj odsud“:** odkaz předvyplní požadavky odesílatele do vlastní relace příjemce,
  který pak hledá dál. Originál se nemění.
- **D) Společný seznam:** více členů, hlasování a komentáře. Pozvánka e-mailem zároveň založí
  účet (přihlášení kódem). Vyžaduje nový datový model (seznamy, členství) a řešení GDPR u
  pozvaných. Inspirací může být sdílení článků vybraným uživatelům podle e-mailu (0.3.0), které
  funguje i pro lidi bez účtu.
- **E) E-mail z aplikace:** hrozí, že se aplikace stane rozesílačem spamu. Je potřeba omezit
  počet odeslání a adresu příjemce neukládat.
- **F) Systémové sdílení + QR:** na mobilu nativní nabídka „Sdílet“ (Web Share API), jinak
  kopírování odkazu. QR kód pro ukázání v autosalonu. Obsahem je odkaz z A.

Platí pro všechny varianty: odkaz neprozradí autora (náhodný token, žádný e-mail), stránka má
`noindex`, expirace (30 dní), vytvořit snapshot může i nepřihlášený uživatel.

## 6. Hlídač cen a akcí

**Co:** u oblíbeného vozu (#3) zapnout hlídání. Když import zaznamená nižší cenu nebo novou
akci, uživatel dostane e-mail („Škoda Kodiaq Style: −35 000 Kč od 1. 10.“). Hlídání jde
vypnout jedním kliknutím z e-mailu.

**Proč:** důvod se k aplikaci vracet. Využívá data, která už máme.

**Návaznost:** append-only historie cen (`prices` s platností) a `app/services/mailer.py`
existují. Spouští se po importu (#8). Chce to rate-limit a souhrnný e-mail místo jednoho e-mailu
za každou změnu. E-mail by měl respektovat jazyk uživatele (UI je od 0.2.47 i anglicky).

**Otevřená otázka (po dokončení #3):** oblíbené jsou uložené po *modelech*, ceny ale po
konfiguracích (výbava × motor). Hlídač tedy buď upozorní na změnu u kterékoli konfigurace
likenutého modelu (jednodušší, ale víc e-mailů), nebo si uživatel u modelu vybere konkrétní
konfigurace ke hlídání.

## 7. Fotky vozů

**Co:** nahradit šrafovaný placeholder skutečnou fotkou, ideálně podle modelu a barvy.
Fallback je fotka modelu, pak placeholder.

**Proč:** výrazně zvedne důvěryhodnost a čitelnost výsledků. Nově i v porovnání vozů (#1).

**Návaznost / rizika:** největší otázka je **zdroj a licence**. Fotky výrobců jsou chráněné,
takže potřebujeme press/media kit s licencí, nebo ruční upload v adminu. Soubory do úložiště
(ne blob v DB, viz Version2.md „Object storage“), v DB jen reference. Vyžaduje persistentní
úložiště i na nasazení. Stejné úložiště by se hodilo i pro obrázky v článcích, které se dnes
vkládají přímo do HTML jako data URL.

## 8. Plánovaný scraping

**Co:** automatický běh scraperu a importu (např. týdně). V adminu report posledního běhu:
nové modely, změny cen, chyby parserů. E-mail adminovi při selhání.

**Proč:** dnes se katalog aktualizuje jen ručně přes `/admin`. Je to i předpoklad pro #6.

**Návaznost:** admin konzole spouští scraper i import jako subprocess, od 0.2.48 v záložce
„Ovládání“. Od 0.2.49 joby hlásí průběh strojově čitelnými řádky `PROGRESS {json}`
(`scraper/progress.py`), pamatují si délku posledního úspěšného běhu a spouštějí se přes
`subprocess.Popen` na jakémkoli event loopu. Opravená je i chyba, kvůli které import pod
`uvicorn --reload` na Windows nikdy nedoběhl. Z toho může report posledního běhu přímo
vycházet. Plánovač je buď cron na hostingu (Render Cron Job), nebo interní scheduler.
**Podmínka:** persistentní DB, jinak se výsledek při restartu ztratí (viz
[../db/troubleshooting-few-models.md](../db/troubleshooting-few-models.md)).

## 9. Analytika poptávky

**Co:** anonymní agregace toho, co lidé hledají: rozložení rozpočtů, požadované pohony a
kategorie, nejčastější požadavky a hlavně **neuspokojené dotazy** (0 výsledků). Zobrazuje se v
admin dashboardu po týdnech.

**Proč:** ukazuje, která data v katalogu chybí. Do budoucna jde o potenciální produkt pro
dealery.

**Návaznost:** zdrojem jsou `StructuredRequirements` po každém doporučení, ukládané bez vazby
na uživatele (bez e-mailu, IP, volného textu zpráv). Grafy v admin stránce (nová záložka vedle
„Data“, „Ovládání“, „AI komunikace“ a „Autoři“).

**Pozor:** nutné GDPR ošetření: agregovat, neukládat volný text, informovat v zásadách.

---

## Hotovo mimo původní seznam

Funkce, které v brainstormingu 2026-09 nebyly (nebo byly zamítnuté), ale mezitím vznikly.

### 10. Články a role autora — ✅ hotovo (0.3.0, 0.3.2)

**Co:** portál článků. Přihlášený uživatel požádá o roli autora („Stát se autorem“),
administrátor žádost schválí nebo zamítne v adminu (záložka „Autoři“). Autor píše ve WYSIWYG
editoru (NiceGUI `ui.editor` / Quasar QEditor) a volí viditelnost: jen já (koncept), vybraní
uživatelé (podle e-mailu, i bez účtu) nebo všichni. Od 0.3.2 může mít článek českou i anglickou
verzi. Když verze v jazyce čtenáře chybí, zobrazí se ta dostupná s upozorněním.

**Proč:** články mohou pomoct s výběrem auta, inspirovat nebo objasnit důvody určitého aspektu
výběru. Zároveň přitahují pozornost k portálu jako takovému. Schvalování adminem je prvek
bezpečnosti a kontroly kvality. Sdílení jen vybraným uživatelům je záměr, protože uživatelé
mohou chtít sdílet informace jen mezi sebou, ne veřejně.

**Implementace:** `app/services/authors.py`, `app/services/articles.py`,
`app/ui/articles_page.py`. Tabulky `author_requests`, `articles`, `article_translations`,
`article_recipients` (migrace `b7d2e8f41a90`, `d5a8c3e1f720`). Manuál pro autory:
[../manuals/article-editing.md](../manuals/article-editing.md).

**Možné navazující kroky:** úložiště pro obrázky místo data URL (viz #7), odkazy z článků na
konkrétní vozy nebo předvyplněné hledání (#5 C), upozornění čtenáři e-mailem, když s ním někdo
článek sdílí, historie verzí článku.

### 11. Anglická verze UI — ✅ hotovo (0.2.47)

**Co:** celé UI v angličtině, včetně odpovědí AI (doplňující otázky, vysvětlení doporučení),
PDF, přihlašovacího e-mailu a admin konzole. Přepínač je v menu účtu a volba se pamatuje v
prohlížeči. Ceny zůstávají v Kč, data katalogu (názvy výbavy, barvy) jsou česky, jak jsou v
ceníku.

**Proč:** prezentace portálu i zahraničním uživatelům. V brainstormingu 2026-09 byla anglická
verze zamítnutá. Rozhodnutí se změnilo.

**Implementace:** `app/ui/i18n.py` (`STRINGS`), `app/ui/i18n_en.py` (`STRINGS_EN`), shodu klíčů
hlídá `tests/ui/test_i18n.py`.

### 12. Záznam komunikace s AI v adminu — ✅ hotovo (0.2.44)

**Co:** záložka „AI komunikace“. U každého volání LLM ukazuje čas, účel, model, dobu trvání,
tokeny, výsledek, kompletní prompt a odpověď (i jako surový JSON). Data jsou jen v paměti
serveru (posledních `LLM_TRACE_MAX_ENTRIES` volání), protože obsahují texty uživatelů.

**Proč:** ladění a budoucí optimalizace počtu použitých tokenů.

**Možné navazující kroky:** souhrn spotřeby tokenů za den/týden (bez textů uživatelů, tedy
ukladatelný), podklad pro rozhodnutí, který model použít pro který účel.

### 13. Záložka „Ovládání“ a průběh jobů — ✅ hotovo (0.2.48, 0.2.49)

**Co:** scraper a import se přesunuly ze záložky „Data“ do „Ovládání“. Ukazují průběh (zdroj,
dokument, značka), uplynulý čas a odhad zbývajícího času. Opravená chyba, kvůli které import
nikdy nedoběhl.

**Proč:** import trvá několik minut, takže možnost sledovat průběh je uživatelsky přívětivější.
Hlavním spouštěčem ale byla chyba, kvůli které import nedobíhal.

### Drobnější hotové změny

- Přeuspořádaná hlavička: vše kolem účtu v jednom menu, na počítači i na mobilu (0.2.50).
- Připnutá hlavička v detailu vozu (0.2.45).
- Oprava chyby 500 při načítání stránky po návratu z adminu (0.2.46).
- Výchozí roční nájezd 15 000 km v průvodci (0.2.43).
- `scripts/fast-run.bat` pro rychlý start bez migrací a importu (0.3.1).

---

## Doporučené pořadí

1. **#8 Plánovaný scraping**: předpokladem je persistentní DB. Odblokuje #6 a vyřeší
   aktuálnost dat. Díky 0.2.48–0.2.49 je jednodušší (průběh a výsledky jobů už existují).
2. ~~**#3 Oblíbené vozy**~~: hotovo v 0.2.39.
3. ~~**#1 Porovnání vozů**~~: hotovo v 0.2.51. Zbývá AI shrnutí jako menší navazující úkol.
4. **#6 Hlídač cen**: staví na #3 a #8.
5. **#4 Chat k vozu** a **#2 TCO**: AI a výpočetní vrstva, nezávislé. TCO by se hodilo i jako
   řádek v porovnání.
6. ~~**#5 Sdílení/PDF**~~: varianty A + F hotové. Zbývá C, D a „Moje sdílení“. **#9 Analytika**.
7. **#7 Fotky**: až bude vyřešená licence a úložiště. Úložiště by sloužilo i obrázkům v článcích.

## Zamítnuté návrhy (pro historii)

Konfigurátor ceny (barva + výbava → cena), „Proč ne?“ a téměř shody, hlasové zadávání,
dashboard kvality dat, kalkulačka financování/leasingu, Render blueprint + Postgres.

Anglická verze UI byla v 2026-09 zamítnutá, ale nakonec je hotová (0.2.47, viz #11).
