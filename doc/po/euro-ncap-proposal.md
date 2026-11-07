# Bezpečnostní hodnocení Euro NCAP

*Návrh ze dne 7. 11. 2026, zatím bez implementace*

## Shrnutí

Doporučuji zobrazovat hodnocení Euro NCAP **ve třech úrovních**:

1. odznak s hvězdičkami na kartě výsledku,
2. detailní panel se čtyřmi dílčími skóre v detailu vozidla,
3. řádky ve srovnání vybraných aut.

Hvězdičky a grafy kreslíme **vlastním designem** podle `doc/design-tokens.md`. Oficiální logo ani grafiku hodnocení Euro NCAP nepřebíráme a vždy přidáme odkaz „Zdroj: Euro NCAP“ na stránku modelu.

Data zpočátku plníme **ručně kurátorovanou tabulkou**, podobně jako fotky v `backend/app/ui/car_photos.py`. Nestahujeme hromadně celou databázi Euro NCAP.

Výchozí stav: v katalogu (`backend/app/models/`) ani ve scraperu zatím žádná bezpečnostní data nejsou.

Pozn.: grafický návrh vznikl jako mockup v konverzaci s agentem. Tento dokument popisuje jeho obsah slovně.

## 1. Co Euro NCAP hodnotí

- **Celkové hodnocení:** 0–5 hvězdiček.
- **Čtyři dílčí oblasti (protokoly do roku 2025), každá v procentech:**
  - Adult occupant, ochrana dospělých posádky,
  - Child occupant, ochrana dětí,
  - Vulnerable road users, ochrana chodců a cyklistů,
  - Safety assist, asistenční systémy.
- **Datum hodnocení:** každé hodnocení nese rok testu. Pravidla se zpřísňují, takže 5★ z roku 2018 není totéž co 5★ z roku 2024. Rok proto zobrazujeme vždy u hvězdiček.
- **Protokoly od roku 2026:** Euro NCAP přechází na novou strukturu oblastí. Detaily je třeba ověřit v aktuálních protokolech na euroncap.com, než zafixujeme UI. Datový model proto nese verzi protokolu a dílčí skóre ukládá obecně (viz kap. 4), aby šly vedle sebe zobrazit oba formáty.

## 2. Platnost hodnocení

- **Délka platnosti:** hodnocení platí **6 let** od roku testu (date stamp).
- **Po šesti letech:** pokud model mezitím nebyl přetestován ani nahrazen, hodnocení vyprší. Nově vyrobené kusy jsou pak vedené jako *unrated*. Vozy vyrobené během platnosti si hodnocení ponechávají.
- **Facelift nebo větší úprava:** během platnosti může Euro NCAP posoudit, zda původní hodnocení stále platí.

Dopad na aplikaci:

- Stav hodnocení **počítáme v kódu** z roku testu, neukládáme ho:
  - `valid`: platné,
  - `expiring`: poslední rok platnosti,
  - `expired`: vypršelé.
- Vypršelé hodnocení zobrazíme šedě jako „Hodnocení vypršelo (2018)“ místo plných hvězdiček, aby staré 5★ nepůsobilo stejně jako nové.
- Hodnocení vážeme ideálně na **generaci modelu**, ne jen na jeho název, protože facelift ho může změnit.

## 3. UI

### 3.1 Odznak na kartě výsledku (`results_grid.py`)

- Malý štítek s ikonou štítu, hvězdičkami a rokem testu, např. `★★★★★ 2024`.
- Neotestovaný model: neutrální štítek „Zatím netestováno“. Nesmí to vypadat jako 0★.
- Vypršelé hodnocení: šedý štítek „Vypršelo (2018)“.

### 3.2 Detailní panel (`vehicle_detail_modal.py`)

- **Hlavička:** velké hvězdičky, rok testu a verze protokolu, vpravo odkaz „Celý protokol“ na stránku modelu na euroncap.com.
- **Čtyři vodorovné pruhy** s procenty pro jednotlivé oblasti:
  - na každém pruhu je značka minimálního skóre potřebného pro 5★ v dané oblasti, takže je vidět, jak blízko je auto další hvězdičce,
  - nejslabší oblast auta je zvýrazněná varovnou barvou (`flag`), ostatní pruhy jsou v `accent`.
- **AI věta:** jedna věta vztahující hodnocení k požadavkům uživatele, např. „Silné pro rodinu s dětmi, ochrana chodců je jen průměrná.“ Generuje ji existující vrstva vysvětlení v `app/ai`.

### 3.3 Srovnání (`compare_dialog.py`)

- Řádky: Hvězdičky, Dospělí, Děti, Chodci, Asistenty.
- Nejlepší hodnota v řádku je zeleně, výrazně slabá hodnota varovnou barvou.

### 3.4 Konvence

- Všechny texty přes `t()` s klíči v `i18n.py` i `i18n_en.py`.
- Barvy pouze z design tokenů. Hvězdičky jsou vlastní vykreslení (znak ★ nebo ikona), ne obrázek Euro NCAP.

## 4. Datový model

Platí dvojí dialekt (SQLite i Postgres), viz `CLAUDE.md`.

