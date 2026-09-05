# Návrh otázek pro DriveWise wizard (netechničtí uživatelé)

Brainstorm/návrh — zatím neimplementováno, nescoped. Cílem je sada otázek, kterými `RequirementInterpreter`
(`backend/app/ai/requirement_interpreter.py`) může doplňovat chybějící `StructuredRequirements`, když je
požadavek uživatele neúplný nebo nejasný — viz `drivewise-ai-recommendations` skill, sekce "Follow-up questions".

DriveWise je konverzační chat, ne formulář s pevnými poli, takže se tyto otázky nepokládají všechny najednou.
AI vrstva má z aktuální zprávy poznat, co už uživatel řekl, a doptat se **jen na jednu chybějící věc** — tohle
je zásobník otázek/formulací, ne skript, který se má odříkat od začátku do konce.

## Předpoklad: netechnický uživatel

Otázky nesmí vyžadovat, aby uživatel předem znal technické pojmy (karoserie, pohon 4×4, typ paliva/pohonu).
Místo toho se ptají na jeho reálné chování a situaci, ze které AI vrstva odvodí technický parametr sama.

## Otázky

1. **Jaký je váš rozpočet na nové auto?**
   → `budget`

2. **K čemu auto nejčastěji použijete – dojíždění do práce, rodinné výlety, převoz nákladu, nebo kombinace?**
   → `usage`

3. **Kolik lidí bude auto pravidelně vozit?**
   → `min_seats`

4. **Jak má auto vypadat a jak velké má být?**
   *(Např. menší auto do města, praktické kombi na časté cesty, vyšší SUV s lepším výhledem, nebo velký
   rodinný vůz na 7 lidí.)*
   → `body_type`

5. **Jezdíte i tam, kde bývá bláto, sníh nebo horší cesta (chalupa, hory, pole)?**
   *(Pokud ano, hodí se auto s pohonem všech kol – lépe drží na kluzkém povrchu.)*
   → `drivetrain` (AWD)

6. **Jak vypadá vaše typické jezdění?**
   Místo přímé otázky na typ paliva/pohonu (benzín/nafta/hybrid/elektro) — pomocné podotázky, ze kterých AI
   vrstva pohon odvodí:
   - *Jezdíte hlavně po městě na kratší vzdálenosti a máte možnost dobíjet doma nebo v práci?*
     → naznačuje elektromobil
   - *Kombinujete město i časté delší cesty (výlety, práce mimo město)?*
     → naznačuje hybrid
   - *Jezdíte hodně a na dlouhé vzdálenosti (časté dálnice, služební cesty)?*
     → naznačuje naftu (nižší spotřeba na dálnici)
   - *Jezdíte málo nebo nepravidelně a chcete to mít jednoduché?*
     → naznačuje benzín
   → `fuel_type`

7. **Kolik kilometrů ročně přibližně najezdíte?**
   *(Doplněk k otázce 6, pomáhá potvrdit odhad pohonu.)*
   → `annual_mileage` (podpůrný signál pro `fuel_type`)

8. **Vozíte často něco objemného – kočárek, sportovní vybavení, nářadí, nebo táhnete přívěs/loď?**
   *(Konkrétní příklady místo abstraktního "velký zavazadlový prostor".)*
   → `large_trunk`

9. **Preferujete konkrétní značku, nebo naopak nějakou vyloučit?**
   → `brand` (preferovaná/vyloučená)

10. **Co by vás nejvíc naštvalo na špatně vybraném autě – vysoké náklady na provoz, časté opravy,
    nedostatek síly/výkonu, nebo nepohodlí na dlouhých cestách?**
    *(Rámování přes "čemu se chci vyhnout" bývá pro netechnické uživatele snazší než abstraktní priority
    jako "spolehlivost" nebo "komfort".)*
    → `priority`

## Klíčový princip (otázka 6)

Uživatel nemusí vědět, co znamená "hybrid" vs. "elektro" — ptáme se na jeho reálné chování (kde jezdí, jak
často, jestli může dobíjet) a `RequirementInterpreter` z toho `fuel_type` odvodí sám. To odpovídá patternu ze
`drivewise-ai-recommendations` skillu: AI vrstva strukturuje požadavky z volného textu, neočekává od uživatele
předem technický žargon.

## Návazné kroky (nescoped)

- Promítnout formulace do promptu `RequirementInterpreter` (follow-up otázky).
- Případné UI hint chipy v `chat_column.py` by šly přes `t()`/`app/ui/i18n.py`, ne natvrdo.
