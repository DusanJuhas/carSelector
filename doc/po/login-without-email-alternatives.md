# Účty bez e-mailu: registrace, schválení adminem a přihlášení

*Návrh ze dne 23. 10. 2026, zatím bez implementace*

## Proč

Dnešní přihlášení stojí na jednorázovém kódu z e-mailu. Na Renderu ale e-mail spolehlivě nefunguje: Resend v sandbox režimu doručuje jen na adresu admina a free plán blokuje SMTP porty 25, 465 a 587 (viz `user-registration-analysis.md`). Tento dokument hledá způsoby, jak zakládat účty, schvalovat je adminem a přihlašovat se **bez odesílání e-mailů z DriveWise**.

Navazuje na `user-approval-alternatives.md`, který řeší schvalování nad dnešním přihlášením přes e-mail.

## Dva modely schválení (platí pro všechny varianty)

Schválení adminem je na způsobu přihlášení nezávislé. Každou variantu níže jde kombinovat s jedním z těchto modelů:

- **P (pending):** uživatel se zaregistruje sám, účet vznikne ve stavu `pending` a nejde s ním nic dělat, dokud ho admin v konzoli neschválí. Vzor: `AuthorRequest` a `app/services/authors.py`.
- **I (pozvánka):** veřejná registrace neexistuje. Admin v konzoli vytvoří účet nebo jednorázovou pozvánku a předá ji uživateli mimo aplikaci (osobně, WhatsApp, SMS, svým vlastním e-mailem). Schválení je tím implicitní.

Bez e-mailu má DriveWise jen jeden kanál, kterým může uživateli něco doručit: admina. Proto se model I hodí pro uzavřenou betu a model P pro veřejnou aplikaci. Kombinace P + I je možná (žádost z webu, nebo rovnou pozvánka od admina).

## Společné změny v datovém modelu

- `users.email` dnes slouží jako identita (`unique`, `NOT NULL`). Bez e-mailu je potřeba nový identifikátor `username` (unikátní, normalizovaný na malá písmena) a `email` změnit na volitelný.
- `users.status`: `pending | active | rejected | disabled` (řetězec, ne DB enum, kvůli SQLite i Postgres).
- Stávající účty zůstanou platné. Při migraci dostanou `status=active` a `username` odvozený z e-mailu, nebo si ho nastaví při příštím přihlášení.
- Session se nemění: po úspěšném přihlášení se jako dnes zapíše `auth_user_id` do `app.storage.user` a `AuthState.refresh()` dál čte uživatele z DB při každém načtení stránky.
- **Obnova přístupu bez e-mailu** jde vždy přes admina: admin vydá jednorázový reset odkaz nebo kód (hash v DB, krátká platnost) a předá ho mimo aplikaci. Tuto komponentu sdílejí všechny varianty.

## Varianta 1: uživatelské jméno + heslo

**Registrace a schválení:** model P (formulář: jméno, heslo, důvod) nebo I (admin vytvoří účet s dočasným heslem, nebo pozvánku podle varianty 2).

**Přihlášení:** uživatelské jméno + heslo.

**Implementace**

- Hash hesla přes stdlib `hashlib.scrypt` (bez nové závislosti), nebo přes `argon2-cffi` (doporučený algoritmus, jedna nová závislost s předkompilovanými wheely).
- Nová tabulka pokusů o přihlášení pro rate limit na účet a IP. Dnešní limity jsou svázané s `login_codes`, takže je nejde použít přímo.
- UI: formulář přihlášení, registrace, změna hesla, v admin konzoli „resetovat heslo“.
- Odhad: **nízká až střední** náročnost.

**Bezpečnostní rizika**

- Slabá a opakovaně používaná hesla, credential stuffing a hádání hesel. Zmírnění: minimální délka, kontrola proti seznamu nejčastějších hesel, rate limit, dočasné zamčení účtu.
- Phishing: heslo lze vylákat.
- Únik DB: hashe jsou offline lámatelné. S scrypt/argon2 je to drahé, ale slabá hesla padnou.
- Reset přes admina: kdo přesvědčí admina, dostane účet (sociální inženýrství).

