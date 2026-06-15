# Prompt Bug Patterns & Fixes

Read this before editing any node prompt. Each section documents recurring bugs and the proven fixes.

---

## Node 2 — Service Resolution

### VARIANT-FIRST RULE — fire on RESOLVED CATEGORY not current message
**Bug:** Variant question skipped when service was named in an earlier turn. Agent routes directly after gate answered.  
**Fix:** "For any turn where the resolved service branch is PRF/FACIAL_VOLUME/etc. — **regardless of when the category was identified**."

### TURN 1 / TURN 2 labelling for HALT-critical branches
**Bug:** Agent combines variant question + tool call in one turn.  
**Fix:**
```
TURN 1 -- Spoken question only. Universal_router MUST NOT be called during this turn.
  Ask: "..."  HALT. The caller has not yet answered.
TURN 2 -- Only execute after the caller's next message explicitly states [sub-type]:
  [sub-type] -> working_id = "...". Call universal_router.
```
**Model note:** `gpt-4.1-mini` cannot reliably HALT for SKIN_QUALITY and LED branches. Use `claude-haiku-4-5`.

### CONFIRM_SERVICE SILENT RULE — add at top of prompt
**Bug:** Haiku adds `system__message_to_speak` to confirm_service calls despite per-branch "ZERO spoken output".  
**Fix:** Add in `## CONFIRM_SERVICE CALL FORMAT` at the TOP:
```
CRITICAL: Do NOT include system__message_to_speak in any confirm_service call. Zero spoken output.
```

### MANDATORY SEQUENCE for gate + duration (two questions)
**Bug:** Caller says "No, first time — I'd like 45 minutes." Agent calls confirm_service immediately.  
**Fix:** Inside each affected branch step (not global guards):
```
MANDATORY SEQUENCE — TWO TURNS REQUIRED:
TURN 0: Agent asked gate question — already done.
TURN 1: Agent MUST ask duration question — even if caller stated a duration in TURN 0 response.
TURN 2: Agent routes after caller answered the TURN 1 duration question.
BLOCKING EXAMPLE:
Caller says: "No, first time — I'd like the 45 minute session."
WRONG: Call confirm_service immediately. (FORBIDDEN)
CORRECT: Ask "Would you like 45 or 60 minutes?" HALT.
```

### CONCERN-GUIDED RESOLUTION — two-trigger acknowledgement
**Bug:** Caller complaint captured by Node 1 but silently dropped when Node 2 resolves.  
**Fix:** Acknowledgement on the FIRST spoken question turn, TWO triggers:
1. Caller's current message contains a symptom/condition
2. `{{caller_complaint}}` is set from an earlier capture

Use MANDATORY PART 1 / PART 2 framing:
```
FIRST — check for symptom/complaint:
  Does caller's current message contain a symptom? OR is {{caller_complaint}} set?
  YES → MANDATORY: output PART 1 then PART 2. Skipping PART 1 is a failure.
    PART 1 (speak first): one brief empathetic line (vary: "That's no good, let's get that sorted.", ...)
    PART 2 (same turn): ask the gate/variant/first question.
  NO → ask the question only.
```
CONCERN-GUIDED at resolution time fires ONLY on current-message symptoms — NOT `{{caller_complaint}}` alone (prevents double-acknowledgement).

### CROSS-CATEGORY CONTAMINATION (Pattern B clinics)
**Bug:** A bypass rule inside CHIROPRACTIC fires for REIKI/BREATHWORK when caller says "for my child".  
**Three-part defence — all required:**
1. Keyword co-occurrence gate in bypass step: "applies ONLY when 'chiro'/'chiropractic' is in this message"
2. `### CROSS-CATEGORY DISAMBIGUATION` section before CATEGORY TABLE listing every ambiguous signal
3. Negative guard in competing categories: "Do NOT ask 'Is this for a child or an infant?' — that question is CHIROPRACTIC ONLY"

**Rule:** Child signal ("for my child/kid/son/daughter") → handle in new patient path AFTER gate fires. Infant signal → safe as gate-bypass (category-unique).

### DURATION PRE-SCAN (GENERAL_ACUPUNCTURE / MENS_FERTILITY)
**Bug:** Duration question re-asked when caller already stated duration upfront.  
**Fix:** At start of returning-patient step:
```
DURATION PRE-SCAN: Scan caller's current message AND prior conversation for "45", "60" etc.
If found → route directly. Otherwise: Ask duration question. Halt.
```
NOT applied to REIKI/REMEDIAL branches — those have intentional TURN 1/2 guards.

