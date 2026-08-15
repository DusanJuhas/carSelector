# DriveWise AI – frontend

React + TypeScript + Vite + Tailwind CSS + Zustand + react-i18next. See `doc/prompt/CLAUDE.md` for
repo-wide conventions and `doc/api-contract.md` for the request/response shapes this app's types
must match.

## Layout

```
src/
  components/  reusable UI components — one component = one file + one *.test.tsx
  pages/       routed screens (currently: ChatPage)
  hooks/       custom React hooks (e.g. useConversation)
  api/         backend calls, typed — real client + a mock/ subfolder (see below)
  types/       shared TS types, mirroring backend/app/schemas per doc/api-contract.md
  store/       global state (Zustand) — conversationStore
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
the same keys so a second language is a resource file + a switcher, not a rewrite. The scripted
demo conversation (`src/api/mock/conversation.ts`) is written directly in Czech instead of going
through the translation keys — it stands in for AI-generated content the backend will eventually
produce already-localized, not static chrome.

Prices are a `Money` object (`{ amount, currency }`, matching `doc/api-contract.md`), formatted via
`src/utils/money.ts`'s `formatMoney()` (`Intl.NumberFormat('cs-CZ', { style: 'currency', currency:
'CZK' })`) — never a hardcoded currency symbol or a pre-formatted string in mock/seed data.

## Current status: chat UI runs against mock data

There is no `src/api/client.ts` yet — `src/api/mock/conversation.ts` is the only implementation of
the conversation API today, and `hooks/useConversation.ts` calls into it. The backend's real
conversation endpoints exist (see `backend/README.md`) but aren't wired up from here yet.

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
