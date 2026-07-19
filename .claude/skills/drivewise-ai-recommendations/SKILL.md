---
name: drivewise-ai-recommendations
description: The AI requirement-interpreter and recommendation-engine patterns for DriveWise AI — turning free-text user needs into structured search parameters via the Claude API, filtering and ranking vehicles, and generating human-readable explanations. Use this whenever building or changing the chatbot's requirement extraction, follow-up questioning, intent detection, the ranking logic, or recommendation explanations. Reach for it any time a task involves the AI understanding what a user wants, scoring/ordering candidate cars, or explaining why a car was recommended — even if phrased loosely as "the chatbot" or "the matching logic."
---

# DriveWise AI — Requirement Interpreter & Recommendation Engine

Two cooperating pieces: the **AI layer** converts language into structure and explains results; the **recommendation engine** (plain backend code) does the deterministic filtering and ranking. Keep ranking decisions in code, not in the model — the AI structures and explains, it does not decide the order.

## 1. Requirement interpreter (AI layer)

Job: understand the user's need, ask follow-up questions when the request is underspecified, and emit **structured search parameters**. Call the Claude API from the backend only.

**Contract:** input is conversation text; output is a JSON object of search parameters. Prompt the model to return JSON only — no prose, no Markdown fences — and parse it defensively (strip stray fences, validate against a Pydantic schema, fall back to a follow-up question on parse failure).

**Example**

Input:
> I want a car to transport my whole family to our cottage.

Output:
```json
{
  "min_seats": 5,
  "body_type": "SUV",
  "large_trunk": true,
  "suitable_for_long_trips": true
}
```

Input:
> I need a reliable family SUV under €40,000 with low fuel consumption.

Output:
```json
{
  "vehicle_type": "SUV",
  "budget": 40000,
  "priority": "reliability",
  "fuel_efficiency": true,
  "usage": "family"
}
```

**Follow-up questions:** when required fields are missing or contradictory (e.g. budget absent, or "sporty" + "7 seats"), have the AI ask one focused follow-up rather than guessing. Only extract once you have enough to search.

**Intent detection:** distinguish a new search from a refinement ("actually, make it cheaper") and from a comparison request, so the backend routes to the right flow.

## 2. Recommendation engine (backend code)

Deterministic pipeline — no AI in the ranking itself:

1. Receive the structured requirements.
2. Filter the catalog (see `drivewise-data-model` for query helpers) on hard constraints: budget, seats, body type, fuel type, drivetrain.
3. Score remaining candidates against soft preferences (fuel efficiency, reliability, trunk size, driving style).
4. Rank by score.
5. Return the top matches with the data needed to explain them.

Keep scoring transparent and testable — a weighted sum over named criteria beats an opaque heuristic. Criteria in play: budget, vehicle type, brand preference, fuel type, family size, driving style.

## 3. Explanation generation (AI layer)

Once the engine has ranked results, use the Claude API to produce a short, honest explanation per recommendation, grounded in the actual matched attributes — never invent specs the vehicle doesn't have.

**Example**

Recommended: Skoda Kodiaq
Reason: 7 seats · large luggage compartment · suitable for family trips · available with AWD

## End-to-end success scenario

User: *"We are a family with three children and often travel to our cottage on gravel roads. We need enough luggage space and our budget is 35,000 EUR."*

Flow: AI asks any needed follow-up → extracts `{min_seats, body_type, drivetrain: AWD, large_trunk: true, budget: 35000, currency: EUR}` → engine filters + ranks → AI explains. Expected shortlist shape: Skoda Kodiaq, VW Tiguan Allspace, Toyota RAV4, Hyundai Santa Fe.

## Guardrails

- All Claude API calls run server-side; never expose keys to the frontend.
- Validate every AI JSON output against a Pydantic schema before it reaches the engine.
- The AI never reads or ranks the database directly — it only produces parameters and explanations. The backend owns retrieval and ordering.
