# Vlastní doména s SPF a DKIM záznamy (pro odesílání e-mailů)

Popisuje, co znamená „ověřit vlastní doménu“ u poskytovatele transakčních e-mailů
(Brevo, Resend apod.) a proč je to potřeba pro spolehlivé doručení přihlašovacích kódů.

## Co je „vlastní doména“

Jde o **DNS doménu, kterou vlastníš** (např. `rovis.cz`) a ve které můžeš upravovat DNS záznamy
u registrátora nebo DNS hostingu.

- Doménu od Renderu (`*.onrender.com`) použít nejde, protože její DNS neovládáš.
- Freemailovou doménu (`@seznam.cz`, `@gmail.com`) použít nejde, protože její DNS patří
  Seznamu nebo Googlu.

## Proč je to potřeba

Když přijde e-mail od `noreply@rovis.cz`, přijímající server (Seznam, Gmail, …) ověřuje, jestli
ho vlastník domény opravdu povolil. Odpověď hledá v DNS té domény:

| Záznam | Typ | K čemu slouží | Příklad |
|---|---|---|---|
| **SPF** | TXT na `rovis.cz` | Seznam serverů, které smí za doménu odesílat poštu | `v=spf1 include:spf.brevo.com ~all` |
| **DKIM** | TXT nebo CNAME na `<selektor>._domainkey.rovis.cz` | Veřejný klíč. Poskytovatel e-mail podepíše soukromým klíčem a příjemce podpis ověří tímhle veřejným klíčem. Tím se potvrdí, že e-mail přišel z tvé domény a cestou ho nikdo nezměnil | hodnotu vygeneruje poskytovatel |
| **DMARC** | TXT na `_dmarc.rovis.cz` | Říká příjemci, co dělat s e-mailem, když SPF a DKIM neprojdou | `v=DMARC1; p=none; rua=mailto:dmarc@rovis.cz` |

Když tyto záznamy chybí, nebo když se odesílá „za cizí“ doménu (např. `@seznam.cz` přes servery
Brevo), ověření neprojde. E-mail pak skončí ve spamu nebo ho příjemce odmítne.

Gmail a Yahoo dnes vyžadují SPF, DKIM i DMARC u hromadných odesílatelů. I u malého objemu je
lepší mít všechny tři.

## Postup (Brevo)

1. **Pořídit doménu.** Doména `.cz` stojí řádově pár set Kč ročně. Pokud už nějakou máš, stačí ta.
2. **Přidat doménu v Brevu:** *Senders, Domains & Dedicated IPs → Domains → Add a domain*.
3. **Zkopírovat DNS záznamy.** Brevo vypíše konkrétní záznamy (ověřovací TXT kód, DKIM, případně
   SPF a DMARC). Ty vložíš do DNS u registrátora.
   - Pokud už na doméně SPF záznam máš, nepřidávej druhý. Doplň `include:spf.brevo.com` do
     stávajícího, protože doména smí mít jen jeden SPF záznam.
4. **Ověřit.** V Brevu klikni na *Authenticate / Verify*. Projde, až se záznamy rozšíří, typicky
   během minut až hodin.
5. **Nastavit aplikaci.** V konfiguraci (`render.yaml`, `backend/.env`) nastav například
   `SMTP_FROM=noreply@rovis.cz`.

U Resendu je postup stejný: *Domains → Add Domain*, zkopírovat vypsané záznamy do DNS a ověřit.

## Poznámky

- **Poštovní schránka na doméně není potřeba.** Odesílání funguje bez ní, schránka je potřeba jen
  pro příjem odpovědí (nebo DMARC reportů).
- **Ověření domény odstraní sandbox omezení.** U Resendu s ověřenou doménou odpadá omezení
  sandbox odesílatele `onboarding@resend.dev`, který doručuje jen na e-mail vlastníka účtu.
  E-maily pak jdou komukoli.
- **Kontrola záznamů:** `nslookup -type=TXT rovis.cz` nebo
  `nslookup -type=TXT _dmarc.rovis.cz`, případně online nástroje jako MXToolbox.
