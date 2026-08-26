# Documentation index

This folder holds everything that isn't code: architecture, contracts, scope, and process notes.
Not everything here is equally current — some files are brainstorms or the original brief, kept
for context rather than as instructions to follow today. This index says which is which.

## Source of truth (current — keep in sync with the code when either changes)

| Doc | Covers |
|---|---|
| [`api-contract.md`](api-contract.md) | Backend `/api/*` endpoint signatures and shared request/response shapes; `backend/app/schemas/` must match it. |
| [`db/db-structure.md`](db/db-structure.md) | The actual PostgreSQL catalog schema (`brands/models/trims/powertrains/configurations/...`), matching `backend/app/models/`. |
| [`design-tokens.md`](design-tokens.md) | Colors/typography/spacing tokens used in `backend/app/ui/styles.py` (Tailwind `@theme`). |
| [`arch/webScraping/`](arch/webScraping/) | The scraper's real, implemented architecture and current brand/model coverage — see `IMPLEMENTATION_PLAN.md` for status, `Car_Price_List_Architecture.md` for the longer-term target. |
| [`prompt/CLAUDE.md`](prompt/CLAUDE.md) | Repo-wide conventions for Claude Code / any coding agent working in this repo. |

## Scope decisions

| Doc | Covers |
|---|---|
| [`po/MVP.md`](po/MVP.md) | What's in scope for the MVP and why. |
| [`po/Version2.md`](po/Version2.md) | What was deliberately deferred past MVP, and why it can wait. |

## Historical / brainstorm (context, not current spec)

| Doc | Covers |
|---|---|
| [`main.md`](main.md) | The original challenge brief the project started from. Several details (Flask, OpenAI/Azure, no `min_seats` field) have since been superseded — see the status note at the top of the file. |
| [`arch/architecture.md`](arch/architecture.md) | An early architecture sketch. Still useful for the high-level picture; specific tech/schema choices in it are superseded — see the status note at the top of the file. |
| [`db/brainstorm1.md`](db/brainstorm1.md) | Early thinking on what data needs storing and where — precursor to `db/db-structure.md`. |
| [`ai/claude-integration-brainstorm.md`](ai/claude-integration-brainstorm.md) | Ideas for extending the Claude integration beyond what's implemented today. Not scoped or committed to. |

## Process / meta

| Doc | Covers |
|---|---|
| [`roles/roles.md`](roles/roles.md) | Proposed team roles and responsibilities for a full end-to-end delivery. |

## Design assets

| Path | Covers |
|---|---|
| [`gui/`](gui/) | Visual design proposals/mockups (HTML concepts, a PDF draft) that `design-tokens.md` was drawn from. |
| `arch/Car_Selector_Architecture.drawio` / `.jpg` | Diagram source and export for the architecture sketch. |
| `arch/uiDraft1.jpg` | An early UI draft. |

## Keeping this index honest

When you add, rename, retire, or supersede a doc, update this index in the same change. If a doc's
status changes (e.g. a brainstorm gets formalized into a decision), move its row and add a status
note at the top of the file itself, the way `main.md` and `arch/architecture.md` do.