**Infrastruktura mimo DriveWise:** žádná.

## Varianta 2: pozvánka od admina + heslo

Specializace varianty 1 s modelem I, uvedená zvlášť, protože jde o nejmenší rozumný celek.

**Registrace a schválení:** admin v konzoli vytvoří pozvánku (volitelně s předvyplněným jménem a rolí, třeba autor). Vznikne jednorázový odkaz s náhodným tokenem (v DB jen HMAC, stejně jako dnes u `login_codes`) a expirací například 7 dní. Uživatel odkaz otevře, zvolí si jméno a heslo a účet vznikne rovnou jako `active`.

**Přihlášení:** uživatelské jméno + heslo.

**Implementace**

- Vše z varianty 1 kromě veřejné registrace a fronty `pending`.
- Navíc tabulka `invites` a stránka pro přijetí pozvánky.
- Token nepatří do query stringu, kde by skončil v logu Renderu: dát ho do fragmentu (`#token`) a do aplikace ho předat přes JavaScript, nebo ho hned po otevření vyměnit za session.
- Odhad: **střední** náročnost.

**Bezpečnostní rizika**

- Rizika varianty 1 kromě spamu registrací.
- Pozvánku může použít kdokoli, komu se odkaz dostane do ruky. Zmírnění: jednorázovost, krátká expirace, admin vidí, kdo pozvánku použil, a může účet zrušit.

**Infrastruktura mimo DriveWise:** žádná.

## Varianta 3: passkeys (WebAuthn)

**Registrace a schválení:** P nebo I. Při registraci prohlížeč vytvoří passkey (otisk prstu, Windows Hello, Face ID, správce hesel). Server uloží jen veřejný klíč.

**Přihlášení:** jedno kliknutí a biometrie nebo PIN zařízení. Žádné heslo.

**Implementace**

- Závislost `webauthn` (py_webauthn) pro ověřování na serveru.
- V NiceGUI je potřeba volat `navigator.credentials.create/get` přes `ui.run_javascript` a převádět base64url. To je nejpracnější část.
- Tabulka `credentials` (více passkeys na uživatele).
- Obnova přes admina je nutná, protože ztráta zařízení znamená ztrátu přístupu (pokud se passkey nesynchronizuje přes iCloud nebo Google).
- Odhad: **vysoká** náročnost, zvlášť testování napříč prohlížeči a zařízeními.

**Bezpečnostní rizika**

- Nejbezpečnější varianta: odolná proti phishingu (klíč je vázaný na doménu), nic k hádání, únik DB je neškodný (jen veřejné klíče).
- Zbývající riziko je proces obnovy přes admina.
- Passkey je vázané na doménu (`rp_id`). Přechod z `mycar-sg4s.onrender.com` na vlastní doménu (viz `vlastni-domena-spf-dkim.md`) všechny registrované passkeys zneplatní. Doménu je proto lepší ustálit **před** zavedením passkeys.

**Infrastruktura mimo DriveWise:** žádná. Vyžaduje HTTPS (Render ho má, `localhost` funguje pro vývoj).

## Varianta 4: uživatelské jméno + TOTP (autentizační aplikace)

**Registrace a schválení:** P nebo I. Po schválení (nebo při přijetí pozvánky) aplikace zobrazí QR kód pro Google Authenticator, Microsoft Authenticator, Aegis a podobně. Uživatel opíše první kód pro potvrzení.

**Přihlášení:** uživatelské jméno + 6místný kód z aplikace. Žádné heslo.

**Implementace**

- Závislost `pyotp`. Na QR kód je už v projektu `segno` (sdílení výsledků).
- Tajný klíč TOTP je sdílené tajemství, nejde ho hashovat. V DB by měl být šifrovaný klíčem odvozeným z `AUTH_SECRET`, což znamená další závislost `cryptography`.
- Ochrana proti opakovanému použití stejného kódu a rate limit (stejné principy jako dnešní `LOGIN_CODE_MAX_ATTEMPTS`).
- Odhad: **střední** náročnost.

**Bezpečnostní rizika**

