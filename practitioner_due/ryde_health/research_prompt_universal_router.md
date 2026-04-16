# Implementation Task: Add `complaint_intake` Intent to universal_router_webhook.py

## Context
The Ryde Health voice agent has a Node 1 (Entry Greeting Router) that classifies
incoming caller intent and routes via expression edges driven by the
`uni_router_intent` dynamic variable. Existing routing-only intents include
`info_pivot`, `wrap_up`, `cancel_intent`, `service_resolved`, `booking_self`,
`booking_other`, `constraint_change`, etc.

We are adding a **new node** (Node 2C — Complaint Intake) that handles callers
who open with a symptom or condition rather than a named service. To route to it
from Node 1, we need a new pass-through routing intent: **`complaint_intake`**.

It is purely a routing flag — no backend side effects, no database writes, no
external API calls. It must:

1. Set `uni_router_intent` = `"complaint_intake"` in the response, so a Node 1
   expression edge `uni_router_intent == "complaint_intake"` fires and routes
   to the new Node 2C.
2. Clear primary flags (booking_completed, availability_checked, etc.) like
   other pass-through intents.
3. Accept and persist optional context fields from the payload via the existing
   `_validate_and_extract_context` mechanism. Specifically `caller_complaint`,
   `booking_for`, `preferred_gender`, `timeframe_raw`, `practitioner_preference`,
   `location` if Node 1 captured them in the same turn.
4. **NOT** trigger any of the abandon-booking clear keys, info-pivot wipes, or
   booking flow transitions.

## File to Modify
`C:\Users\chomps\Documents\cliniko_api\ClinikoAgent\Nucaching\tools\universal_router_webhook.py`

## Required Changes

### 1. Add to `INTENT_TO_UNI_ROUTER_INTENT` dict
Add the line:
```python
"complaint_intake": "complaint_intake",
```
Place it grouped with the other pass-through routing intents (near
`abandon_booking`, `abandon_availability`, `cancel_intent`).

### 2. Confirm Pydantic intent validator accepts it
Find the `intent: str = Field(...)` declaration around line 335 and check
whether the description / enum constraint needs `complaint_intake` added so
incoming requests aren't rejected. Update the docstring/description to mention
the new intent.

### 3. Add `caller_complaint` to `CONTEXT_FIELD_SPEC`
Around line 230. Currently `caller_complaint` is not in the spec, which means
the universal_router silently drops it. Add:
```python
"caller_complaint": None,  # any string — captured by Node 1, persisted to session
```

### 4. (Verify only — no change unless missing)
Confirm `_get_routing_flags` will route `complaint_intake` through the
default `uni_val = INTENT_TO_UNI_ROUTER_INTENT.get(intent, "")` branch
(it should — it's not in the special-cased set on line 199, and it has no
primary flag, so it falls through correctly). No code change needed here
unless your reading shows otherwise.

## Test Expectations

After the change, calling `universal_router_webhook` with:
```json
{
  "intent": "complaint_intake",
  "called_number": "+61299999999",
  "caller_id": "+61488888888",
  "payload": "{\"caller_complaint\": \"lower back pain\", \"booking_for\": \"self\"}"
}
```

Should return a response with:
- `success: true`
- `intent: "complaint_intake"`
- `uni_router_intent: "complaint_intake"`
- `caller_complaint: "lower back pain"` (echoed for ElevenLabs to bind)
- `booking_for: "self"`
- All other routing flags cleared (`""` or sentinels)
- No database writes
- No emails sent

## Tests to Run

1. Locate the existing universal_router test file (likely
   `tools/test_universal_router*.py` or `test_universal_router*.py` at repo root).
2. Add a test case for `complaint_intake` mirroring the existing `cancel_intent`
   pass-through test.
3. Verify the new test passes and no existing tests regress.

## Out of Scope
- Do NOT modify `INTENT_TO_PRIMARY_FLAG` — this intent has no primary flag.
- Do NOT add to `_ABANDON_BOOKING_CLEAR_KEYS` — this is not an abandonment.
- Do NOT add wrap-up logic.
- Do NOT touch `smart_intent_router` / `openai_intent_detector` — those are
  upstream classifiers and may need separate changes (handled in a different
  task).

## Deliverables
- A diff showing the exact lines added to `universal_router_webhook.py`
- The new test case added
- Test run output showing pass

If you find any inconsistency between this spec and the actual file (e.g.
the Pydantic model rejects unknown intents in a stricter way than expected),
flag it before making changes — do not silently work around it.