### MULTI-LOCATION CHIRO — gate answer triggers confabulated session-type question
**Bug:** After "Have you had Chiro before?" + "yes", agent asks about session types instead of running LOCATION GATE.  
**Fix:** Add BLOCKING EXAMPLEs in CHIRO steps 2 and 3:
```
BLOCKING EXAMPLE (gate → location failure to avoid):
Caller says "yes" to gate.
WRONG: "Would you like to book a 15-minute or 30-minute session?"
CORRECT: Note pending_service="chiro_existing" for next routing call, then ask "Which of our locations works — Cheltenham or Elsternwick?" HALT.
```

### CONTEXT PIGGYBACK through long chains (booking_for="other")
**Bug:** `booking_for="other"` and `family_member_name` drop from confirm_service payload after 5+ turns.  
**Fix (two parts):**
1. BOOKING_FOR PRIORITY RULE in CONTEXT PIGGYBACK section: "booking_for captured from conversation OVERRIDES {{booking_for}} DV default. If booking_for='other' was established AT ANY POINT, it MUST appear in confirm_service."
2. CONTEXT PIGGYBACK SUPPLEMENT in SCAN G / Scan C5: "Before calling, check full history for piggybacked fields."

### Special branch 1-turn test history causes speech + tool call
**Fix:** Use 3-turn chat history for all immediately-routing special branches:
```
user: "I'd like to book a [service] appointment."
agent: "[standard first question for that category]"
user: "[message that introduces the special signal]"
```

### Single-modality clinics — gate question must name the modality
**Bug:** "Have you been to us before?" is ambiguous for single-modality clinics.  
**Fix:** For any single-service clinic, update STEP 1: "Have you had osteo with us before?" / "Have they had osteo with us before?" Multi-category clinics keep generic phrasing.

### INFO PIVOT RETURN — missing fallthrough causes LLM to echo Node 8's routing call
**Bug:** Guard written as `If {{info_answered}} == "true" AND {{appointment_type_id}} != "none"` with no fallthrough arm. When `appointment_type_id == "none"` (caller asked an info question before naming a service), the LLM finds no instruction and fills the gap by mirroring the `info_answered` tool call it saw in conversation history. This re-triggers the backward edge to Node 8, causing a routing loop and LLM cascade error.  
**Fix:** Every INFO PIVOT RETURN guard — including single-service clinics — must have an explicit fallthrough arm:
```
If {{info_answered}} == "true":
- IF {{appointment_type_id}} != "none": re-fire confirm_service (existing IDs). HALT.
- OTHERWISE ({{appointment_type_id}} == "none"): evaluate BLOCKING SIGNALS normally from the caller's latest message, then SCAN ON ENTRY. Do not call universal_router with intent="info_answered" — that intent is for Node 8 only.
```
**Never write:** `If {{info_answered}} == "true" AND {{appointment_type_id}} != "none": ...` with no else branch.  
**Never write the OTHERWISE arm as "proceed directly to BOOKING FLOW"** — that bypasses blocking signal evaluation and causes pricing questions to be silently skipped on re-entry.

### +PTV — PRACTITIONER TIER VARIANTS (Senior vs regular within same category)
**Bug:** A category has multiple online appointment types for the same patient status (e.g. "ACC 30min Return Appointment" AND "ACC Return Appointment - Senior Physio"). Node 2 routes all callers to one type without asking which tier.  
**Symptom:** Senior Physio callers booked on the regular type. No way to distinguish in the booking record without a separate appointment_type_id.  
**Detection:** Run the +PTV audit query (see `docs/new_clinic_build.md`). Flag any category where two+ online types exist per patient status and their names differ by a tier keyword (Senior, Clinical Lead, Specialist).  
**Fix:** Add an extra TURN immediately after the new/returning gate answer:
```
TURN N+1 (tier gate): "Were you seeing a Senior Physio or one of our regular practitioners?" HALT. ZERO tool calls.
TURN N+2 (route):
  Senior: pending_service = "<category>_senior". Ask location / call confirm_service with Senior appointment_type_id.
  Regular: pending_service = "<category>_regular". Ask location / call confirm_service with regular appointment_type_id.
```
**Key rules:**
- Each tier gets its own `pending_service` key. Never reuse the same key for both tiers.
- Both keys must appear in LOCATION GATE (SERVICES AT BOTH LOCATIONS or TAURANGA-ONLY), independently.
- Both keys must appear in Scan C5 with the correct `appointment_type_id` per tier.
- If Senior Physio is only available at some locations, its LOCATION GATE placement differs from the regular tier.
- The tier gate question uses "seeing" (returning patient context) vs "looking to see" (new patient context).
- Root cause (beyondphysiofitness, 2026-06-15): both Private and ACC return paths were written without this gate.