- Jako jediný faktor je to 6 číslic: bez přísného rate limitu jde hádat. S limitem je riziko malé.
- Phishing v reálném čase (kód lze přeposlat během 30 sekund).
- Únik DB a zároveň `AUTH_SECRET` prozradí tajné klíče všech uživatelů. To je horší než únik hashů hesel.
- Ztráta telefonu znamená obnovu přes admina.
- UX: pro běžné uživatele je instalace autentizační aplikace bariéra.

**Infrastruktura mimo DriveWise:** žádná (aplikace běží na telefonu uživatele).

## Varianta 5: přístupový klíč vydaný adminem

**Registrace a schválení:** jen model I. Admin vytvoří účet a vygeneruje dlouhý náhodný přístupový klíč (například 128 bitů v čitelné podobě `XXXX-XXXX-…`). Klíč předá uživateli. V DB je jen jeho HMAC.

**Přihlášení:** vložení klíče (případně osobní přihlašovací odkaz s klíčem ve fragmentu URL).

**Implementace**

- Nejméně kódu ze všech variant. Hashování i ověření jde převzít z `login_codes`, nové závislosti nejsou.
- V konzoli: vytvořit účet, vygenerovat nový klíč (starý se zneplatní), zrušit.
- Odhad: **nízká** náročnost.

**Bezpečnostní rizika**

- Hádání nehrozí, únik DB je neškodný.
- Klíč je dlouhodobé tajemství na nosiči: uživatel ho uloží do poznámek, pošle si ho zprávou, nechá v historii prohlížeče (pokud jde o odkaz). Kdo klíč získá, má účet, dokud admin klíč nevymění.
- Phishing: klíč lze vylákat stejně jako heslo.
- Bez druhého faktoru a bez možnosti, aby si klíč uživatel sám změnil (to jde doplnit).

**Infrastruktura mimo DriveWise:** žádná.

## Varianta 6: přihlášení přes externího poskytovatele (OAuth 2.0 / OpenID Connect)

**Registrace a schválení:** model P je přirozený: první přihlášení přes Google, Microsoft, GitHub nebo Seznam vytvoří účet `pending` s jménem a ověřeným e-mailem od poskytovatele. Admin schválí. Lze kombinovat s allowlistem (předschválené adresy nebo domény).

**Přihlášení:** tlačítko „Přihlásit přes Google“ a podobně.

**Implementace**

- Závislost `authlib` (nebo ruční implementace přes `httpx`).
- FastAPI routy pro redirect a callback. Je potřeba ověřit, že v callbacku jde zapsat do `app.storage.user` NiceGUI (session se dnes nastavuje uvnitř stránky).
- Tabulka `identities` (poskytovatel + `sub`), aby jeden účet mohl mít víc poskytovatelů.
- Odhad: **střední** náročnost na jednoho poskytovatele, každý další je levnější.

**Bezpečnostní rizika**

- Hesla ani tajemství uživatelů DriveWise neukládá. Bezpečnost (2FA, ochranu proti phishingu) přebírá poskytovatel.
- Nutná pečlivá implementace: parametr `state` (CSRF), ověření `nonce` a podpisu ID tokenu, přesná redirect URI. Knihovna to řeší, vlastní implementace je riskantní.
- Kompromitace účtu u poskytovatele znamená kompromitaci účtu v DriveWise.
- Závislost na třetí straně: výpadek poskytovatele, změna podmínek. Uživatel bez účtu u žádného z nabízených poskytovatelů se nepřihlásí.
- Soukromí: poskytovatel ví, že se uživatel přihlašuje do DriveWise.

**Infrastruktura mimo DriveWise**

- Registrace OAuth aplikace u každého poskytovatele (Google Cloud Console, Microsoft Entra, GitHub, Seznam pro vývojáře; podmínky Seznamu je potřeba ověřit). Pro běžné scope `openid email profile` je registrace zdarma.
- `CLIENT_ID` a `CLIENT_SECRET` v Environment na Renderu.
- Redirect URI je vázané na doménu: při přechodu na vlastní doménu ji stačí přidat u poskytovatele, účty se nezneplatní (na rozdíl od passkeys).
- Bonus: ověřený e-mail bez odesílání e-mailů, pokud ho DriveWise někdy bude chtít.

