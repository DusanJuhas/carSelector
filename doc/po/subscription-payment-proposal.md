# Placené předplatné DriveWise

*Návrh ze dne 6. 11. 2026, zatím bez implementace*

## Shrnutí

Doporučuji **Stripe Checkout + Stripe Billing + Customer Portal**. Platbu i správu předplatného (změna karty, zrušení, faktury) obslouží hostované stránky Stripe, my jen přesměrujeme uživatele a přijímáme webhooky. Prémiový přístup se odvozuje z lokální tabulky `subscriptions`, kterou plní výhradně webhook.

Hlavní rozhodnutí je volba poskytovatele: **Stripe** dává nejrychlejší a nejčistší integraci, **Paddle** je lepší, pokud nechceme sami řešit DPH a daňové doklady.

Výchozí stav aplikace: přihlášení je bez hesla, jednorázovým kódem na e-mail (`backend/app/services/auth.py`), `User` má příznaky rolí (`is_admin`, `is_author`), ceny jsou v CZK a UI (NiceGUI) běží ve stejném procesu jako FastAPI.

## 1. Poskytovatel plateb

| Poskytovatel | Výhody | Nevýhody |
|---|---|---|
| **Stripe** (doporučeno) | karty, Apple Pay, Google Pay, CZK; hostovaný Checkout i Customer Portal; plný testovací režim, `stripe` CLI přeposílá webhooky na localhost; karetní data se nás nedotknou (minimální PCI) | DPH a daňové doklady řešíme sami (Stripe Invoicing pomůže) |
| **GoPay / Comgate** | české brány, platební tlačítka bank, která čeští uživatelé znají | opakované platby mají těžkopádnější API; obrazovky „spravovat předplatné“ si musíme postavit sami |
| **Paddle / Lemon Squeezy** (merchant of record) | prodávají naším jménem, řeší EU DPH, OSS i faktury | vyšší poplatky (~5 %) |

## 2. Datový model

Platí dvojí dialekt (SQLite i Postgres), viz `CLAUDE.md`.

- **Nová tabulka `subscriptions`:**
  - `user_id`, `provider`
  - `provider_customer_id`, `provider_subscription_id`
  - `plan` (`monthly` / `yearly`)
  - `status` (`active`, `trialing`, `past_due`, `canceled`)
  - `current_period_end`, `cancel_at_period_end`, `updated_at`
- **Nová tabulka `billing_events`** (unikátní ID události od poskytovatele): opakované doručení webhooku se zpracuje jen jednou.
- **Žádný příznak `is_premium` na `User`.** Prémiový přístup se počítá z předplatného (stav `active` nebo `trialing` a nevypršelé zaplacené období), aby neexistovaly dva zdroje pravdy.

## 3. Backend

- **`app/services/billing.py`, třída `BillingService`:**
  - `create_checkout_session(user, plan)`: vrátí URL na Stripe. Předá `client_reference_id=user.id` a předvyplní `customer_email`, e-mail známe z přihlášení.
  - `create_portal_session(user)`
  - `handle_event(payload, signature)`: ověří podpis, přeskočí už zpracované události, pak vloží nebo aktualizuje předplatné.
  - `has_premium(user)`: jediné místo, kde se ptá každá placená funkce.
- **`app/api/billing.py`, endpoint `POST /api/billing/webhook`.** Jen volá service vrstvu. Je to jediné místo, kde zaplacení skutečně zapne prémiový přístup. Návratu z Checkoutu (redirect) se pro to nevěří.
- **Konfigurace:** `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` a ID cen v `app/core/config.py`.
- **Dokumentace:** doplnit webhook a Pydantic schémata do `doc/api-contract.md`.

## 4. UI

- Položka v menu účtu „Předplatné“ otevře dialog s tarify a cenami.
  - Ceny jako `Money`, formátované přes `format_money()`.
  - Všechny texty přes `t()`, každý klíč v českém i anglickém slovníku.
- Volba tarifu vytvoří Checkout session (přes `run.io_bound`) a přesměruje na Stripe přes `ui.navigate.to(url)`.
- Po návratu na `/?billing=success` stránka ukazuje „zpracovává se…“, dokud webhook předplatné neaktualizuje.
- Předplatitelé uvidí položku „Spravovat předplatné“, která otevře Customer Portal.
- Admin konzole dostane přehled předplatitelů jen pro čtení.

## 5. Co může být placené (k rozhodnutí)

- **Více AI konverzací denně:** každá konverzace nás stojí poplatky za LLM, takže je to nejpřirozenější věc ke zpoplatnění. Denní limit pro neplatící může hlídat existující `SlidingWindowLimiter`.
- **Funkce, které už existují:** export do PDF, statistiky porovnání, víc uložených požadavků a oblíbených modelů.
- **Nové nápady:** e-mailová upozornění na změnu ceny (scraper už vede `price_history`, viz `price-watch-proposal.md`), články bez reklam.
- **Nechat zdarma:** základní vyhledávání, aby si noví návštěvníci produkt vyzkoušeli.

## 6. Poznámky k zavedení

- **Právo:** potřebujeme obchodní podmínky včetně pravidel zrušení. V EU platí u digitálních služeb 14denní lhůta pro odstoupení, pokud se jí uživatel při platbě výslovně nevzdá.
- **Faktury:** pro plátce DPH vystaví řádné daňové doklady Stripe Invoicing, případně je řeší Paddle jako merchant of record.
- **Verze:** navrhuji **0.4.0**, protože placené účty zásadně mění produkt. Potvrzuje člověk.
- **Commity:** rozdělit na model a migraci, pak service a webhook s testy (mockované události Stripe), nakonec UI dialog a smoke testy.
