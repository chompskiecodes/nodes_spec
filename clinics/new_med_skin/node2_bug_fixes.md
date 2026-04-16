# Node 2 Bug Fixes — new_med_skin

## Bug 1: New Patient Action — verbatim script spoken without tool call

**Symptom:** Agent said the new patient verbatim script but did NOT call `universal_router` in the same turn — or called the tool silently with no spoken output. Tests for new patient gate (C2) failed.

**Root cause:** The TURN TYPE RULE stated every turn is "spoken response OR tool call" with only CONCERN-GUIDED as the exception. NEW PATIENT ACTION requires BOTH speech and tool call in the same turn, but this wasn't listed as an exception, so the model defaulted to tool-call-only (zero speech) or speech-only.

**Fix applied to `node_2_service_resolution.txt`:**
1. TURN TYPE RULE: Added `(2) NEW PATIENT ACTION` as a named exception — "verbatim script spoken FIRST, then tool call in the SAME turn -- both are required and must co-occur."
2. NEW PATIENT ACTION block: Restructured as explicit PART 1 (speak) + PART 2 (tool call), with "NEVER emit the spoken script without also calling universal_router" and vice versa.

---

## Bug 2: Variant question skipped when `{{implied_service}}` is pre-set

**Symptom:** When caller named a service in message 1 (setting `implied_service`), then answered the gate question in message 2, the agent bypassed the variant question and routed directly to a sub-type appointment. Tests for PRF.C3, FACIAL_VOLUME.C3, SKIN_PEELS.C3, SKIN_QUALITY.C3, LED.C3 all showed this pattern.

**Root cause:** The VARIANT-FIRST RULE said "When the caller's **message** matches PRF/FACIAL_VOLUME/etc." — this only fires on the *current turn's message*. When entering the branch via `{{implied_service}}` (set in a prior turn), the current message is just a "yes"/"no" to the gate question, which doesn't match the category keyword trigger. The rule didn't cover this entry path.

**Fix applied to `node_2_service_resolution.txt`:**
- VARIANT-FIRST RULE rewritten to cover BOTH entry paths: "whether triggered by the caller's current message matching the category OR by `{{implied_service}}` already being set to that category." Added: "There is NO shortcut past the variant question."

---

## Bug 3: LED Top-up — secondary guard not enforced before routing

**Symptom:** When caller said "top-up" for LED, agent routed directly to the add-on appointment type (`1649827716951713108`) without first asking "Have you already completed an LED pack with us?" Test LED.top-up secondary guard failed.

**Root cause:** The prompt said "Top-up / add-on (only if caller confirms prior pack)" but the secondary question was listed after the routing action as a fallback ("Caller says top-up but has NOT confirmed prior pack: ask..."). The model treated the guard as optional because the routing line came first. The guard was advisory, not mandatory.

**Fix applied to `node_2_service_resolution.txt`:**
- Restructured LED Top-up as an explicit STEP 1 / STEP 2 flow:
  - STEP 1 (mandatory): Ask "Have you already completed an LED pack with us?" HALT. Do NOT route yet.
  - STEP 2: Route to add-on only after "Yes" confirmation. On "No", redirect to pack options.

---

## Additional fixes applied during iteration

### VARIANT-FIRST RULE (Revision 2)
Original Bug 2 fix introduced "caller's **current** message" wording which was too narrow — when entering SKIN_QUALITY/LED/PRF via service mentioned in an earlier turn, the current message is "Yes, I've been before." which doesn't match the category. Regression: C3 tests started producing silent tool calls.

**Fix:** Rewrote VARIANT-FIRST RULE to be category-based: "fires based on the RESOLVED CATEGORY -- not on which turn the service was named."

### SKIN_QUALITY/LED branch restructure
gpt-4.1-mini consistently combined speech + tool call for SKIN_QUALITY.C3 and LED.C3 — asking the variant question AND calling `universal_router` simultaneously, despite explicit HALT instructions. Root cause: the routing options (TURN 2) immediately follow the variant question (TURN 1) in the prompt, and gpt-4.1-mini "completes" the full interaction in one shot.

**Fixes applied:**
- Restructured SKIN_QUALITY and LED branches with explicit TURN 1 / TURN 2 labels
- Added "Universal_router MUST NOT be called during this turn" in TURN 1
- Added "Only execute this block after the caller's next message explicitly states..." in TURN 2
- Updated TURN TYPE RULE to explicitly list variant questions as type-A (spoken only, never combined with tool call)
- Added SKIN_QUALITY disambiguation note: "skin booster/NCTF → SKIN_QUALITY, NOT SKIN_PEELS"

### CATEGORY TABLE disambiguation
gpt-4.1-mini misrouted "skin booster" → SKIN_PEELS (chemical peels). Added explicit DISAMBIGUATION line in the CATEGORY TABLE above the SKIN_PEELS entry.

### Model selection — gpt-4.1 vs gpt-4.1-mini
Despite all prompt fixes, gpt-4.1-mini could NOT reliably follow HALT for SKIN_QUALITY.C3 and LED.C3. Switching scaffold model to `gpt-4.1` resolved both tests immediately (50/50 pass).

**Recommendation:** For 30KB+ Node 2 prompts with complex HALT logic, use `gpt-4.1` not `gpt-4.1-mini` in production. If production uses gpt-4.1-mini, the SKIN_QUALITY and LED C3 behavior (combined speech+tool) should be validated separately.

---

## Final test results

**50/50 tests passing** with `gpt-4.1` scaffold model.

Prompt fixes:
1. Bug 1: TURN TYPE RULE + NEW PATIENT ACTION block restructured → new patient action now correctly speaks verbatim script + calls tool in same turn
2. Bug 2: VARIANT-FIRST RULE rewritten to fire on resolved category (not just current message) → variant questions now fire correctly after gate question flow
3. Bug 3: LED Top-up restructured as mandatory STEP 1 / STEP 2 → secondary guard now enforced before routing
4. Bonus: SKIN_QUALITY/LED TURN 1/2 structure + CATEGORY TABLE disambiguation for "skin booster"
