# API Contract – DriveWise AI

Source of truth for backend endpoint signatures and shared request/response shapes, per
`doc/prompt/CLAUDE.md`. Frontend TS types in `frontend/src/types` and backend Pydantic schemas in
`backend/app/schemas` must both match this document; when one changes, update this file in the same
change.

This is drafted (not yet implemented) against the normalized catalog schema proposed for
`brands / models / trims / powertrains / configurations / colors / option_items /
option_availability / prices / source_documents` (see conversation history / future
`doc/data-model.md`). Nothing here is implemented yet — no backend exists in the repo.

## Conventions

- Base path: `/api`
- All responses: `application/json`
- Money is always `{ "amount": number, "currency": "CZK" }` — never a bare number or a formatted
  string. `amount` is the VAT‑included consumer price unless a field name says otherwise
  (`amount_excl_vat`).
- Timestamps: ISO 8601 (`2026-07-20T10:00:00Z`)
- List endpoints are paginated: `?page=1&page_size=20`, response wrapped as
  `{ "items": [...], "page": 1, "page_size": 20, "total": 137 }`
- Errors: `{ "error": { "code": "string", "message": "string", "details": {} } }` with a matching
  HTTP status (400 validation, 404 not found, 422 unprocessable, 500 server error)
- No auth in v1 (see architecture doc's bonus features) — endpoints are unauthenticated

## Shared schemas

### Money

| field | type | null? |
|---|---|---|
| amount | number | no |
| currency | string (ISO 4217, e.g. `CZK`) | no |

### VehicleSummary

The recommendation‑card / results‑grid shape — one row per `configuration`, flattened for display.
This is the schema the frontend's chat prototype currently mocks as `Car`
(`frontend/src/types/car.ts`); that mock will need to be updated to match this once the real API
lands — notably `price` becomes a `Money` object instead of a formatted string, and `id` refers to
a `configuration_id`, not a synthetic slug.

| field | type | null? | notes |
|---|---|---|---|
| configuration_id | integer | no | |
| brand | string | no | |
| model | string | no | |
| trim | string | no | |
| price | Money | no | current price (`prices` row with `valid_to IS NULL`) |
| match_score | integer (0–100) | yes | null outside a recommendation context (e.g. plain catalog browse) |
| specs | string[] | no | short display tags, e.g. `["AWD", "5 seats", "Hybrid"]` — derived, not a DB column |
| flag | string | yes | e.g. `"Over budget by ~2,200 Kč"` — set by the recommendation engine, not stored |
| top_pick | boolean | no | default `false` |
| thumbnail_url | string | yes | no image data exists in the scraped source yet — expect null for the foreseeable future |

### VehicleDetail

Extends `VehicleSummary` for a single configuration's detail page.

| field | type | null? | notes |
|---|---|---|---|
| ...VehicleSummary fields | | | |
| powertrain | PowertrainSpec | no | |
| colors | ColorOption[] | no | |
| standard_equipment | string[] | no | names only, `availability = standard` |
| optional_equipment | OptionLine[] | no | `availability = optional`, includes surcharge |
| price_history | PricePoint[] | no | see below |

### PowertrainSpec

| field | type | null? |
|---|---|---|
| fuel_type | enum(petrol, diesel, mild_hybrid, phev, electric) | no |
| transmission | string | yes |
| drivetrain | enum(fwd, rwd, awd) | no |
| power_kw | integer | yes |
| power_hp | integer | yes |
| consumption_min | number | yes |
| consumption_max | number | yes |
| consumption_unit | enum(l_100km, kwh_100km) | yes |
| co2_min_g_km | integer | yes |
| co2_max_g_km | integer | yes |

### ColorOption

| field | type | null? |
|---|---|---|
| name | string | no |
| finish_type | enum(solid, metallic, pearlescent) | yes |
| surcharge | Money | no |

### OptionLine

| field | type | null? |
|---|---|---|
| name | string | no |
| category | enum(equipment, package, warranty, service) | no |
| surcharge | Money | no |

### PricePoint

| field | type | null? |
|---|---|---|
| valid_from | date | no |
| valid_to | date | yes |
| price | Money | no |
| lowest_price_30d | Money | yes |

### StructuredRequirements

Output of the AI requirement‑extraction step (architecture.md's Claude‑extraction example),
input to the recommendation engine's filter/rank step.

| field | type | null? | notes |
|---|---|---|---|
| body_type | string | yes | e.g. `"SUV"` |
| min_seats | integer | yes | |
| budget_max | Money | yes | |
| fuel_type | string | yes | |
| drivetrain | enum(fwd, rwd, awd) | yes | |
| priorities | string[] | no | free‑text priority tags, e.g. `["reliability", "cold-weather"]`; default `[]` |
| notes | string | yes | anything extracted that doesn't map to a typed field above |

### UserRequirement

The human‑readable "requirements drawer" card — already implemented in
`frontend/src/types/requirement.ts` and matches this contract as‑is, no changes needed. One
`UserRequirement` is produced per populated field in `StructuredRequirements` (backend maps
structured → display, not the frontend).

| field | type | null? |
|---|---|---|
| label | string | no |
| value | string | no |
| source | string | no |
| changed | boolean | no |

### ChatMessage / ConversationTurn

Match `frontend/src/types/conversation.ts` as‑is:

```
ChatMessage        { role: "user" | "assistant", text: string }
ConversationTurn   { userText, assistantText, stageName, requirements: UserRequirement[], cars: VehicleSummary[] }
```

## Endpoints

### `POST /api/conversations`

Start a new conversation. No body required.

**Response `201`**
```json
{ "conversation_id": "uuid", "intro_message": "string" }
```

### `POST /api/conversations/{conversation_id}/messages`

Send a user message; get back the assistant's reply plus the updated structured requirements and
shortlist. This is the endpoint the chat prototype's `useConversation` hook will call once the mock
in `frontend/src/api/mock/conversation.ts` is replaced with a real HTTP call.

**Request**
```json
{ "text": "We're a family of 4 and head to the mountains almost every weekend for skiing." }
```

**Response `200`**
```json
{
  "assistant_text": "string",
  "requirements": [ "UserRequirement", "..." ],
  "structured_requirements": "StructuredRequirements",
  "vehicles": [ "VehicleSummary", "..." ]
}
```

### `GET /api/vehicles`

Catalog search/browse, independent of the chat flow (results grid without a conversation).

**Query params**: `body_type`, `min_seats`, `budget_max`, `currency`, `fuel_type`, `drivetrain`,
`market` (default `CZ`), `page`, `page_size`

**Response `200`**: paginated list of `VehicleSummary` (`match_score` and `flag` are null here —
those only apply inside a recommendation context)

### `GET /api/vehicles/{configuration_id}`

**Response `200`**: `VehicleDetail`
**Response `404`**: unknown configuration_id

### `GET /api/vehicles/compare`

**Query params**: `ids` (comma‑separated `configuration_id`s, 2–4)

**Response `200`**
```json
{ "vehicles": [ "VehicleDetail", "..." ] }
```

### `GET /api/models/{model_id}`

Model overview: all trims and their configurations, for a "choose your trim" browsing page.

**Response `200`**
```json
{
  "brand": "string",
  "model": "string",
  "category": "string | null",
  "trims": [
    { "id": "integer", "name": "string", "configurations": [ "VehicleSummary", "..." ] }
  ]
}
```

### `GET /api/brands`

**Response `200`**: `{ "items": [ { "id": "integer", "name": "string", "slug": "string" } ] }`

## Open items for the backend implementation

- `match_score` and `flag` are recommendation‑engine outputs, not stored fields — confirm the
  ranking algorithm (see `drivewise-ai-recommendations` skill) actually produces both per vehicle,
  not just a rank order.
- `thumbnail_url` has no source yet; either scope image sourcing into the scraper later or drop the
  field from `VehicleSummary` until there's a plan for it.
- `GET /api/vehicles` filtering by `budget_max` needs a currency‑aware comparison against
  `prices.currency` — reject or convert cross‑currency queries rather than silently comparing
  numbers across currencies.