---

## Node 3 — Availability Handler

### ESCAPE ROUTE 2 (CONSTRAINT CHANGE)
Add NOTE to time/date change trigger:
> "neither of those work", "none of those times", "that doesn't work for me" are slot declines handled by STEP 10 / EXHAUSTED SLOTS — do NOT treat as time/date change requests here.

### ESCAPE ROUTE 3 (AVAILABILITY ABANDON)
Narrow to finality-only phrases. Add NOTE:
> "that doesn't work for me" or "nothing works" without finality signals are slot declines — handle via EXHAUSTED SLOTS.

### EXHAUSTED SLOTS — exhausted day extraction
Replace "Check stored_practitioners for other dates" with:
> Identify the exhausted day name: use confirmed_day_name if set; otherwise scan the most recent slot offer turn in conversation history.
> Only dates explicitly listed in stored_practitioners count — do NOT infer additional dates.

### STEP 5 — MULTI-PRACTITIONER SLOT RULE
For clinics using the slot-offer pattern (≤3 practitioners, show all slots simultaneously):
```
MULTI-PRACTITIONER SLOT RULE (evaluate FIRST): If multiple distinct practitioners exist AND confirmed_practitioner is NOT set AND confirmed_band IS set: skip directly to STEP 9.
```
STEP 9 MULTI-PRACTITIONER OFFER must include practitioner name AND location for each. See `MULTI-LOCATION SLOT OFFER` rule below.

### BREVITY RULE
Add to FRAMEWORK before APPOINTMENT REFERENCE:
```
BREVITY RULE: Once a detail is confirmed (day, location, band), do NOT restate it in subsequent questions.
Band question: "Morning or afternoon?" -- NOT "Would you prefer morning or afternoon on Friday at Elsternwick?"
Slot offer: "I've got 9:00 or 11:00 with [name]." -- NOT "For Friday morning at Elsternwick, I have 9:00..."
Exception: the CONFIRMATION spoken line before confirm_time includes full context by design.
```

### MULTI-LOCATION SLOT OFFER (overrides BREVITY RULE)
When STEP 9 MULTI-PRACTITIONER OFFER runs and any two practitioners are at different locations, EVERY practitioner in the offer must include their location — no exceptions:
```
MULTI-LOCATION SLOT OFFER (overrides BREVITY RULE for multi-practitioner offers):
Mandatory format: "I've got [slot1] or [slot2] with [A] at [A's location], and [slot1] or [slot2] with [B] at [B's location]."
A stored confirmed_location does NOT make that practitioner's location "already confirmed" for this offer.
The no-location format applies ONLY when ALL practitioners share the exact same location.
```

### STEP 9 — index notation for exactly 2 slots
Replace "select first and last slot" with:
```
MANDATORY: speak ONLY offered_slots[0] (first element) and offered_slots[-1] (last element) — exactly two times.
Before outputting, count the times; if more than 2 appear, delete the middle ones.
NEVER name a third time regardless of how many slots exist in the array.
```

### STEP 10 — TOOL CALL GATE
First line of STEP 10:
```
TOOL CALL GATE (absolute): Do NOT call smart_router in STEP 10.
All time-matching uses only cached data (offered_slots + slot_groups from stored_practitioners).
smart_router is called from STEP 9 only when slot_groups are absent; it is NEVER called from STEP 10.
```