- **Nová tabulka `safety_ratings`:**
  - `id`
  - `model_id`: odkaz na `models`, volitelně i `trim_id`, pokud se hodnocení liší podle výbavy,
  - `generation_note`: volný text pro odlišení generace nebo faceliftu,
  - `provider`: zatím jen `euro_ncap`, do budoucna případně ANCAP nebo IIHS,
  - `stars`: 0–5,
  - `test_year`, `protocol_version`,
  - `source_url`: stránka modelu na euroncap.com,
  - `updated_at`.
- **Nová tabulka `safety_rating_scores`** (`rating_id`, `area`, `score_pct`):
  - oblasti jsou obecné, takže se do stejné struktury vejdou čtyři oblasti dnešních protokolů i nová struktura od 2026,
  - `area` je enum v `models/enums.py`.
- **Stav platnosti** (`valid` / `expiring` / `expired`) se neukládá. Počítá se v service vrstvě z `test_year`, aby nevznikl druhý zdroj pravdy.
- **API:** nové Pydantic schéma `SafetyRating` jako volitelné pole u odpovědi vozidla, doplnit do `doc/api-contract.md`.

## 5. Zdroj dat

| Varianta | Výhody | Nevýhody |
|---|---|---|
| **A: ruční kurátorovaný seznam** (doporučeno pro start) | právně nejbezpečnější (jednotlivá fakta s odkazem na zdroj); stejný princip jako `car_photos.py`; stačí pro modely v katalogu | ruční údržba, nová hodnocení vycházejí několikrát ročně |
| **B: scraper pro stránky modelů Euro NCAP** | automatické aktualizace | riziko porušení podmínek webu a práva pořizovatele databáze (EU sui generis); křehké parsování; nutné předem ověřit podmínky a robots.txt |
| **C: dohoda s Euro NCAP** (oficiální data nebo souhlas) | jistota, možnost použít i oficiální logo | závisí na jejich odpovědi, může trvat |

Doporučení: začít variantou A a souběžně napsat Euro NCAP (bod C). Variantu B zvážit až podle jejich odpovědi. Pokud vznikne, patří do `/scraper` jako samostatný úkol, ne do backendu.

## 6. Právní stránka (není právní rada)

- **Pravděpodobně v pořádku:**
  - zobrazit fakta, tedy počet hvězd, procenta a rok testu, vlastní grafikou,
  - přidat zřetelný odkaz „Zdroj: Euro NCAP“ na stránku modelu,
  - samotné odkazování na veřejnou stránku je běžné.
- **Vyžaduje souhlas:**
  - oficiální logo Euro NCAP a grafiku hvězdného hodnocení s date stampem. Podle jejich pravidel vizuální identity potřebuje třetí strana, která chce zveřejňovat hodnocení s jejich vizuální identitou, předchozí souhlas sekretariátu,
  - logo se navíc nesmí upravovat ani deformovat.
- **Omezené:** fotky a videa z crash testů. Euro NCAP je uvolňuje pro redakční (editorial) použití a jiné účely omezuje. Komerční portál pro výběr aut nemusí jako redakční použití projít. Proto na média jen odkazujeme a nehostujeme je, stejně jako u fotek modelů dbáme na licence.
- **Pozor dále:**
  - nevzbuzovat dojem, že Euro NCAP CarSelector doporučuje nebo podporuje,
  - neopisovat systematicky podstatnou část jejich databáze (právo pořizovatele databáze v EU),
  - udržovat data aktuální, tedy vypršení i nová hodnocení, aby portál neukazoval neplatné údaje.

**Před spuštěním:** poslat sekretariátu Euro NCAP krátký e-mail s popisem použití (vlastní vizualizace, odkaz na zdroj, rozsah dat) a požádat o potvrzení. Případně se ve stejném e-mailu zeptat na souhlas s oficiálním logem.

## 7. Využití v doporučování

- Pokud uživatel zmíní bezpečnost, děti nebo rodinu, `recommendation_engine.py` může hodnocení použít jako **měkký faktor řazení**:
  - nejde o tvrdý filtr, protože neotestovaná auta nejsou nutně nebezpečná,
  - vypršelé hodnocení má nižší váhu.
- `RequirementInterpreter` může rozpoznat požadavek typu „aspoň 4 hvězdy v NCAP“ jako volitelný filtr `min_safety_stars`.

## 8. Navržené pořadí

1. Datový model + ruční seed pro modely v katalogu + API pole.
2. Odznak na kartě výsledku + detailní panel.
3. Řádky ve srovnání.
4. Měkký faktor v doporučování + AI věta.
5. Podle odpovědi Euro NCAP: oficiální logo nebo scraper.

## Zdroje

- [Euro NCAP – How to read the stars](https://www.euroncap.com/en/about-euro-ncap/how-to-read-the-stars/)
- [Euro NCAP – FAQ](https://www.euroncap.com/faq/)
- [Euro NCAP – Application of star ratings v18.1](https://cdn.euroncap.com/media/61290/euro-ncap-application-of-star-ratings-v181.pdf)
- [Euro NCAP – Publication guidelines](https://www.euroncap.com/en/press-media/publication-guidelines)
- [Euro NCAP – Visual identity guidelines 2026](https://cdn.euroncap.com/cars/assets/Euro_NCAP_Visual_Identity_Guidelines_2026_c0d792fedc.pdf)
- [Euro NCAP – Detailed guidelines 2016](https://cdn.euroncap.com/media/21956/euro-ncap-detailed-guidelines-2016.pdf)
