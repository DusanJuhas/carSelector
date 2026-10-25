DriveWise AI · UI colours



\# Every colour the app uses, and where



Taken from `backend/app/ui/styles.py`, the components and the PDF/e-mail renderers. Hex values are sRGB conversions of the OKLCH tokens. Translucent colours are shown over the panel colour (left half) and the text colour (right half).



\## 1. Design tokens



Defined once as Tailwind `@theme` variables and used as classes like `bg-panel`, `text-accent` or `border-border`.



| Colour | Token / class | OKLCH | ≈ Hex | Where it's used |

| --- | --- | --- | --- | --- |

|  | `bg` bg-bg | 0.975 0.01 245 | #F1F8FD | Page background: body, main page, admin, articles, shared page. |

|  | `panel` bg-panel, bg-panel/85 | 0.995 0.004 75 | #FFFDFA | Cards, dialogs, requirements drawer, header, chat column. Used in almost every component. The 85 % version is the sticky header. |

|  | `panel-2` bg-panel-2, bg-panel-2/90 | 0.95 0.016 245 | #E6F0F9 | Secondary surfaces: chips, spec tags, wizard options, section rows in the compare table, the inactive state of badges and source chips, secondary buttons (share). PDF table fill. |

| Aa | `text` text-text | 0.27 0.02 55 | #2E241D | Main text everywhere: headings, values, input text, the AI chat bubble. |

| Aa | `subtext` text-subtext | 0.52 0.02 55 | #72665E | Secondary text: labels, hints, metadata, spec labels, low match-score badges, article blockquotes. |

|  | `border` border-border | 0.9 0.015 70 | #E5DCD4 | All borders and dividers: cards, inputs, dialogs, chat bubbles, `hr` and blockquote rule in articles. |

| Aa | `accent` bg-accent, text-accent, border-accent | 0.58 0.15 250 | #1F7DCF | Primary buttons (Send, Save, Confirm), links (back to app, edit article), the user's chat bubble, the selected wizard option, the top-pick card border, active states, the bar in comparison stats, the "OK" status in admin. |

| Aa | `accent-soft` bg-accent-soft | 0.58 0.15 250 / 0.14 | #E0EBF4 on panel | Soft highlights: high match-score badge, "best value" cells in the compare table, avatar in the header, active filter chip, "in progress" feedback badge, the active source in admin, the flash animation. |

| Aa | `accent-text` text-accent-text | 0.99 0.005 75 | #FEFBF8 | Text on `accent` backgrounds (primary buttons, user bubble, selected wizard option), and on the `flag` background of the delete-article button. |

| Aa | `flag` text-flag, bg-flag | 0.55 0.15 40 | #B74B21 | Warnings and errors: error messages in all dialogs and admin panels, Reject/Revoke/Delete buttons, the "over budget" label on result cards, the destructive delete-article button. |

| Aa | `flag-bg` bg-flag-bg | 0.55 0.15 40 / 0.12 | #F6E8E0 on panel | Background of warning boxes: warning label on a result card, error boxes in the login and author-request dialogs, the warning banner on the main page. |

| Aa | `ai-bubble` bg-ai-bubble | 0.95 0.035 235 | #D9F3FF | Assistant chat bubble, typing indicator and the chat input field (`chat\_column.py`). |

|  | `shadow-card` shadow-card | 0.4 0.02 60 / 0.12 | #50453D at 12 % | Card shadow: `0 6px 18px`. Result cards and floating panels. |



\## 2. Colours that bypass the tokens



Hard-coded or framework-default colours. These won't change if you edit the tokens.



| Colour | Value | ≈ Hex | Where it's used | File |

| --- | --- | --- | --- | --- |

|  | bg-black/25 | #000000 @ 25 % | Backdrop behind the requirements drawer. | requirements\_drawer.py:26 |

| © credit | bg-black/45 + text-white | #000 @ 45 %, #FFF | Photo-credit label over car photos. | results\_grid.py:201 |

|  | dark="#000" light="#fff", bg-white | #000000 / #FFFFFF | QR code and its frame in the share dialog. | share\_dialog.py:44, :96 |

| Aa | Quasar color=primary | #1976D2 | "Show differences only" checkbox in the compare dialog. Quasar's default blue, not `accent`. | compare\_dialog.py:159 |

| Aa | ui.notify type=positive | #21BA45 | Success toast ("Link copied"). | share\_dialog.py:81 |

| Aa | ui.notify type=negative | #C10015 | Error toasts: PDF export failed, share failed, admin errors. | pages.py:228, compare\_dialog.py:124, vehicle\_detail\_modal.py:97, admin panels |

| Aa | \\\_TEXT (46, 36, 29) | #2E241D | PDF export: main text. Matches `text`. | vehicle\_pdf.py:41 |

| Aa | \\\_SUBTEXT (114, 102, 94) | #72665E | PDF export: labels and muted cells. Matches `subtext`. | vehicle\_pdf.py:42 |

|  | \\\_BORDER (229, 220, 212) | #E5DCD4 | PDF export: table lines. Matches `border`. | vehicle\_pdf.py:43 |

|  | \\\_PANEL\_2 (230, 240, 249) | #E6F0F9 | PDF export: table and section-row fill. Matches `panel-2`. | vehicle\_pdf.py:44 |

| Aa | \\\_ACCENT (31, 125, 207) | #1F7DCF | PDF export: title and "best value" cells. Matches `accent`. | vehicle\_pdf.py:45 |

| Aa | color:#222 | #222222 | Login-code e-mail: body text. | services/mailer.py:120 |

| Aa | color:#666 | #666666 | Login-code e-mail: "ignore this e-mail" footnote. | services/mailer.py:124 |



\## 3. Contrast of real pairings



WCAG 2 contrast ratio. Normal text needs 4.5:1 (AA). Most UI text in DriveWise is 12–14 px, so it counts as normal text.



| Sample | Pairing | Ratio | AA | Where you see it |

| --- | --- | --- | --- | --- |

| Škoda Octavia | text on panel | 14.9 | Pass | Card titles, values |

| Jaký máte rozpočet? | text on ai-bubble | 13.1 | Pass | Assistant chat bubble |

| Spotřeba 5,1 l/100 km | subtext on panel | 5.5 | Pass | Labels, metadata |

| Zobrazeno 12 vozů | subtext on bg | 5.2 | Pass | Text directly on the page |

| Nafta | subtext on panel-2 | 4.8 | Pass | Chips, spec tags |

| Nad rozpočet | flag on panel | 5.1 | Pass | Error and warning text |

| Zpět do aplikace | accent on panel | 4.2 | Fail | Links, accent text, high score badge |

| Odeslat | accent-text on accent | 4.2 | Fail | Primary buttons (13 px), user chat bubble |



Left half of a swatch: panel Right half: text colour