## Zamítnuté varianty

- **SMS kód:** placená služba (Twilio, GoSMS a podobně), sběr telefonních čísel (GDPR), SIM swap. Pro DriveWise neúměrné.
- **Bot v messengeru (Telegram a podobně):** závislost na konkrétní aplikaci, složitá integrace, pro cílovou skupinu nepřirozené.
- **Přihlašovací kód přes jinou e-mailovou službu:** to není přihlášení bez e-mailu, ale oprava doručování. Řeší ji `user-registration-analysis.md`.

## Srovnání

### Bezpečnost

| | 1 heslo | 2 pozvánka + heslo | 3 passkeys | 4 TOTP | 5 přístupový klíč | 6 OAuth |
|---|---|---|---|---|---|---|
| Hádání / credential stuffing | střední riziko | střední riziko | žádné | nízké (s rate limitem) | žádné | přebírá poskytovatel |
| Phishing | ano | ano | odolné | ano (v reálném čase) | ano | závisí na poskytovateli |
| Dopad úniku DB | hashe lze lámat | hashe lze lámat | žádný | vysoký (pokud unikne i klíč) | žádný | žádný |
| Spam registrací | ano (model P) | ne | dle modelu | dle modelu | ne | nízký |
| Obnova přístupu | přes admina | přes admina | přes admina | přes admina | přes admina | u poskytovatele |
| Celkově | ★★ | ★★½ | ★★★★★ | ★★★ | ★★½ | ★★★★ |

### Snadnost implementace

| | 1 heslo | 2 pozvánka + heslo | 3 passkeys | 4 TOTP | 5 přístupový klíč | 6 OAuth |
|---|---|---|---|---|---|---|
| Nové závislosti | žádná / `argon2-cffi` | žádná / `argon2-cffi` | `webauthn` | `pyotp`, `cryptography` | žádná | `authlib` |
| Nové tabulky | pokusy o přihlášení | + `invites` | `credentials` | žádná (sloupce v `users`) | žádná (sloupec v `users`) | `identities` |
| Náročná část | UX hesel, rate limit | stránka pozvánky | JS mezi NiceGUI a WebAuthn | šifrování tajemství | — | callback a session |
| Náročnost | nízká až střední | střední | vysoká | střední | nízká | střední |

### Nároky na infrastrukturu mimo DriveWise

| | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Externí služba | ne | ne | ne | ne | ne | ano (OAuth aplikace u poskytovatele) |
| Další tajemství v Environment | ne | ne | ne | ne (používá `AUTH_SECRET`) | ne | ano (`CLIENT_ID/SECRET`) |
| Vazba na doménu | ne | ne | **silná** (změna domény zneplatní passkeys) | ne | ne | slabá (redirect URI) |
| Nároky na uživatele | žádné | žádné | moderní zařízení / prohlížeč | autentizační aplikace | bezpečně uložit klíč | účet u poskytovatele |

## Doporučení

1. **Teď (uzavřená beta, málo uživatelů): varianta 2, pozvánka od admina + heslo.** Žádná externí infrastruktura, střední náročnost, admin má plnou kontrolu nad každým účtem. Pokud je potřeba úplně nejrychlejší řešení na pár dní, stačí **varianta 5** (přístupový klíč), ale jako dlouhodobé řešení je slabší.
2. **Pro veřejnou aplikaci: varianta 6 (OAuth přes Google, případně Seznam) s modelem P.** Nejlepší poměr bezpečnosti a práce: DriveWise neukládá žádná tajemství a admin schvaluje frontu `pending`. Stojí to jednorázovou registraci OAuth aplikace.
3. **Později jako upgrade: varianta 3 (passkeys)** vedle hesla nebo OAuth, až bude ustálená doména.

Varianty 1, 2, 3 a 5 sdílejí admin funkci „vydat jednorázový reset / pozvánku“. Vyplatí se ji postavit jako první, protože ji každá z nich potřebuje.
