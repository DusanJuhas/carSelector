# Claude Integration Brainstorm — Life Situation → Car Model Selection

Brainstorm only — nothing here is scoped or implemented yet. Goal: catalog ideas for how Claude
can help translate a user's needs and life situation into a car model recommendation, beyond what
already exists in the codebase.

## Baseline: what's already wired

Two Claude touchpoints exist today (`backend/app/ai/`):

- `requirement_interpreter.py` — turns conversation text into `StructuredRequirements` JSON, or a
  follow-up question when underspecified.
- `explanation_generator.py` — generates a short, fact-grounded one-sentence explanation per
  recommended vehicle.

Both are untested against a live `ANTHROPIC_API_KEY` (see [api-contract.md](../api-contract.md)).
`pgvector`/RAG and a comparison page are deferred to [Version2.md](../po/Version2.md).

## Deepening the front door (needs elicitation)

- **Situational probing, not just field-filling.** Instead of only asking for missing structured
  fields, have Claude infer *which* follow-up question resolves the most uncertainty — e.g.
  "family + cottage" already implies AWD/space questions matter more than fuel-type ones, so ask
  that first.
- **Life-stage reasoning.** "We're expecting our second child" → Claude can reason about near-term
  needs (isofix count, trunk with stroller + shopping, but not necessarily 7 seats yet) rather
  than just extracting current-state facts.
- **Implicit constraint surfacing.** Detect budget/usage tension the user hasn't stated explicitly
  — e.g. "as cheap as possible but big enough for the whole family" — and have Claude name the
  tension back to the user rather than silently picking one side.
- **Multi-modal input.** Let users describe their parking situation with a photo (narrow garage,
  street parking) or upload a "wish list" screenshot from another site — Claude's vision input
  could extract constraints humans wouldn't think to type ("your garage looks under 4.5m — that
  rules out these three SUVs").

## Translating "life situation" language into structured + soft criteria

- **Two-tier extraction**, not just one JSON blob: keep the current hard-filter
  `StructuredRequirements`, but add a parallel set of *soft* tags Claude infers ("gravel roads" →
  ground clearance priority, "often carries bikes" → roof-rail/hitch preference) that a scorer can
  weight even when there's no DB column for it yet — natural fit for the `notes`/`priorities`
  fields already in the schema, and later for the `pgvector` semantic layer once it lands.
- **Scenario translation table as a living prompt asset.** Maintain example mappings
  (chata/gravel-road trips, city commuting + weekend skiing, growing family, first car for a
  teenager) as few-shot examples in the system prompt — cheap to extend as you learn what Czech
  users actually say.
- **Uncertainty-aware output.** Right now `requirements` vs `follow_up_question` is binary. Claude
  could instead emit *partial* requirements with confidence, so the recommendation engine can show
  a shortlist immediately while still asking a clarifying question in parallel — feels less like an
  interrogation.

## Beyond hard filters

- **Trade-off narration.** When no vehicle satisfies everything, have Claude explain the trade-off
  in the user's own terms ("nothing under 700k CZK has 7 seats and AWD — dropping AWD gets you 4
  options, dropping to 5 seats gets you 2") rather than the UI just silently relaxing a filter.
- **"Would this actually work for you?" simulation.** For a borderline match, Claude can reason
  about the user's stated scenario against the vehicle's specs narratively — "the trunk fits a
  stroller and weekly shopping, but three kids' luggage for a week at the cottage would be tight."

## Trust and comparison

- **Comparative explanations**, extending `explanation_generator.py` from "why this car" to "why
  this car over the other two in your shortlist" — directly useful once the comparison page
  (Version2) exists.
- **Honesty guardrails already exist** (grounded-only-in-facts, no invented specs) — worth
  extending the same discipline to a "what this car *won't* be great for" line, since naming the
  downside is often what makes a recommendation feel trustworthy rather than sales-y.
- **Q&A over vehicle knowledge**, once manuals/pricelists are RAG-indexed (Version2): let users ask
  free-form questions ("does the Kodiaq's AWD auto-engage or do I switch it manually?") anchored to
  real source documents, with citations back to the source doc.

## Iteration over a session

- **Conversational refinement memory** — already partly scoped ("actually make it cheaper" merges
  with prior context) — could extend to remembering *why* a criterion was set, so if the user later
  contradicts it, Claude can flag the contradiction instead of silently overwriting ("earlier you
  said AWD was important for the cottage road — drop it?").
- **"What changed" summaries** after each turn, so the requirements drawer's `changed: true` flag
  comes with a one-line reason, not just a highlight.

## Longer-horizon ideas (bonus-feature territory)

- **Sentiment/frustration detection** — if a user seems stuck in a loop (rejecting every
  suggestion), have Claude change tack and ask a higher-level question rather than keep narrowing
  filters.
- **Voice + multi-language** — already on the bonus list; Claude's realtime/voice-friendly output
  style would matter more than the STT/TTS plumbing itself.
- **Financing/TCO framing** — Claude could translate a price into a "life situation" number the
  user actually thinks in (monthly leasing cost, fuel cost for their commute distance) — useful in
  the Czech market where financing structures vary a lot by dealer.

## Open question for next step

Which of these to prototype first — deepening extraction quality, adding the soft-criteria/
trade-off narration layer, or comparison explanations? Each has different implications for the
`StructuredRequirements` schema.
