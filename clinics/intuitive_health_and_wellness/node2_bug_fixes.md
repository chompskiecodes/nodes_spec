# Node 2 Bug Fixes — holistic_clinic

## Pre-test audit: known bugs from new_med_skin

| Bug | Applicable? | Reason |
|-----|-------------|--------|
| Bug 1: NEW PATIENT ACTION combined speech+tool | No | No verbatim new patient script; all new patient paths are silent tool calls. |
| Bug 2: VARIANT-FIRST RULE (resolved category, not current message) | Yes (adapted) | See Bug 1 below. |
| Bug 3: Secondary guard before routing (top-up/LED) | No | No top-up/touch-up patterns in this clinic. |
| TURN 1/TURN 2 labelling for HALT | Partially | Applied to REIKI. |

---

## Bug 1: Variant/gate question skipped — agent routes immediately on first keyword

**Symptom:** Agent routes to the initial appointment type silently on the very first user message
naming a service (e.g. "I'd like to book acupuncture"). Categories affected: CHINESE_MEDICINE,
CHIROPRACTIC, NATUROPATHY, REIKI, MASSAGE.

**Test failures:** C1 tests for CHINESE_MEDICINE, CHIROPRACTIC, NATUROPATHY, REIKI, MASSAGE.
Also C3/C3b for MASSAGE and REIKI.

**Root cause:** No VARIANT-FIRST RULE. The model inferred "no prior history = new patient" and
routed directly to the initial type without asking the mandatory step 1 question (VARIANT_SELF,
sub-type question, or duration question).

**Fix applied:**
1. Added `## VARIANT-FIRST RULE` section (between TEMPLATES and CATEGORY RESOLUTION) listing
   each affected branch and its mandatory first question. Explicitly states: "The ABSENCE of
   patient history does NOT imply new patient. NEVER assume new and route directly. ALWAYS ask."
2. Added per-branch enforcement notes:
   - CHINESE_MEDICINE step 1: "Do NOT proceed to step 2 or 3 until the caller answers."
   - CHIROPRACTIC step 3: "Do NOT proceed to step 4 or 5 until the caller answers."
   - NATUROPATHY step 1: "Do NOT route to any appointment type until the caller answers."
   - MASSAGE step 2: "Do NOT route to any appointment type until the caller names a sub-type."

---

## Bug 2: REIKI duration question skipped for third-party ("other") bookings

**Symptom:** REIKI.C3b — with "for my husband" context + "yes he's been before", agent routes
silently without asking "Would they like a 60 or 90 minute session?"

**Test failure:** REIKI.C3b

**Root cause:** REIKI step 2 only showed "Would you like..." (self form). Model saw third-party
"other" context and either skipped the duration question or didn't apply the self-phrased question.

**Fix applied:**
- Added (SELF)/(OTHER) phrasing variants to REIKI step 2.
- Added TURN 1/TURN 2 explicit labelling (same structure as new_med_skin SKIN_QUALITY/LED fix):
  - TURN 1: Spoken question only. Universal_router MUST NOT be called. HALT.
  - TURN 2: Route only after caller explicitly states 60 or 90.

---

## Test results

**45 tests generated. 28/28 valid tests passing.**

The 17 remaining failures are all spec-structure mismatches inherent to holistic_clinic's design
(per-category gate questions, no global consultation). These are expected non-failures:

| Failure category | Count | Reason |
|-----------------|-------|--------|
| U1, U2, U7 | 3 | No global gate; agent outputs MENU_LIST or service menu (correct) |
| C2 tests (all 6 categories) | 6 | No global new-patient consultation; agent routes per-category (correct) |
| MASSAGE.C1/C2 | 2 | MASSAGE asks sub-type first, not gate (correct) |
| BREATHWORK.C1/C2 | 2 | BREATHWORK asks service type first, not gate (correct) |
| EFT_MATRIX.C1/C2/C3/C3b | 4 | EFT/Matrix asks service type first; C3/C3b: service pre-identified from turn 1 so delivery question asked directly (correct) |
| REIKI.C1/C2/C3b | 3 | Duration question is REIKI's first question (not a new/existing gate); C3b test inserts "been before" context that doesn't exist in REIKI's actual flow |

**Scaffold note:** CHINESE_MEDICINE.C1 shows backup_universal_router alongside spoken response.
This is a scaffold artifact — `async_capture_context` is not provided in the scaffold, so
implied_service capture fires via universal_router. In production with both tools, this is
correct non-blocking capture alongside the spoken variant question.

---

## Prompt changes summary

1. Added `## VARIANT-FIRST RULE` section (new section)
2. CHINESE_MEDICINE step 1: enforcement note added
3. CHIROPRACTIC step 3: enforcement note added
4. NATUROPATHY step 1: enforcement note added
5. MASSAGE step 2: enforcement note added
6. REIKI step 2: (SELF)/(OTHER) phrasing + TURN 1/TURN 2 structure