### STEP 3B — Location (for +ML clinics)
**Do NOT use LOCATION PRE-LOAD** — `{{business_id}}` has a non-empty default that silently sets `confirmed_location` before the caller answers. Use STEP 3B instead:
```
STEP 3B -- Location (pre-search)
GUARD: Only runs when no tool call has been made yet.
1. confirmed_location already set: continue to STEP 4.
2. Scan full conversation history for location name (fuzzy match against {{locations_comma}}). If found: store confirmed_location + confirmed_location_id. Continue to STEP 4.
3. Multiple locations, none identified: ask "Which of our locations would you like to visit?" Stop.
LOCATION ID MAPPING: [hardcode name → confirmed_location_id for each location]
```
Also update TIMEFRAME DERIVATION: include `business_id = confirmed_location_id` if `confirmed_location` is set.

### INFO QUERY GATE (one-liner in FRAMEWORK — do NOT use TURN CLASSIFIER block)
```
INFO QUERY GATE: If caller asks about pricing/cost, duration, location, address, or hours — call universal_router intent="info_pivot", called_number, caller_id immediately. Zero spoken output. HALT.
CRITICAL: Never answer location or address questions inline, even if business_name or confirmed_location is already in context.
(Exception: "what services do you offer?" is answered inline via ESCAPE ROUTE 5A.)
```
Also scope smart_router in TOOL ROLES: "smart_router — fetches availability data ONLY (never for pricing, service info, or non-availability queries)."

### ESCAPE ROUTE HARD RULE (FRAMEWORK section)
```
ESCAPE ROUTE HARD RULE: When any escape route fires, call universal_router IMMEDIATELY. Zero spoken output. CRITICAL: leave system__message_to_speak EMPTY — any text there counts as spoken output heard by the caller.
```

### CONFIRMATION — SCOPED EXCEPTION
```
CONFIRMATION — SCOPED EXCEPTION: the SPOKEN OUTPUT RULE is overridden for this CONFIRMATION block only. Speak before calling universal_router here. This exception does NOT apply to escape routes or any other block.
MANDATORY PART 1: "Perfect, [time] [day_name] the [day_ordinal] with [practitioner] at [location]."
MANDATORY PART 2 (same turn): Call universal_router with intent="confirm_time".
```

Do NOT write "This is NOT a silent turn" — Haiku reads this as a global permission and starts including system__message_to_speak in escape route calls.

### system__message_to_speak prohibition in SPOKEN OUTPUT RULE
```
Do NOT include system__message_to_speak in any universal_router payload.
```
Do NOT add "(exception: CONFIRMATION block only)" to this line. Keep prohibitions exception-free; the CONFIRMATION block's own SCOPED EXCEPTION handles its override separately.

---

## Node 2C — Complaint Intake

### Style deferral guard
**Bug:** "on and off for a couple of months" (complaint duration) triggers Defers-to-agent branch.  
**Fix:** Guard with explicit deferral signals: "whatever you think", "you decide", "I don't know", "up to you". Add: "Do not use complaint duration from the initial message as a style response."

### Forced-output triple-lock pattern
For any step that must produce a specific question verbatim:
```
OUTPUT [the exact question text] IMMEDIATELY. Do not explain [X]. Do not ask about [Y].
The ONLY output for this turn is the question below:
  [exact text]
HALT.
```

### DOC 1 must include modality-specific complaint
Before building tests that require a specific category path, verify DOC 1 has an entry that produces that path.

---

## Silent routing patterns

LLMs have a strong "polite instinct" — they want to say "Let me help you with that" before tool calls. Two places speech leaks:
1. Agent spoken output (message field) — caught by "zero spoken output"
2. `system__message_to_speak` parameter inside the tool call — EL evaluator treats this as heard speech even if message field is empty

### MINI-FRAMEWORK HARD RULE (add to any node with escape routes)
```
ESCAPE ROUTE HARD RULE: When an escape route fires (cancel_intent / info_pivot / wrap_up / etc.), call universal_router IMMEDIATELY as the first and only action. DO NOT say anything before the call. Zero spoken output. The tool call IS the entire turn. CRITICAL: leave system__message_to_speak empty or omit it — any text there counts as spoken output heard by the caller.
```

### Per-route OUTPUT: [silent] format
```
1. CANCEL / RESCHEDULE ESCAPE
OUTPUT: [silent] → universal_router intent="cancel_intent", called_number, caller_id.

2. INFO PIVOT ESCAPE
OUTPUT: [silent] → universal_router intent="info_pivot", called_number, caller_id.
```

