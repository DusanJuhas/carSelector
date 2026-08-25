# Natural-Language → Technical-Parameter Translation

A proposed addition to the schema in [db-structure.md](./db-structure.md) / [`backend/app/models/`](../../backend/app/models/):
a small controlled vocabulary + phrase-mapping layer between the free text users type in the chat
and the technical fields `RequirementInterpreter` has to fill in
(`backend/app/schemas/requirement.py`'s `StructuredRequirements`: `body_type`, `fuel_type`,
`drivetrain`, `priorities`). **Not yet implemented** — this is a design proposal, not a migration.

## Why this is needed

Today the AI free-guesses these strings from conversation text with no controlled vocabulary
anywhere, but two of them are matched with exact equality further downstream:

- `catalog.list_vehicles` filters `body_type` with `CarModel.category == body_type`
  ([`catalog.py:173`](../../backend/app/services/catalog.py#L173)) — a plain string equality
  against `models.category`, not a fuzzy or partial match.
- `recommendation_engine.recommend` only accepts `fuel_type` if it parses as one of the six
  `FuelType` enum values ([`recommendation_engine.py:107`](../../backend/app/services/recommendation_engine.py#L107));
  anything else is silently dropped.

Any mismatch between what the AI writes and what's actually stored means a filter that silently
matches nothing. This is worse than a hypothetical today: **`models.category` is `NULL` for 36 of
the 37 models currently in `storage/drivewise.db`** — only the hand-seeded Mazda CX-5 has
`"SUV"` set, so `body_type` search on scraper-imported data can't work at all yet regardless of
translation quality. That's a separate, prerequisite fix (populating `category` on import); this
table is the piece that makes translating *to* the right value possible once it's populated.

`priorities` has no downstream equality check today — it's matched loosely against
`vehicle.specs` display tags (`AWD`, `Hybrid`, …) — but a controlled vocabulary still keeps the
values the AI produces consistent and displayable (the Requirements drawer shows them verbatim).

**Deliberately out of scope:** `min_seats` and `budget_max` are numeric, not enumerable — "rodina
se 3 dětmi" → `min_seats=5` or "kolem 800 tisíc" → `budget_max=800000` need extraction/reasoning,
not a lookup table. Left to the LLM (or a small regex pass), not this schema.

## Schema

Two tables, matching this project's SQLite/Postgres dual-dialect convention (`app/db/base.py`'s
`BigIntPK`; enums stored as plain `VARCHAR`, validated in Python/Pydantic rather than a DB-level
`CHECK`, same as `app/models/enums.py`'s existing enums on SQLite).

### `search_parameter_values`

The canonical vocabulary — what a phrase is allowed to resolve *to*.

```sql
CREATE TABLE search_parameter_values (
    id          INTEGER PRIMARY KEY,
    field       VARCHAR(16) NOT NULL,   -- 'body_type' | 'fuel_type' | 'drivetrain' | 'priority'
    code        VARCHAR(64) NOT NULL,   -- the technical value written into StructuredRequirements
    label_cs    VARCHAR(128) NOT NULL,  -- display label, e.g. Requirements drawer / priority chips
    label_en    VARCHAR(128) NOT NULL,
    UNIQUE (field, code)
);
```

- For `fuel_type` / `drivetrain`, `code` must literally equal the existing `FuelType` /
  `Drivetrain` enum value (`app/models/enums.py`) — no second mapping layer, the interpreter can
  pass it straight through.
- For `body_type`, `code` is whatever `models.category` should actually contain
  (`suv`, `combi`, `hatchback`, `mpv`, `sedan`, …) — this table becomes the single source of truth
  both the AI prompt and the catalog-import normalization step read from.
- For `priority`, `code` is a new small controlled tag set (`low_fuel_consumption`, `cargo_space`,
  `offroad`, `family`, `city`, `performance`, …) that doesn't exist as a DB enum yet.

### `search_phrase_translations`

The actual language → parameter mappings.

```sql
CREATE TABLE search_phrase_translations (
    id          INTEGER PRIMARY KEY,
    value_id    INTEGER NOT NULL REFERENCES search_parameter_values(id),
    locale      VARCHAR(5) NOT NULL DEFAULT 'cs',
    phrase      TEXT NOT NULL,
    match_type  VARCHAR(8) NOT NULL,   -- 'keyword' | 'example' - see Integration below
    source      VARCHAR(16) NOT NULL DEFAULT 'curated',  -- 'curated' | 'conversation_log'
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_phrase_translations_value ON search_phrase_translations (value_id);
```

`source` mirrors the naming already used by `UserRequirement.source`
(`app/schemas/requirement.py`) — provenance of curated-by-hand vs. mined-from-real-conversations
entries, useful once there's enough real chat traffic to mine synonyms from.

## Integration: two distinct uses, don't conflate them

`match_type` exists because this table has to serve two different jobs:

1. **Prompt grounding** (`match_type = 'example'`) — at request time, load the vocabulary plus a
   handful of representative phrases per value and inject them into
   `RequirementInterpreter.SYSTEM_PROMPT` as an explicit allowed-values list (*"`body_type` must be
   one of: suv, combi, …"*) instead of letting Claude invent strings. This is the actual fix for
   the exact-match fragility described above.
2. **Deterministic normalization** (`match_type = 'keyword'`) — after Claude responds, if
   `body_type` / `fuel_type` / a priority doesn't land exactly on a known `code`, do a
   substring/keyword lookup of the user's own message against these rows to coerce it to the
   nearest canonical value, or drop the field. Cheap enough to also serve as a rule-based fallback
   for catalog filtering when `ANTHROPIC_API_KEY` isn't configured at all (today, browsing mode has
   zero personalization in that case).

## Example rows

| field | code | label_cs | phrase (locale, match_type) |
|---|---|---|---|
| `body_type` | `suv` | SUV | *"jezdím hodně po horách"* (cs, example) |
| `body_type` | `combi` | Kombi | *"potřebuju velký kufr"* (cs, keyword) |
| `fuel_type` | `hybrid` | Hybrid | *"chci to úsporné"* (cs, example) |
| `drivetrain` | `awd` | Pohon všech kol | *"jezdím i mimo asfalt"* (cs, keyword) |
| `priority` | `family` | Rodina | *"vozím rodinu se psem"* (cs, example) |

## Summary

| Table | Purpose |
|---|---|
| `search_parameter_values` | Canonical vocabulary per `StructuredRequirements` field — what the AI/engine are allowed to produce/match on |
| `search_phrase_translations` | Curated (or mined) natural-language phrases mapped to a canonical value, tagged for prompt-grounding vs. deterministic-normalization use |

Deliberately just two tables, no generic "taxonomy" framework — matches the rest of
`app/services`' preference for a handful of plain, purpose-built shapes over an abstraction layer
nothing yet needs.
