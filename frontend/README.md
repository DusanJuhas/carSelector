# DriveWise AI – frontend

React + TypeScript + Vite + Tailwind CSS + Zustand + react-i18next. See `doc/prompt/CLAUDE.md` for
repo-wide conventions and `doc/api-contract.md` for the request/response shapes this app's types
must match.

## Layout

```
src/
  components/  reusable UI components — one component = one file + one *.test.tsx
  pages/       routed screens (currently: ChatPage)
  hooks/       custom React hooks (useConversation, useCatalog, useVehicleDetail)
  api/         typed backend calls — client.ts (Axios instance + ApiError), conversation.ts,
               catalog.ts, vehicleSummary.ts (shared VehicleSummary DTO + Car adapter),
               vehicleDetail.ts (VehicleDetail DTO + adapter)
  types/       shared TS types, mirroring backend/app/schemas per doc/api-contract.md
  store/       global state (Zustand) — conversationStore, catalogStore
  i18n/        i18next config + locale resource bundles (see Language below)
  utils/       small pure helpers (e.g. money formatting)
```

Side effects (API calls) belong in `src/api` or a custom hook, never directly inside a component.
Styling is Tailwind utility classes only — no inline styles, no CSS-in-JS. Design tokens (colors,
type, spacing) are in `doc/design-tokens.md`.

## Language: Czech only, multi-language-ready

The UI ships in Czech only — `src/i18n/config.ts` fixes `lng`/`fallbackLng` to `'cs'`, there's no
language switcher. All static UI copy goes through `useTranslation()`/`t()` against
`src/i18n/locales/cs.json`, not hardcoded strings in components; `en.json` exists alongside it with
the same keys so a second language is a resource file + a switcher, not a rewrite. AI-generated
content (the assistant's messages, per-vehicle explanations) comes from the backend already in
Czech — see `doc/prompt/CLAUDE.md`'s language convention — and isn't routed through the
translation keys, since it isn't static chrome.

Prices are a `Money` object (`{ amount, currency }`, matching `doc/api-contract.md`), formatted via
`src/utils/money.ts`'s `formatMoney()` (`Intl.NumberFormat('cs-CZ', { style: 'currency', currency:
'CZK' })`) — never a hardcoded currency symbol or a pre-formatted string in mock/seed data.

## Talking to the backend

`hooks/useConversation.ts` calls `api/conversation.ts`'s `startConversation`/`sendMessage` (an
Axios client, `api/client.ts`) against the real backend — `VITE_API_BASE_URL` overrides the
default of `http://localhost:8000/api` (see backend/README.md for running it). Errors surface as
a typed `ApiError` with a `code` (`"ai_not_configured"`, `"network_error"`, ...) so the UI can
show a specific message instead of a generic failure - see `ChatPage`'s error banner for the
`ai_not_configured` case.

### Browsing mode vs. narrowed mode

`ChatPage` shows one of two things in the results panel, decided by `conversationStore`'s
`hasNarrowed` flag:

- **Browsing** (default, and whenever the AI hasn't actually searched yet): the full catalog,
  loaded page by page via `hooks/useCatalog.ts` → `api/catalog.ts`'s `listVehicles` (`GET
  /vehicles`, paginated, "Load more" to fetch another page). This needs no conversation and no
  `ANTHROPIC_API_KEY` - it's what you see before typing anything, and what you're left with if the
  AI layer isn't configured (see the banner above).
- **Narrowed**: once a chat turn's response has `searched: true` (the recommendation engine
  actually ran - see doc/api-contract.md), the AI-ranked/filtered shortlist from that turn.
  `hasNarrowed` stays `true` through later follow-up-only turns (a real zero-match search must
  show "0 matches", not silently fall back to the catalog) - only `restart()` clears it.

`Car.score` is `null` in browsing mode (no match to score against) - `CarCard` hides the
score badge/top-pick ribbon when it's `null` rather than showing a misleading 0%.

### Vehicle detail

Clicking a `CarCard` (in either browsing or narrowed mode) opens `VehicleDetailModal`, which
fetches the full `VehicleDetail` (powertrain, color options, standard/optional equipment, price
history) for that configuration via `hooks/useVehicleDetail.ts` → `api/vehicleDetail.ts`'s
`getVehicleDetail` (`GET /vehicles/{configuration_id}`). The selected configuration id is
page-local `useState` in `ChatPage`, not Zustand state - it's ephemeral UI state that doesn't need
to survive a restart. The modal closes on backdrop click, its close button, or Escape.

## Setup

```bash
npm install
```

## Run

```bash
npm run dev
```

Opens the Vite dev server (default `http://localhost:5173`).

## Tests

```bash
npm run test
```

Vitest + React Testing Library, jsdom environment (`src/setupTests.ts`). Every component currently
has a co-located `*.test.tsx`.

## Lint / build

```bash
npm run lint    # oxlint
npm run build   # tsc -b && vite build
```
