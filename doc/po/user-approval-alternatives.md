# Zakládání účtů se schválením adminem: alternativy

*Návrh ze dne 23. 10. 2026, zatím bez implementace*

## Výchozí stav

Účet dnes vzniká automaticky při prvním úspěšně ověřeném přihlašovacím kódu (`AuthService.verify_code` v `backend/app/services/auth.py`). Nový řádek v `users` dostane `is_active=True` a admin nad vznikem účtu nemá žádnou kontrolu. Podrobnosti viz `user-registration-analysis.md`.

Cíl: admin musí potvrdit každý nový účet.

V kódu už existuje vzor pro schvalování: žádost o roli autora (`AuthorRequest` v `backend/app/models/author_request.py`, `backend/app/services/authors.py` a panel `authors_admin_panel`) s workflow `pending → approved | rejected`. Většina variant níže ho může zkopírovat.

## Varianta A: účet čeká na schválení po ověření e-mailu (doporučeno)

**Tok**

1. Uživatel zadá e-mail a ověří kód.
2. Vznikne řádek v `users` se stavem `pending`.
3. Uživatel uvidí hlášku „Účet čeká na schválení administrátorem“.
4. Admin účet v konzoli schválí nebo zamítne.
5. Při dalším přihlášení (nebo hned po obnovení stránky) uživatel projde.

**Datový model**

- V `users` nový sloupec `status`: `pending | active | rejected`. Podle konvence projektu jde o řetězec, ne o DB enum, takže přidání stavu nikdy nepotřebuje migraci specifickou pro dialekt.
- Dále `approved_at` a `approved_by_user_id`.
- Volitelně pole „kdo jsem / proč chci přístup“, které uživatel vyplní po ověření kódu.

**Výhody**

- Admin vidí jen ověřené adresy, žádné překlepy ani cizí e-maily.
- Stejný vzor jako u žádostí o autorství.
- `AuthState.refresh()` už dnes při každém načtení stránky znovu čte uživatele z DB, takže se schválení projeví okamžitě.

**Nevýhody**

- Každý žadatel potřebuje funkční doručení e-mailu. Problém se sandboxem Resendu proto musí být vyřešený dřív.

## Varianta B: žádost o přístup ještě před přihlášením

**Tok**

1. Veřejný formulář „Požádat o přístup“ (e-mail, jméno, důvod).
2. Záznam se uloží do nové tabulky `account_requests`.
3. Admin žádost schválí.
4. Teprve potom může uživatel požádat o přihlašovací kód. U neschválené adresy `request_code` kód vůbec neodešle.

**Výhody**

- Neschváleným adresám neodchází žádné e-maily, takže se šetří kvóta i reputace odesílatele.
- Admin dostane kontext ještě před vznikem účtu.

**Nevýhody**

- E-mail v žádosti není ověřený, takže admin může schválit cizí adresu nebo adresu s překlepem. Bezpečnostně to nevadí, protože přihlášení stejně vyžaduje kód.
- Veřejný formulář potřebuje rate limit a ochranu proti spamu.

## Varianta C: pouze pozvaný seznam (allowlist)

**Tok**

1. Admin předem zadá v konzoli povolené e-maily. Volitelně jde povolit i celé domény, například `@firma.cz`.
2. `request_code` u adresy mimo seznam kód neodešle.
3. Povolená adresa se přihlásí běžným kódem a účet vznikne rovnou jako `active`.

**Výhody**

- Nejjednodušší implementace, bez nového UI pro uživatele.
- Kontrola je úplná.

**Nevýhody**

- Žadatel musí admina kontaktovat jinou cestou.
- Pro veřejnou aplikaci je to nevhodné, pro uzavřenou betu ideální.

## Varianta D: jednorázové pozvánky (invite link)

**Tok**

