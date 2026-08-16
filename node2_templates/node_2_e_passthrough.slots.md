# Family E (`PASSTHROUGH`) — `node_2_e_passthrough.txt` slot reference

Template file: `nodes/node2_templates/node_2_e_passthrough.txt`

Clinics in this family: `bob_ward_physio` (the only member).

## Base clinic

**Base: `bob_ward_physio`** -- trivially, it is the only clinic in this family. There is no drift to detect or normalise (that needs a second clinic to compare against; see the NORMALISED DRIFT section below). The template is bob_ward_physio's 76-line body copied byte-for-byte, with the 4 genuinely clinic-identifying spans lifted to `<<SLOT>>` tokens so a future single-service clinic (one appointment type, no gate question, no category table -- guard-and-forward only) can reuse the same structure.

Family E is defined by the absence of service resolution: this clinic offers exactly one appointment type, so Node 2's whole job is (a) an empathy/concern-guided check, (b) a time-only guard so a bare date/time mention doesn't trigger a premature booking call, and (c) forwarding to `confirm_service` with a fixed payload. There is no `CATEGORY TABLE`, no `CATEGORY BRANCHES`, no `PRACTITIONER-ONLY PATH`, no patient-status gate, and no `MENU_LIST` -- none of Family A/B's per-service machinery is present at all, which is why the template needs only 4 slots against Family B's 45.

## 1. Slot reference

All 4 slots are required (none optional -- a passthrough clinic has no feature to turn off).

| Slot | Description | Value (`bob_ward_physio`) |
|---|---|---|
| `APPOINTMENT_TYPE_ID` | appointment_type_id used for this clinic's single (passthrough) appointment type | `1406607806622081880` |
| `APPOINTMENT_TYPE_NAME` | appointment_type name used for this clinic's single appointment type | `Standard Appointment` |
| `VARIANT_TYPE_VALUE` | variant_type value written into the payload for this clinic's single appointment type (lowercase word matching APPOINTMENT_TYPE_NAME's shape, e.g. 'standard') | `standard` |
| `SERVICE_KEYWORD` | Single-service booking keyword used as (a) a generic-booking-language example in the CONCERN-GUIDED exclusion note and (b) an entry in BOOKING INTENT SIGNALS. A future single-service clinic built from this template would replace this with its own service word (e.g. 'chiro', 'osteo', 'massage'). | `physio` |

`SERVICE_KEYWORD` is used twice in the source file: once embedded inside a generic-booking-language example phrase (`"I need physio"`, itself inside its own outer quotes -- "physio" is not independently quoted there), and once as its own quoted entry in the `BOOKING INTENT SIGNALS` list. Confirmed via a whole-word scan (`grep -o "[A-Za-z]*[Pp]hysio[A-Za-z]*"`) that the bare word "physio" occurs exactly twice in the file and never as a substring of a longer word (e.g. "physiotherapy" does not appear anywhere in this file), so both occurrences were replaced unambiguously.

## 2. NORMALISED DRIFT

None. Drift-normalisation means picking a canonical wording between two or more clinics that spell the same rule differently -- with only one clinic in this family, there is nothing to compare against, so every line of `bob_ward_physio`'s body that isn't one of the 4 slots above is preserved completely verbatim, including its existing internal inconsistencies (see Bugs Spotted below, e.g. the curly-quote `URGENCY QUALIFIER` line, which was left as-is rather than unilaterally "corrected" against a single source).

## 3. Verification

Mechanical round-trip: every `<<SLOT>>` token in the template was substituted with `bob_ward_physio`'s value from the table above (no collapse step needed -- there are no optional slots and no blank-line-count changes anywhere in this family), then compared to the clinic's actual current `node_2_service_resolution.txt` body.

- Rendered length: 14147 characters
- Original length: 14147 characters
- Result: **EXACT BYTE-FOR-BYTE MATCH**

## 4. Bugs spotted (not fixed — reported only)

1. **`URGENCY QUALIFIER` uses typographic (curly) quote marks** where the rest of the file, and most of the fleet, use straight ASCII quotes: `When the caller uses “emergency”, “urgent”, “as soon as possible”, or “same day” ... timeframe_raw=”today”`. Cosmetic only, but it's the same drift pattern found (and normalised) between the two Family B clinics' identical rule -- see `node_2_b_gate_first.slots.md` NORMALISED DRIFT item 3. Left as-is here per this file's fidelity requirement (nothing to normalise against with only one clinic in the family), but a real cleanup pass could standardise it to straight quotes.

2. **`PAST PRACTITIONER LOOKUP GUARD` PHASE B carries multi-location machinery this clinic has no use for.** PHASE B reads `business_id`/`business_name` from the tool result, sets `confirmed_business_id`/`confirmed_location` via a "fuzzy-match against this clinic location names", and branches on "skip LOCATION GATE when confirmed_location is already set; otherwise run LOCATION GATE or gate questions as this clinic requires" -- but bob_ward_physio's file defines no `LOCATION GATE`, no location list, and (being a single-appointment-type PASSTHROUGH clinic with no gate questions of any kind, per `CASE 1 IS INACTIVE FOR THIS NODE` at the top of the file) no gate questions to run either. This branch is dead code for this clinic. The same pattern was independently found in Family B's `new_med_skin` (see that family's `.slots.md` bug 4) — strongly suggesting `PAST PRACTITIONER LOOKUP GUARD`'s PHASE B paragraph is a fleet-wide boilerplate block, originally written for a multi-location/multi-category clinic, that gets copy-pasted into every clinic's Node 2 (Family A, B, and E alike) without being trimmed for clinics that don't have a `LOCATION GATE` at all. Worth a fleet-wide check, not just a Family B/E fix.
