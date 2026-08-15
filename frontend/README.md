# DriveWise AI – frontend

React + TypeScript + Vite + Tailwind CSS + Zustand. See `doc/prompt/CLAUDE.md` for repo-wide
conventions and `doc/api-contract.md` for the request/response shapes this app's types must match.

## Layout

```
src/
  components/  reusable UI components — one component = one file + one *.test.tsx
  pages/       routed screens (currently: ChatPage)
  hooks/       custom React hooks (e.g. useConversation)
  api/         backend calls, typed — real client + a mock/ subfolder (see below)
  types/       shared TS types, mirroring backend/app/schemas per doc/api-contract.md
  store/       global state (Zustand) — conversationStore
```

Side effects (API calls) belong in `src/api` or a custom hook, never directly inside a component.
Styling is Tailwind utility classes only — no inline styles, no CSS-in-JS. Design tokens (colors,
type, spacing) are in `doc/design-tokens.md`.

## Current status: chat UI runs against mock data

There is no `src/api/client.ts` yet — `src/api/mock/conversation.ts` is the only implementation of
the conversation API today, and `hooks/useConversation.ts` calls into it. The backend's real
conversation endpoints exist (see `backend/README.md`) but aren't wired up from here yet. When
that lands, `types/car.ts`'s shape will need to move to match `doc/api-contract.md`'s
`VehicleSummary` (notably `price` becomes a `Money` object instead of a formatted string).

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