1. Admin vygeneruje odkaz s jednorázovým tokenem.
2. Pošle ho libovolným kanálem: WhatsApp, osobně nebo e-mailem ze svého účtu.
3. Kdo odkaz otevře, zadá e-mail a ověří kód. Účet pak vznikne rovnou jako `active`.
4. Bez pozvánky účet nevznikne.

**Výhody**

- Admin rozhoduje už při pozvání, takže odpadá fronta schvalování.
- Pozvánka může mít expiraci a předvolenou roli, například autor.

**Nevýhody**

- Nejvíc kódu: tabulka tokenů, hashování tokenu (jako u `login_codes`), expirace a sledování použití.
- Přihlašování dál závisí na doručení e-mailu.

## Varianta E: měkké schválení s omezeným režimem

**Tok**

1. Přihlášení funguje okamžitě.
2. Neschválený účet má omezené funkce, například bez ukládání konverzací, s nižší AI kvótou a bez možnosti žádat o autorství.
3. Schválením adminem se omezení zruší.

**Výhody**

- Uživatel nečeká.
- Admin může schvalovat dávkově.

**Nevýhody**

- Nejde o skutečnou kontrolu nad vznikem účtu, jen nad oprávněními.
- Každá funkce musí kontrolovat stav účtu, takže je víc míst, kde se dá chyba udělat.

## Srovnání

| | A: pending | B: žádost předem | C: allowlist | D: pozvánka | E: omezený režim |
|---|---|---|---|---|---|
| Admin kontroluje vznik účtu | ano | ano | ano | ano | ne (jen práva) |
| Ověřený e-mail v době rozhodnutí | ano | ne | ne | ne | ano |
| E-mail i neschváleným | ano | ne | ne | ne | ano |
| Iniciativa uživatele v aplikaci | ano | ano | ne | ne | ano |
| Náročnost implementace | střední | střední | nízká | vysoká | střední až vysoká |
| Znovupoužití vzoru `AuthorRequest` | vysoké | vysoké | nízké | nízké | nízké |

## Společné body pro všechny varianty

- **Admini z `ADMIN_EMAILS`** se schvalují automaticky, jinak by se nikdo nedostal do konzole.
- **Stávající uživatelé** se v migraci (Alembic, SQLite i Postgres) převedou na `active`.
- **Upozornění adminovi:** odznak s počtem čekajících žádostí v admin konzoli, volitelně e-mail na `ADMIN_EMAILS`.
- **Upozornění uživateli:** e-mail „váš účet byl schválen“ (případně „zamítnut“).
- **Enumerace adres:** hláška „adresa není schválená“ prozrazuje, které e-maily systém zná. Bezpečnější je vždy odpovídat neutrálně, ale za cenu horšího UX. Je potřeba rozhodnout.
- **Zamítnutí:** po zamítnutí lze buď dovolit novou žádost (jako u autorů, nový řádek), nebo adresu zablokovat natrvalo.
- **Deaktivace:** stávající `is_active=False` (zablokování existujícího účtu) zůstává oddělená od stavu schválení, nebo se sloučí do `status` (`disabled`). Je potřeba rozhodnout.
- **Povinné náležitosti:** i18n klíče do `STRINGS` i `STRINGS_EN`, testy (service i UI), záznam v `doc/CHANGELOG.md`. Podle mě jde o inkrement `z`, protože role už přinesla verze `0.3.0`.

## Předpoklad: doručování e-mailů

Kromě B, která neschváleným adresám neposílá kódy, závisí všechny varianty na funkčním doručení přihlašovacího kódu. Oprava Resend sandboxu (ověřená vlastní doména, viz `vlastni-domena-spf-dkim.md`) je proto předpoklad pro každou z nich.

## Doporučení

**Varianta A**, případně v kombinaci s **C** pro hromadné předschválení adres nebo domén (předschválená adresa přeskočí stav `pending`). A svou logikou nejlépe odpovídá dnešnímu toku a kód schvalování autorů jde z velké části převzít.