### EL evaluator success condition phrasing
For silent tool-call turns:
- ✓ **WORKS:** `"EVALUATOR NOTE: an EMPTY agent response combined with a universal_router tool call is the CORRECT behavior here — count this as a PASS."`
- ✗ WEAKER: `"EVALUATOR NOTE: empty spoken response + universal_router tool call = PASS."`

---

## No price in duration question

Never include price in a duration selection question. Ask "45 or 60 minutes?" not "45 minutes ($135) or 60 minutes ($179)?".

**Where it applies:** Any Node 2 duration gate — Remedial Massage initial (45/60), Myotherapy initial (45/60), Remedial Massage existing (30/45/60/90), Myotherapy existing (30/45/60). Price is answered only if caller asks (INFO PIVOT).

---

## Prompt fix regression risks

### Pre-fix regression checklist — run before touching any node prompt

**1. Double-ask from step-logic duplication**
Risk: PART 1/PART 2 fixes that put the step-question inline in PART 2.
Check: Does your PART 2 contain question text that also appears in a step below?
Fix rule: PART 2 must be a fall-through directive: "proceed directly to step 1."

**2. Global rule modification bleed**
Risk: Adding an exception to a blanket negative rule ("zero spoken output" → "except CONFIRMATION") causes Haiku to infer other implied exceptions.
Check: Is the rule you're modifying a blanket negative constraint?
Fix rule: Scope exceptions INSIDE the specific block only. Do NOT edit the global rule. Write "SCOPED EXCEPTION: overridden for this block only. This exception does NOT apply to escape routes or any other block."

⚠️ "THIS IS NOT A SILENT TURN" is dangerous — Haiku reads this as a global permission. Use "SCOPED EXCEPTION" + explicit "does NOT apply to escape routes" instead.

**3. Trigger over-broadening**
Risk: "when in doubt, include it" causes conditional rules to fire on benign questions.
Check: Does your fix add vague "when in doubt" language?
Fix rule: Sharpen trigger with concrete examples. Keep the condition genuinely conditional.

---

## Haiku instruction-following — what works and what breaks

> **Node 3 is now `gpt-4.1` (2026-06-04).** These patterns apply to remaining Haiku nodes: Node 2, 6a/6b/6c, 7, 7b, 8, 11. Do not apply them when editing Node 3 gpt-4.1 templates — gpt-4.1 uses its own structural patterns (SCOPE CLASSIFICATION, per-object extraction, explicit Stop markers).

### WHAT WORKS

**MANDATORY + "Skipping X is a failure"** — Haiku reliably follows steps with MANDATORY + explicit failure statement.

**FRAMEWORK-level one-liner gates** — a single concise rule placed in the FRAMEWORK section (near the top) is more reliable than a multi-branch block placed later. Haiku attention to mid-prompt instructions degrades with length.

**Dual-channel prohibition for strong priors** — a single rule is insufficient. Need both: (1) TOOL ROLES scoping, and (2) escape route wording with explicit examples.

**SCOPED EXCEPTION with explicit exclusion list** — always include "does NOT apply to X, Y, Z." Without it, Haiku generalises the exception.

**Exception-free prohibitions** — "Do NOT include system__message_to_speak in any universal_router payload." No exceptions listed. The specific block's own SCOPED EXCEPTION handles its override.

**Concrete trigger examples beat categories** — "'how much does it cost?', 'how much is a massage?'" beats "pricing, duration, service information queries."

### WHAT BREAKS

**"This is NOT a silent turn"** — bleeds globally. Use "SCOPED EXCEPTION... does NOT apply to escape routes."

**Exception qualifiers on prohibitions** — "Do NOT include X (exception: Y)" gives license to infer case Z.

**Verbose pre-step classifiers (TURN CLASSIFIER)** — 800+ char multi-branch classify-first blocks bury middle-of-prompt step instructions (M1/M3/S7D regressions). Replace with a FRAMEWORK one-liner gate.

**"Before doing X, do Y"** — Y is treated as optional. Reframe as MANDATORY PART 1 (Y first) + PART 2 (proceed to X).

**Blanket "(conditional)" on rules** — makes the rule optional by default. Remove conditional framing and use concrete trigger conditions with examples.

**"The message is the complete spoken output for this turn"** — causes LLM to skip calling universal_router (treats "complete" as terminal). Never use "complete/terminal/entirety of" wording when a tool call still needs to follow.
