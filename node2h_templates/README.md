# Node 2h templates — home visit intake

## What these are

`node_2h_home_visit_intake.txt` is the prompt-body template for a new node ("Node 2h") that
sits between Node 2 (service resolution) and Node 3 (availability) for clinics whose
appointment types are all home/in-home visits — `mandys_routine_footcare` was the only one (retired 2026-09-20; no live clinic uses it now). Note that
several live clinics (Balrothery Physiotherapy Clinic, Cascade Women's Health, Northern Physio,
Physio Cure, Yandina Podiatry) offer home-visit types *alongside* ordinary clinic-visit ones;
they are deliberately NOT opted in. See `docs/home-visit-intake-node-design.md`. Its job:
collect a full home address and a date of birth for the patient being booked (skipping either
already on file), then make exactly one `universal_router intent="home_visit_intake"` call and
route onward to availability.

`dob_order_us.txt` / `dob_order_au.txt` are the two interchangeable halves of the DOB-parsing
paragraph — US clinics default ambiguous numeric dates to MM/DD, AU clinics default to DD/MM.
Whichever is right for the clinic gets substituted into the `{{DOB_ORDER_BLOCK}}` placeholder.

Like `nodes/node1_templates/`, `nodes/node2_templates/`, and `nodes/node3_templates/`, these are
consumed by a generator (`scripts/generate_node2h.py`) that renders the
final per-clinic `nodes/clinics/<slug>/node_2h_home_visit_intake.txt` file by substituting three
slots — `{{PRACTITIONER_FIRST_NAME}}`, `{{CLINIC_AREA_HINT}}`, `{{DOB_ORDER_BLOCK}}` — and
wrapping the body with the usual `Node ID:` / `Label:` / `LLM: claude-haiku-4-5` /
`Override: Disabled` / `Edges:` / `Additional Prompt:` header. **Never hand-write a per-clinic
`node_2h_home_visit_intake.txt`** — same rule as every other generated node type in this repo;
edit the template here (or the mirrored DOB-order block) and regenerate.

Note: the template currently only actually uses `{{CLINIC_AREA_HINT}}` and `{{DOB_ORDER_BLOCK}}`
in its body text. `{{PRACTITIONER_FIRST_NAME}}` is contracted (per the interface spec this
template was built against) but not referenced — every ask in the body is deliberately phrased
neutrally ("the visit," "the date of birth for the visit") rather than naming the practitioner,
so it reads correctly for both `booking_for="self"` and `booking_for="other"` without a
SELF/OTHER branch. Left in the contract in case a future clinic's phrasing needs it; the
generator substituting it into an unused slot is harmless.

## Design decisions

### DOB readback — DELIBERATE DEVIATION from kynd_psychology's node_6a rule, readback IMPLEMENTED

`kynd_psychology/node_6a_name_collection_self.txt` has a rule (`## 3.5 ADDITIONAL ATTENDEE` →
`IDENTIFIER` → `DOB GIVEN`) that explicitly forbids reading a partner's DOB back: "MANDATORY: do
NOT read the DOB back for confirmation... A wrong DOB only means the backend fails to find a
match and creates a new record instead — never a wrong-person mix-up — so no confirmation step
exists for it." That rule is scoped to DOB used as an **identity-lookup key** — it's one of two
alternative ways (mobile OR DOB) to try to match an *existing* Cliniko record for a returning
family member. A wrong value there is genuinely self-correcting: the lookup just misses and a
new record gets created, with no lasting harm and no wrong-person risk.

