# User feedback subsystem — proposal variants (2026-10-09)

Status: **variant A implemented in 0.3.4** (`app/services/feedback.py`, admin tab "Zpětná
vazba"). The other variants are still proposals. Follows the format of [Brainstorm-2026-10-09.md](./Brainstorm-2026-10-09.md):
sizes are **S** = up to a day, **M** = a few days, **L** = a week or more.

## Goal

A logged-in user can tell us something: a **bug** ("the page crashed", "the price is wrong"),
an **idea** ("add TCO"), **praise** ("the recommendation was spot on"), or **something else**
(a question, a missing brand). The admin sees it, can act on it, and nothing gets lost.

Why logged-in only: we already have accounts (login by e-mail code), so we get an identity for
free, spam is much less likely, and we can reply. Anonymous feedback can be added later if
needed.

## Shared building blocks (apply to every variant)

- **Entry point:** "Send feedback" / „Napsat zpětnou vazbu“ in the account menu in the header
  (`components/header.py`), next to "Become an author". A dialog in the style of
  `author_request_dialog.py`.
- **Type:** `bug` | `idea` | `praise` | `other` — a plain string column, not a DB enum, same
  reasoning as `author_requests.status` (no dialect-specific migration when a type is added).
- **Auto-captured context** (shown to the user in the dialog, so nothing is collected silently):
  app version (from `CHANGELOG.md`'s top entry or a constant), UI language, which part of the
  app it was opened from (search, vehicle detail, compare, articles, admin), and the related
  object if any (vehicle/trim id, article id). Optional checkbox: "attach my current
  requirements" (the structured `Requirements`, not the chat text).
- **Status workflow:** `new` → `in_progress` → `resolved` | `wont_fix` | `duplicate`. Rows are
  kept after resolution (like author requests) so history stays.
- **Admin:** a new "Feedback" tab in the admin console (next to "Authors"), with a filter by
  type/status and a counter of `new` items in the tab label.
- **Limits:** max text length (e.g. 4 000 chars), rate limit per user (e.g. 10/day) enforced in
  the service, not the UI.
- **Privacy:** the user's e-mail is visible to admins only. Retention (e.g. delete resolved items
  after 12 months) documented in the service docstring. Feedback text never goes into the LLM
  unless a later variant explicitly asks for it.
- **i18n:** every new string in both `i18n.py` and `i18n_en.py`; admin can see which language
  the feedback was written in.
- **Layering:** model `app/models/feedback.py`, schemas, `app/services/feedback.py`, UI
  component + admin panel. A `/api/feedback` endpoint is optional (only if an external client
  needs it — the UI calls the service in-process).

## Overview of variants

| | Variant | What the user gets | Size | Notes |
|---|---|---|---|---|
| A | Feedback inbox | one dialog, one admin list | S–M | ✅ done (0.3.4) |
| B | Contextual feedback | 👍/👎 on recommendations + "report a data error" on a vehicle | M | best signal quality, feeds AI + data |
| C | Two-way tickets ("My feedback") | status + admin replies + e-mail notice | M–L | builds on A |
| D | Public idea board | ideas others can vote on, roadmap | L | needs moderation |
| E | Forward outside the app | e-mail / GitHub issue | XS–S | quick, but no in-app history |

### A) Feedback inbox (minimal)

**What:** the dialog from the shared blocks; one table `feedback` (id, user_id, type, text,
context JSON, language, app_version, status, created_at, resolved_at, resolved_by_user_id,
admin_note). The admin sees a list, opens the detail, changes the status, writes an internal
note. The user only gets "Thank you, we've got it".

**Pros:** small, fits the existing author-request pattern almost 1:1. **Cons:** the user never
learns what happened with their report — a one-way street.

### B) Contextual feedback

**What:** feedback where the user already is, instead of one generic dialog:

1. **On a recommendation / AI explanation:** 👍 / 👎 + an optional reason ("too expensive",
   "wrong body type", "explanation doesn't match the car"). Stored with the requirements and
   the recommended trim ids.
2. **On the vehicle detail:** "Report a data error" → pick a field (price, equipment, colour,
   consumption, other) + what's correct. Linked to the vehicle's `source_document`, so the admin
   can open the original price list right away.
3. **Generic dialog** from A stays for everything else.

**Why:** a 👍/👎 click is cheap, so we get far more signal than from free text. Data error
reports directly support data freshness (the scraper/import pipeline). 👎 together with the
requirements is ready-made material for tuning the ranking and prompts.

**Caveat:** the LLM trace (`app/ai/trace.py`) is in-memory only. If we want a 👎 to point to the
exact prompt/response, the report has to copy the relevant trace entry at that moment (with the
user's consent, since it contains their text).

**Possible follow-up:** a weekly aggregate in the admin ("12× 👎 on SUVs, mostly 'too
expensive'"), optionally summarized by the LLM through `app/ai`.

### C) Two-way tickets ("My feedback")

**What:** A + a "My feedback" page in the account menu: the user sees their reports, status, and
admin replies. A reply is a message in a thread (table `feedback_messages`: feedback_id,
author_user_id, text, created_at). On a reply or status change the user gets an e-mail via
`app/services/mailer.py` (in their UI language, like the login code), with a link back.

**Pros:** users see they were heard; the admin can ask a clarifying question ("which car was
it?"). **Cons:** more UI, e-mail templates, and an obligation to actually reply.

### D) Public idea board

**What:** ideas (only type `idea`) can be made public by the admin after review. Other logged-in
users can vote (one vote per user) and comment. Statuses visible to everyone: "under review",
"planned", "done in 0.x.y" (link to the changelog entry).

**Pros:** shows the product is alive, removes duplicates ("vote for this instead"), helps
prioritize. **Cons:** moderation of comments, a page that looks empty while there are few users,
and public promises. Makes sense only with a real user base — later.

### E) Forward outside the app

**What:** the dialog just sends an e-mail to a configured address (`FEEDBACK_EMAIL` in config)
via the existing mailer, or creates a GitHub issue through the API. Nothing stored in our DB.

**Pros:** almost no code, works today. **Cons:** no admin view, statuses or link to the app's
context; a GitHub issue would make user texts (and possibly e-mails) public — would need
stripping of personal data and a private repo. Usable as a *notification* on top of A rather
than a replacement.

## Recommendation

1. **A + the "report a data error" part of B** as the first step (M). Same `feedback` table:
   a data error is just `type = "bug"` with `context.vehicle` filled in. Optional admin e-mail
   notification of new items (E as a notification, not storage).
2. **👍/👎 on recommendations** (rest of B) next — it's the cheapest way to learn whether the
   recommendation engine is any good.
3. **C** once there are real users who would wait for an answer. The data model from step 1 only
   gains a `feedback_messages` table, so nothing has to be rewritten.
4. **D** only after the product is public.

## Open questions

- Should praise be allowed to be quoted publicly (testimonials)? Then it needs an explicit
  consent checkbox.
- Screenshots / attachments: needs file storage, which doesn't exist yet (same blocker as
  photos, Brainstorm #7). Proposed: no attachments in the first version.
- Who besides admins handles feedback — a new role (the "Customer Success" role from
  [../roles/roles.md](../roles/roles.md)), or admins only for now?
- Does this count as a `0.3.z` feature, or (together with C/D) a product shift worth `0.4.0`?
  Proposal: A/B are `0.3.z`.
