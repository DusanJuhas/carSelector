# Vytváření uživatelů v DriveWise: jak funguje a proč se přihlásí jen admin

*Analýza ze dne 21. 10. 2026*

## Shrnutí

Kód je v pořádku a noví uživatelé se zakládají automaticky. Na Renderu (a v lokálním `.env`) se ale e-mail s přihlašovacím kódem odesílá přes **Resend v sandbox režimu** (`SMTP_FROM=onboarding@resend.dev`). Ten doručuje **jen na e-mail vlastníka Resend účtu**, tedy na adresu admina. Ostatním kód nepřijde, a protože účet vzniká až po ověření kódu, nový uživatel nikdy nevznikne.

## Jak přihlášení a vytvoření účtu funguje

Žádná registrace ani heslo neexistuje. Účet vznikne při **prvním úspěšném přihlášení** jednorázovým kódem z e-mailu.

### 1. Zadání e-mailu

Tok volání: `app/ui/components/login_dialog.py`, pak `AuthState.request_code` (`app/ui/auth.py`), pak `AuthService.request_code` (`app/services/auth.py`).

- Adresa se normalizuje (ořízne a převede na malá písmena). Kontrola formátu je záměrně volná (`normalize_email`).
- Platí rate limit: max. `LOGIN_CODE_MAX_REQUESTS_PER_EMAIL_HOUR` (5) žádostí za hodinu na e-mail a `LOGIN_CODE_MAX_REQUESTS_PER_IP_HOUR` (20) na IP.
- Dřívější nepoužité kódy pro danou adresu se zneplatní.
- Vygeneruje se 6místný kód. Do tabulky `login_codes` se uloží **jen jeho HMAC** (klíč `AUTH_SECRET`), platnost je `LOGIN_CODE_TTL_MINUTES` (10 min).
- Zápis do DB se commitne **před** odesláním e-mailu.
- Kód se odešle přes `SmtpEmailSender` (`app/services/mailer.py`). Když odeslání selže:
  - kód se „spálí“ (`consumed_at`),
  - vyhodí se `AuthError("email_delivery_failed")`,
  - uživatel v dialogu uvidí chybu a do logu se zapíše `Login code delivery failed: ...`.
- Při špatné konfiguraci SMTP (chybí host apod.) vrací UI chybu `email_not_configured`.

### 2. Zadání kódu

Metoda `AuthService.verify_code`:

- Najde nejnovější platný, nespotřebovaný kód pro danou adresu.
- Pokusy počítá atomicky v SQL. Po `LOGIN_CODE_MAX_ATTEMPTS` (5) špatných pokusech se kód spálí a vrací se `too_many_attempts`.
- Když kód sedí:
  - **a uživatel v `users` neexistuje, vytvoří se nový řádek**: `is_admin` = adresa je v `ADMIN_EMAILS`, `is_active=True`;
  - existující adrese z `ADMIN_EMAILS` se doplní `is_admin=True` (jen se přidává, práva se tím nikdy neodebírají);
  - deaktivovaný účet dostane `account_disabled`;
  - nastaví se `last_login_at`.

### 3. Session

- Do `app.storage.user` (podepsaná session cookie NiceGUI) se uloží `auth_user_id` a `auth_issued_at`.
- `AuthState.refresh()` při každém načtení stránky načte uživatele znovu z DB. Deaktivace nebo odebrání práv se tak projeví okamžitě.
- Platnost session je `AUTH_SESSION_DAYS` (30 dní) a vynucuje se na serveru.

### Role

| Role | Jak se získá |
|---|---|
| Běžný uživatel | Kdokoli, kdo úspěšně ověří kód |
| Admin | Adresa v `ADMIN_EMAILS` (při přihlášení) nebo udělení jiným adminem |
| Autor článků | Admin schválí žádost (`app/services/authors.py`) |

Admin konzole (`app/ui/admin.py`) **nemá funkci pro ruční založení uživatele**. Jediná cesta ke vzniku účtu je doručený přihlašovací kód.

## Příčina problému

`render.yaml` to přímo uvádí:

```yaml
# The Resend account's own email: the sandbox sender below only
# delivers there, so for now only that address can log in.
- key: ADMIN_EMAILS
  sync: false
...
# Sandbox sender until a domain is verified in Resend.
- key: SMTP_FROM
  value: onboarding@resend.dev
```

Lokální `backend/.env` je nastavený stejně:

```
ADMIN_EMAILS=dnc@seznam.cz
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.resend.com
SMTP_FROM=onboarding@resend.dev
```

Odesílatel `onboarding@resend.dev` smí posílat jen na e-mail Resend účtu, tedy na adresu admina. Pro jakoukoli jinou adresu Resend zprávu odmítne. Aplikace to pak vyhodnotí jako `email_delivery_failed`, nebo e-mail prostě nedorazí. Bez kódu neproběhne `verify_code`, a proto se nevytvoří ani záznam v `users`.

Kde to ověřit: v logu Renderu hledej řádek:

```
Login code delivery failed: SMTP delivery via smtp.resend.com:2587 (starttls) failed: ...
```

Na jeho konci je důvod odmítnutí, který vrátil Resend.

## Řešení

V kódu se nic měnit nemusí, stačí změnit konfiguraci.

### Varianta A: ověřit vlastní doménu v Resendu (doporučeno)

1. V Resendu přidej doménu a nastav DNS záznamy, které vypíše (SPF, DKIM).
2. Na Renderu (Service → Environment) změň `SMTP_FROM=noreply@<tvojedomena>`. Úprava `render.yaml` je volitelná, hodnota je tam natvrdo.
3. Port 2587 / STARTTLS zůstává.

Podmínka: vlastní doména.

### Varianta B: jiný SMTP poskytovatel bez vlastní domény

- Například **Brevo**. Pokud vím, umožňuje ověřit jednu odesílací adresu bez domény a nabízí SMTP na portu **2525**. Před přepnutím si to ověř v jeho dokumentaci.
- Mění se jen hodnoty `SMTP_*` (předvolby jsou v `backend/.env.example`).
- **Seznam ani Gmail z Renderu nepůjdou:** free plán Renderu blokuje odchozí porty 25/465/587 a tyto služby jiné porty nenabízejí.

### Ověření po změně

```bash
python scripts/send_test_email.py   # jako příjemce zadej jinou adresu než admina
```

Pak zkus přihlášení s novou adresou. V tabulce `users` by měl přibýt řádek a v admin konzoli nový uživatel.

## Relevantní soubory

- `backend/app/services/auth.py`: logika kódů a vytváření uživatele
- `backend/app/services/mailer.py`: odesílání e-mailů (console / SMTP)
- `backend/app/ui/auth.py`: stav přihlášení a session
- `backend/app/ui/components/login_dialog.py`: dvoukrokový přihlašovací dialog
- `backend/app/models/user.py`, `backend/app/models/login_code.py`: datový model
- `backend/app/core/config.py`: `ADMIN_EMAILS`, `LOGIN_CODE_*`, `EMAIL_BACKEND`, `SMTP_*`
- `render.yaml`: produkční konfigurace (Resend sandbox)