Node 2h's DOB is different in kind: it's collected specifically for **new-patient intake**
(`{{has_dob_on_file}}` is only `"false"` when there's nothing to match against yet — an
identity-lookup wouldn't even make sense here), and per `tools/booking_stages/resolution.py`
(read in full for this task — see below) it gets written straight into the patient's permanent
Cliniko record via `update_patient_secure(..., date_of_birth=...)` / `create_patient_secure(...,
date_of_birth=...)` and the matching `cliniko.update_patient({"date_of_birth": ...})` /
`create_patient(phone_data)` call. A wrong value here isn't self-correcting — it's a permanently
wrong DOB sitting in a live clinical record until someone notices and fixes it by hand. That's a
materially different risk profile than a failed lookup, so Node 2h implements the opposite of
KYND's rule: it reads the normalized DOB back in natural month-name form ("the fourteenth of
March, nineteen eighty-five") before treating it as resolved. The node body carries a one-line
`NOTE:` next to the DOB confirm step explaining this is a deliberate deviation and naming why, so
a future editor who's seen KYND's no-readback rule doesn't "harmonize" the two and silently
reintroduce the KYND behavior here where it doesn't fit.

### `booking_for="other"` — whose record actually gets the address/DOB (read `resolution.py` in full)

Read `tools/booking_stages/resolution.py` end to end (1533 lines) before writing this template,
specifically the `if request.patient_address or request.patient_date_of_birth:` block at line
1006 (existing-patient path) and the mirrored `if request.patient_date_of_birth:` /
`if request.patient_address:` lines at 1137–1140 (new-patient-creation path, folded into the
Cliniko `create_patient` payload) and 1238–1242 (the matching `create_patient_secure` call).

**Finding: this is already correct for `booking_for="other"` — not a V1 limitation.** Both paths
write to whichever `patient_id` the family-aware lookup (`find_patient_with_family_context`,
called just above at line 923–928) resolved as *the actual subject of this booking* — for an
existing linked family member that's the dependent's own Cliniko patient record, not the
caller's; for a brand-new dependent it's the `cliniko_patient_id` just created for that specific
person. The code comment already sitting at resolution.py:1001-1005 (referencing
`tools/home_visit_utils.py`, built as a separate parallel work item in this same session)
confirms the same read: *"the caller only volunteers a fresh address/DOB when the intake node
asked (has_address_on_file / has_dob_on_file were false) or they explicitly corrected what's on
file, so a present request value always wins here."* There is no branch anywhere in this file
that hardcodes the caller's own `patient_id` for a `booking_for="other"` address/DOB write — it
always follows the same `patient_id` the rest of the booking uses for that visit's patient. So
Node 2h's `SUBJECT-ON-FILE GATE` correctly treats `{{has_address_on_file}}` /
`{{has_dob_on_file}}` as **caller-only** signals (per the task's own framing) and always collects
both fresh for `booking_for="other"`, and the backend then writes them to the right patient
record — no known gap to flag here.

### Escape routes — what's in the template, and what's deliberately NOT restated

This node runs `Override: Disabled`, so it inherits `nodes/shared/system_prompt.txt` in full at
runtime — including `CANCEL ESCAPE`, `INFO PIVOT`, `WRAP-UP`, `PRICING QUERY`, `EMPATHY MOMENTS`,
`LEAVE MESSAGE`, `CONTACT CLINIC`, `COMPOUND REQUESTS`, `OUTCOME CONSISTENCY`, and
`CONTEXT PIGGYBACK`, all already scoped and battle-tested fleet-wide. Per
`.claude/rules/node-prompt-style.md`'s "Don't repeat system-level rules" and the precedent set by
`nodes/shared/node_6a_name_collection_self.txt` itself (which does *not* carry its own
`CANCEL ESCAPE` / `INFO PIVOT` / `WRAP-UP` sections despite having several node-local escape-route
style blocks), **the template deliberately does not write local `cancel_intent`, `info_pivot`, or
`wrap_up` sections** — a caller who says "actually cancel that" or "that's all, thanks" mid-intake
is already caught by the inherited system-prompt signals with zero action needed here. Writing a
node-local version of any of these would risk exactly the bug `nodes/PROMPT_PATTERNS.md`'s
"Node 2C — Node-local escape routes silently absorbing a more specific system-prompt rule"
section documents: a locally-authored trigger list that's even slightly broader or narrower than
the system prompt's own can silently swallow or miss cases the shared rule already owns
correctly. I re-read `system_prompt.txt` in full specifically to check this node's own trigger
wording against it (see next paragraph) rather than assuming the omission was safe.

What the template *does* add locally, because neither is covered by the inherited system prompt:

1. **`ACCOUNT ADDRESS-ON-FILE CHANGE`** — a caller who, mid-collection, asks to update the
   address/DOB *already on file* (referencing "on file," "in your system," "on my account,"
   "on my record") rather than answering the question this node is asking. This is the
   `nodes/README.md` `ACCOUNT/PROFILE MODIFICATION` Railguard's shape (scoped there to nodes
   6a/6b/6c/7/7b/8, not 2h, but the same underlying concern applies here) — routed via
   `info_pivot` rather than silently treated as this node's own answer. I deliberately scoped the
   trigger to explicit "on file"/"in your system" language, not the bare word "address," so it
   doesn't swallow ADDRESS's own in-call `CORRECTIONS` handling (a caller just fixing what they
   told THIS node a moment ago, e.g. "no, it's actually 456 Oak Street") — that's a materially
   different case and stays local to the ADDRESS section, per the same Node 2C lesson but applied
   in the other direction (a trigger that's too broad, not too absent).
2. **`CONSTRAINT PIVOT`** (appointment-type change only) — modeled on `node_6a`'s own
   `CONSTRAINT PIVOT` section, but narrowed to `change_service` only. `node_6a`'s version also
   offers `change_time` / `change_practitioner` / `change_location`, but none of those are
   coherent at this point in the call graph: Node 2h sits between Node 2 (service resolution,
   already just ran) and Node 3 (availability, hasn't run yet) — no time has been offered yet to
   change, and Mandys (the only home-visit clinic today) has exactly one practitioner and one
   location, so those two would never fire anyway. A future multi-practitioner or multi-location
   home-visit clinic might need `change_practitioner`/`change_location` added back in — flagging
   that as a known scope boundary rather than building it speculatively for a clinic that doesn't
   exist yet.

### Slot list

Kept to the three contracted slots (`{{PRACTITIONER_FIRST_NAME}}`, `{{CLINIC_AREA_HINT}}`,
`{{DOB_ORDER_BLOCK}}`) — no new slots added. `{{CLINIC_AREA_HINT}}` is used once, inline in the
ADDRESS section's city-confirmation prompt ("And what city — still {{CLINIC_AREA_HINT}}?") and
again in the full-address readback example. `{{PRACTITIONER_FIRST_NAME}}` is contracted but
unused in the body (see "What these are" above).

## Regression-checklist compliance (`.claude/rules/node-prompt-style.md` Pre-fix Regression Checklist)

1. **PART 2 fall-through only** — the template has no `MANDATORY PART 1 / PART 2` construct at
   all. The one combined spoken+tool turn (`SUBJECT-ON-FILE GATE`'s "nothing to collect" branch)
   is written as a single instruction ("speak one filler phrase... then call...") matching the
   plain `TOOL-CALL FILLER` idiom used throughout the fleet (e.g. Node 2's
   `CONFIRM_SERVICE FILLER RULE`) rather than a two-part label, so there's no step-question text
   to accidentally duplicate into a PART 2.
2. **Scope exceptions inside the block, never globally** — no blanket negative rule is modified
   anywhere in this template; there was nothing to scope an exception against.
3. **Never write "This is NOT a silent turn"** — not present anywhere in the template.
4. **No trigger broadening** — no "when in doubt, include it" language anywhere; every trigger
   (`ACCOUNT ADDRESS-ON-FILE CHANGE`, `CONSTRAINT PIVOT`, the DECLINE/AMBIGUOUS DECLINE lines) is
   written against concrete caller phrasing, per Rule 5's own house convention.
