# CATEGORY BRANCHES — Archetype Templates, Design & Verification

Status: templates written and mechanically verified against the real corpus (byte-diff
harness, throwaway scripts, not committed). No live agent touched. No `nodes/clinics/**`
file modified. `scripts/generate_node2.py` (the generator that will consume these
templates) is being written separately — this document specifies the contract it needs
to honour.

Scope: 19 "Family A" clinics' `nodes/clinics/<slug>/node_2_service_resolution.txt` files,
the `## CATEGORY BRANCHES` section only. 80 `### `-level branches extracted. `mri_first`
is in the Family A clinic list but its equivalent section is named
`## DISAMBIGUATION BRANCHES`, not `## CATEGORY BRANCHES`, and its 11 `### `-level entries
(`HIP_GROUP`, `HAND_GROUP`, `SHOULDER_GROUP`, `WRIST_GROUP`, `ANKLE_GROUP`, `ELBOW_GROUP`,
`SCAPULA_GROUP`, `TMJ_GROUP`, `HAMSTRING_GROUP`, `FOOT_GROUP`, `SPINE_GROUP`) are a
structurally distinct thing — body-part/side/count disambiguation for a radiology clinic
with no patient-status gate anywhere and no service-category concept at all — not a fit
for any of the four branch archetypes below. See §7.

---

## 1. Final archetype taxonomy

The starting hypothesis (GATE 46 / DIRECT 16 / SUBTYPE+GATE 8 / GATE+DURATION 8 / SUBTYPE 1
/ GATE+MULTI 1) was derived from a keyword-heuristic script and is **substantially wrong**
once actually read. Re-derived by reading all 80 branches directly.

| Archetype | Final count | Starting hypothesis | Delta and why |
|---|---|---|---|
| GATE | 23 | 46 | Down. Many "GATE-looking" branches (id count > 2) turned out to be GATE+DURATION with a duration question folded into the "returning" outcome, not a 3rd/4th flat ID; a few more turned out to need SUBTYPE+GATE's more flexible outcome shape. |
| DIRECT | 13 | 16 | Down slightly — a few reclassified once actually read (`HOLISTIC_EXPAND`, `LYMPHATIC_DISAMBIGUATION` are redirect stubs, not resolutions at all). |
| GATE+DURATION | 18 | 8 | Up sharply. This is where most of the "extra ID" branches actually belong: outer 2-way gate, at least one outcome asks a further question before resolving. |
| SUBTYPE+GATE | 22 | 8 | Up sharply, and **absorbs the SUBTYPE hypothesis entirely** (see §1.1) plus a cluster of "flat N-way single question, no patient-status gate" branches that structurally match this shape once you stop assuming the sub-heading has to be `#### `. |
| SUBTYPE (as its own template) | 0 | 1 | **Folded into SUBTYPE+GATE — no separate template built.** See §1.1. |
| GATE+MULTI (as its own template) | 0 | 1 | **Not built — recommended for `patches`.** See §1.2. |
| Recommended for `patches` | 4 | 0 | New finding — see §6. |

Total: 23 + 13 + 18 + 22 + 4 = 80. ✓

### 1.1 Why SUBTYPE was folded into SUBTYPE+GATE, not given its own template

The task's starting hypothesis named exactly one SUBTYPE branch (`palm_beach_osteopathy
RED_LIGHT_THERAPY`). Reading it side by side with the SUBTYPE+GATE branches
(`acacia_healing MOTIVATION_COACHING` etc.) shows **byte-for-byte the same mechanical
skeleton**: an optional pre-note, a `#### <label> (check FIRST...):` or
`#### Single/pack selection:` detection block (keyword rules + a fallback spoken
question), a transition line, then N `#### <PATH> path` sections. The *only* difference
between "SUBTYPE" and "SUBTYPE+GATE" is whether any of the N paths happens to contain its
own nested patient-status gate — which is a property of the **path's content**, not the
branch's outer shape. Since every path body is already an opaque, generator-supplied slot
value (§3.4), a path with no gate and a path with a gate render through the exact same
template. Re-reading confirmed at least 3 branches fit the "SUBTYPE" (no path has a gate)
shape: `kim_gatenby_acupuncture ONLINE_TELEHEALTH`, `meraki_holistic_health
ENERGY_HEALING`, `palm_beach_osteopathy RED_LIGHT_THERAPY` — so it was never really a
singleton to begin with, and building a second, nearly-identical template for it would
have been pure duplication.

### 1.2 Why GATE+MULTI was NOT folded in, and is recommended for `patches`

`ryde_health OSTEOPATHY` (the one branch behind the GATE+MULTI hypothesis; its own header
is itself malformed — see §6) has a genuinely different mechanism from every other
branch in the corpus: a **single gate question whose SELF/OTHER wording changes based on
already-known state** (`practitioner_preference` matching "Deepak"), and **both** the
new-patient and existing-patient outcomes silently fork a second time by that same
already-known practitioner variable — with **no additional caller-facing question**
anywhere. This is structurally distinct from every other archetype:

- Not GATE: GATE's outcomes are flat, single resolutions.
- Not GATE+DURATION: GATE+DURATION's "outcome asks a further question" mechanism is a
  *caller-facing* second question; ryde's fork is silent, driven by state already in the
  conversation.
- Not SUBTYPE+GATE: there's no `#### ` detection-then-paths structure; it's a single
  2-way gate with a hidden third dimension crossed onto each side.

Building a 5th template for a single confirmed instance fails the same "not enough
repetition to justify a template" bar SUBTYPE would have failed had it not turned out to
have siblings. Recommendation: handle via `patches` in `CLINIC_CONFIGS['ryde_health']`
(and fix the malformed header — flagged separately, not by me, per the task brief — while
whoever owns that fix is in the file).

---

## 2. Full branch inventory (clinic → branch → archetype)

`P` = recommended for `patches` instead of an archetype (§6). Branch names shown exactly
as they appear as the `### ` heading text in source (including the malformed ryde_health
header, preserved verbatim for traceability — not fixed here, per the task brief).

| Clinic | Branch | Archetype |
|---|---|---|
| acacia_healing | ACCESS_BARS | GATE+DURATION |
| acacia_healing | HEALING_WITH_NUTRITION | GATE+DURATION |
| acacia_healing | LYMPHATIC_DRAINAGE | GATE+DURATION |
| acacia_healing | MOTIVATION_COACHING | SUBTYPE+GATE |
| acacia_healing | NATUROPATHY | GATE+DURATION |
| acacia_healing | REMEDIAL_MASSAGE | SUBTYPE+GATE |
| acacia_healing | STRUCTURAL_INTEGRATION | SUBTYPE+GATE |
| alpine_osteopaths | OSTEOPATHY | GATE+DURATION |
| balrothery_physio | BIKE_FITTING | DIRECT |
| balrothery_physio | PHYSIOTHERAPY | GATE |
| balrothery_physio | RUNNING_GAIT | DIRECT |
| cascade_womens_health | HYDROTHERAPY | SUBTYPE+GATE |
| cascade_womens_health | MUSCULOSKELETAL | GATE+DURATION |
| cascade_womens_health | TELEHEALTH | DIRECT |
| cascade_womens_health | WOMENS_HEALTH | GATE+DURATION |
| healing_hands_hand_therapy | HAND_THERAPY | GATE |
| healing_hands_hand_therapy | NDIS_HAND | GATE |
| healing_hands_hand_therapy | TELEHEALTH | DIRECT |
| intuitive_health_and_wellness | BREATHWORK | SUBTYPE+GATE |
| intuitive_health_and_wellness | CHINESE_MEDICINE | GATE+DURATION |
| intuitive_health_and_wellness | CHIROPRACTIC | **P** (§6) |
| intuitive_health_and_wellness | EFT_MATRIX | DIRECT |
| intuitive_health_and_wellness | HOLISTIC_EXPAND | **P** (§6) |
| intuitive_health_and_wellness | MASSAGE | SUBTYPE+GATE |
| intuitive_health_and_wellness | NATUROPATHY | GATE |
| intuitive_health_and_wellness | REIKI | SUBTYPE+GATE |
| kim_gatenby_acupuncture | ACUPUNCTURE_INPERSON | GATE+DURATION |
| kim_gatenby_acupuncture | FERTILITY | GATE+DURATION |
| kim_gatenby_acupuncture | ONLINE_TELEHEALTH | SUBTYPE+GATE |
| meraki_holistic_health | ACUPUNCTURE | SUBTYPE+GATE |
| meraki_holistic_health | ENERGY_HEALING | SUBTYPE+GATE |
| meraki_holistic_health | LYMPHATIC_DRAINAGE | SUBTYPE+GATE |
| meraki_holistic_health | MASSAGE | SUBTYPE+GATE |
| meraki_holistic_health | MYOTHERAPY | GATE |
| meraki_holistic_health | VIRTUAL_WELLNESS | GATE |
| mri_first | *(11 DISAMBIGUATION BRANCHES entries)* | out of scope — §7 |
| palm_beach_osteopathy | MANUAL_LYMPHATIC_DRAINAGE | GATE+DURATION |
| palm_beach_osteopathy | OSTEOPATHY | SUBTYPE+GATE |
| palm_beach_osteopathy | RED_LIGHT_THERAPY | SUBTYPE+GATE |
| palm_beach_osteopathy | REMEDIAL_MASSAGE | GATE+DURATION |
| plantar_fascia_clinic | PODIATRY | GATE |
| raymond_terrace_and_tea_gardens_osteopaths | DVA_TYPE | GATE |
| raymond_terrace_and_tea_gardens_osteopaths | EPC_TYPE | GATE+DURATION |
| raymond_terrace_and_tea_gardens_osteopaths | HOME_CARE_TYPE | DIRECT |
| raymond_terrace_and_tea_gardens_osteopaths | STANDARD | GATE+DURATION |
| ryde_health | ACUPUNCTURE | GATE |
| ryde_health | CHIROPRACTIC | GATE |
| ryde_health | MASSAGENo new/returning variant. *(sic — malformed header, §6)* | SUBTYPE+GATE |
| ryde_health | OSTEOPATHYDr Deepak Yagnik has dedicated appointment type IDs. *(sic)* | **P** (§1.2, §6) |
| ryde_health | PHYSIOTHERAPY | GATE |
| ryde_health | PILATES_CONDITIONING | SUBTYPE+GATE |
| speeding_health | CLINICAL_THERAPY | GATE+DURATION |
| speeding_health | FREE_CONSULTATION | SUBTYPE+GATE |
| speeding_health | MASSAGE_RACHEL | SUBTYPE+GATE |
| speeding_health | PILATES | GATE |
| speeding_health | SPORTS_MASSAGE_GLEN | SUBTYPE+GATE |
| taylor_square_osteo_chiro | GENERAL_BOOKING | GATE |
| the_rehab_podiatrist | PODIATRY | GATE+DURATION |
| totally_well | ADVANCED_LYMPHATIC (Tanya Ly only) | GATE |
| totally_well | CLINICAL_LYMPHATIC | GATE |
| totally_well | CRANIOSACRAL (Tanya Ly only) | DIRECT |
| totally_well | FASCIA (Rosario Fernandez or Tanya Ly — Fascia & Cellulite Treatments) | SUBTYPE+GATE |
| totally_well | LYMPHATIC_DISAMBIGUATION | **P** (§6) |
| totally_well | LYMPHOEDEMA (Tanya Ly only — Lymphoedema & Lipoedema Management) | GATE+DURATION |
| totally_well | NATUROPATHY (Tanya Ly only) | GATE |
| totally_well | PACKAGES (TotallyWell Package Deals) | SUBTYPE+GATE |
| totally_well | POST_SURGICAL (Rosario Fernandez or Tanya Ly) | GATE |
| totally_well | PREGNANCY (Rosario Fernandez or Ruby De Paulo) | GATE |
| totally_well | RELAXATION_MASSAGE | SUBTYPE+GATE |
| totally_well | REMEDIAL_MASSAGE | GATE+DURATION |
| village_remedies | ACUPUNCTURE | GATE |
| village_remedies | MASSAGE | DIRECT |
| village_remedies | PHYSIO | DIRECT |
| yandina_podiatry | BULK_BILLED_REFERRAL | DIRECT |
| yandina_podiatry | CHILDRENS_PODIATRY | DIRECT |
| yandina_podiatry | DIABETIC_FOOT | DIRECT |
| yandina_podiatry | FOLLOW_UP_NAIL_SKIN | DIRECT |
| yandina_podiatry | FOOT_PAIN | GATE |
| yandina_podiatry | HEEL_PAIN | GATE |
| yandina_podiatry | SKIN_TOENAIL | GATE |
| yandina_podiatry | SPORTS_INJURY | GATE |

**A note on "GATE" being broader than the starting hypothesis's patient-status framing:**
`raymond_terrace_and_tea_gardens_osteopaths DVA_TYPE` is a **location** gate ("Are you
coming to Raymond Terrace or Tea Gardens?"), not a patient-status one. The GATE template's
question text is a plain slot, not hardcoded to patient-history semantics, specifically so
it generalizes to this case.

**Correction made during verification (§5):** `cascade_womens_health HYDROTHERAPY` and
`totally_well RELAXATION_MASSAGE` were originally assigned GATE (matching GATE's
"one question, 2 flat outcomes" shape) but their *outcome* formatting (an extra
keyword-condition line before `working_type`, or both outcomes described inline under one
header) doesn't match GATE's rigid two-separate-headers-with-working_type-on-its-own-line
shape — they were moved to SUBTYPE+GATE once that mismatch showed up mechanically during
the byte-diff pass, not just theoretically. The table above already reflects the corrected
assignment. `speeding_health FREE_CONSULTATION` has the same kind of mismatch (its own
`2a./2b.` lettered sub-labels plus a pre-scan shortcut don't fit GATE's fixed shape) and
was moved to SUBTYPE+GATE for the same reason — confirmed byte-exact PASS there. The
table above and the §5 totals already reflect all three corrected assignments
(SUBTYPE+GATE final count: 22, not 21 — see §5's updated total below).

---

## 3. Per-archetype design

All four templates live in `nodes/node2_templates/branches/`: `_gate.txt`, `_direct.txt`,
`_gate_duration.txt`, `_subtype_gate.txt`. Each renders **one branch**, starting with the
`### <<BRANCH_NAME>>` heading. None include a trailing `---` — the composer joins
rendered branches with `\n\n---\n\n` (confirmed against source: every branch boundary in
every source file is exactly `<content>\n\n---\n\n### NEXT_BRANCH`, blank line before and
after the separator).

**Line endings:** templates are written LF-only, matching `nodes/node8_templates/node_8_template.txt`
(the closest existing precedent for this `<<SLOT>>` convention) — not CRLF, which the
source `.txt` files actually use. `nodes/node3_templates/*.txt` uses CRLF instead, so the
fleet isn't consistent either way; LF is the safer default since Python's default
text-mode file write on Windows upconverts `\n` → `\r\n` automatically, so whichever
convention `generate_node2.py` uses for its own output write will already normalize this
regardless of the template's own line endings.

**Slot value trailing-whitespace convention (important for the generator):** several
slots (`INTRO_TEXT`, `PRE_GATE_BYPASS`, `PRE_DETECTION_TEXT`, `OUTCOME_*_EXTRA_WORKING_LINES`)
are positioned in the template with **no** literal blank line around them — the slot's
*value* must carry its own trailing blank line (`"\n\n"`) when non-empty, and be the exact
empty string `""` when not applicable. This is the same pattern already used correctly for
DIRECT-shaped slots — the alternative (hardcoding a blank line in the template) would leave
a stray blank line for the many branches that don't have that content at all, which is the
actually-dominant case. Verified against the corpus (see MYOTHERAPY / BIKE_FITTING, both
zero-intro branches, passing byte-exact partly *because* of this convention).

### 3.1 `_gate.txt`

**Base:** composited from the DOMINANT real-corpus conventions rather than one single
branch's exact bytes (no real branch happened to combine all of: Style-A gate-open
wording, the `3./4.` (skip-2) outcome numbering, and the minimal no-payload call line) —
see §4 for why each choice was picked. `meraki_holistic_health MYOTHERAPY` and
`totally_well NATUROPATHY (Tanya Ly only)` are the two real branches that already match
100% of the base's conventions and render byte-exact with zero changes.

Shape: one gate question (2-way; may be patient-status **or any other 2-way disambiguator**
— confirmed necessary by `raymond_terrace DVA_TYPE`, a location gate), each side resolves
directly (no further question).

```
### <<BRANCH_NAME>>

<<INTRO_TEXT>><<PRE_GATE_BYPASS>><<GATE_NUM>>. If {{booking_for}} == "other": ask VARIANT_OTHER ("<<GATE_QUESTION_OTHER>>"). Otherwise: ask VARIANT_SELF ("<<GATE_QUESTION_SELF>>"). Halt.
   Apply CONCERN-GUIDED RESOLUTION RULE case 1 when applicable.

<<OUTCOME_A_NUM>>. <<OUTCOME_A_LABEL>>:
   working_type = "<<OUTCOME_A_TYPE>>"
   working_id = "<<OUTCOME_A_ID>>"
<<OUTCOME_A_EXTRA_WORKING_LINES>>   <<OUTCOME_A_CALL_LINE>>

<<OUTCOME_B_NUM>>. <<OUTCOME_B_LABEL>>:
   working_type = "<<OUTCOME_B_TYPE>>"
   working_id = "<<OUTCOME_B_ID>>"
<<OUTCOME_B_EXTRA_WORKING_LINES>>   <<OUTCOME_B_CALL_LINE>>

<<PRICING_FOOTER>>
```

**Slot table:**

| Slot | Type | Default | Notes |
|---|---|---|---|
| `BRANCH_NAME` | string | required | e.g. `"MYOTHERAPY"` |
| `INTRO_TEXT` | string, must end `\n\n` or be `""` | `""` | free framing sentence(s) before the gate |
| `PRE_GATE_BYPASS` | string, must end `\n\n` or be `""` | `""` | a keyword-triggered silent 3rd path that skips the gate entirely (totally_well pattern — §4.4) |
| `GATE_NUM` | string (digit) | `"1"` | the gate line's own step number; becomes `"3"` when `PRE_GATE_BYPASS` occupies steps 1(–2) |
| `GATE_QUESTION_SELF` / `GATE_QUESTION_OTHER` | string | required | the literal question text, no surrounding quotes |
| `OUTCOME_A_NUM` / `OUTCOME_B_NUM` | string (digit) | `"3"` / `"4"` | fleet convention skips "2" — see §4.2 |
| `OUTCOME_A_LABEL` / `OUTCOME_B_LABEL` | string | `"New patient"` / `"Returning patient"` | no trailing colon (template adds it) |
| `OUTCOME_A_TYPE` / `OUTCOME_B_TYPE` | string | required | → `working_type` and the payload's `appointment_type` |
| `OUTCOME_A_ID` / `OUTCOME_B_ID` | string | required | → `working_id` and the payload's `appointment_type_id` |
| `OUTCOME_A_EXTRA_WORKING_LINES` / `_B_` | string, must end `\n` or be `""` per line | `""` | e.g. `working_patient_status = "new"\nworking_variant_type = "initial"\n`; also covers `practitioner_preference = "..."` (totally_well "Tanya Ly only" pattern) |
| `OUTCOME_A_CALL_LINE` / `_B_` | string (opaque, one logical sentence, no leading `   `) | see §4.3 | the *entire* "speak filler + call the tool" sentence — deliberately opaque, not decomposed further (§4.3 explains why) |
| `PRICING_FOOTER` | string | `""` | verbatim trailing note, e.g. `"Pricing known:\n  ...`" |

**Worked example** (`meraki_holistic_health::MYOTHERAPY`, byte-exact PASS):
```python
{
    'archetype': 'GATE',
    'branch_name': 'MYOTHERAPY',
    'intro_text': '',
    'pre_gate_bypass': '',
    'gate_num': '1',
    'gate_question_self': 'Have you had Myotherapy with us before?',
    'gate_question_other': 'Have they had Myotherapy with us before?',
    'outcome_a': {
        'num': '3', 'label': 'New patient', 'type': 'Myotherapy Initial',
        'id': '1927312838594921970',
        'extra_working_lines': 'working_patient_status = "new"\nworking_variant_type = "initial"\n',
        'call_line': 'Speak one filler phrase from the TOOL-CALL FILLER set, then call '
                     'universal_router intent="confirm_service", per CONFIRM_SERVICE FILLER RULE.',
    },
    'outcome_b': {
        'num': '4', 'label': 'Returning patient', 'type': 'Myotherapy Return',
        'id': '1927313276127938035',
        'extra_working_lines': 'working_patient_status = "existing"\nworking_variant_type = "followup"\n',
        'call_line': 'Speak one filler phrase from the TOOL-CALL FILLER set, then call '
                     'universal_router intent="confirm_service", per CONFIRM_SERVICE FILLER RULE.',
    },
    'pricing_footer': 'Pricing known:\n  Myotherapy (Initial and Return): $140/60min',
}
```

**Worked example 2** (`totally_well::ADVANCED_LYMPHATIC (Tanya Ly only)`, exercises
`PRE_GATE_BYPASS` + `GATE_NUM="3"` + `practitioner_preference`, byte-exact PASS):
```python
{
    'archetype': 'GATE',
    'branch_name': 'ADVANCED_LYMPHATIC (Tanya Ly only)',
    'intro_text': '',
    'pre_gate_bypass': (
        '1. Check caller\'s message for assessment signal ("complete integrative", '
        '"assessment", "integrative assessment"):\n'
        '   If assessment signal: skip gate. Go to Assessment sub-step below.\n\n'
    ),
    'gate_num': '3',
    'gate_question_self': 'Have you had Advanced Lymphatic Therapy with us before?',
    'gate_question_other': 'Have they had Advanced Lymphatic Therapy with us before?',
    'outcome_a': {
        'num': '4', 'label': 'New patient',
        'type': 'Initial appointment - Advanced Lymphatic Drainage', 'id': '1956301037618865267',
        'extra_working_lines': (
            'working_patient_status = "new"\nworking_variant_type = "initial"\n'
            'practitioner_preference = "Tanya Ly" (set this — Tanya is the only '
            'practitioner for this category)\n'
        ),
        'call_line': 'Speak one filler phrase from the TOOL-CALL FILLER set, then call '
                     'universal_router intent="confirm_service". Per CONFIRM_SERVICE FILLER RULE.',
    },
    'outcome_b': { ... },  # symmetric, working_patient_status="existing" etc.
    # NOTE: the "Assessment sub-step:" resolution that PRE_GATE_BYPASS routes to is a
    # THIRD top-level block after outcome B, appended as part of PRICING_FOOTER's slot
    # value in this branch's actual config (the slot is just free text — nothing stops
    # a generator from using it for "whatever comes after outcome B" when needed).
    'pricing_footer': (
        'Assessment sub-step:\n   working_type = "Complete Integrative Lymphatic Assessment"\n'
        '   working_id = "1956319957167907958"\n   practitioner_preference = "Tanya Ly"\n'
        '   Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router '
        'intent="confirm_service". Per CONFIRM_SERVICE FILLER RULE.\n\n'
        'Pricing known:\n  Initial: $160/60min\n  Return: $160/60min\n'
        '  Complete Integrative Assessment: $260/90min'
    ),
}
```

### 3.2 `_direct.txt`

**Base:** `balrothery_physio::BIKE_FITTING` (byte-exact PASS with all optional slots
empty).

```
### <<BRANCH_NAME>>

<<INTRO_TEXT>>
<<CONCERN_GUIDED_LINE>><<WORKING_VARS_BLOCK>>Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "<<APPOINTMENT_TYPE>>", "appointment_type_id": "<<APPOINTMENT_TYPE_ID>>"<<EXTRA_PAYLOAD_FIELDS>>}. HALT.

<<PRICING_FOOTER>>
```

**Slot table:**

| Slot | Type | Default | Notes |
|---|---|---|---|
| `BRANCH_NAME` | string | required | |
| `INTRO_TEXT` | string | `""` | one framing line, no trailing blank needed — template's own line-3 already provides it |
| `CONCERN_GUIDED_LINE` | string, must end `\n` or be `""` | the dominant sentence (§4.1) | empty for the ~4/13 branches (mostly `raymond_terrace`) whose source never mentions CONCERN-GUIDED at all in this section |
| `WORKING_VARS_BLOCK` | string, must end `\n` per line or `""` | `""` | `working_type = "..."\nworking_id = "..."\n` pre-declaration, present in ~half the corpus |
| `APPOINTMENT_TYPE` / `APPOINTMENT_TYPE_ID` | string | required | |
| `EXTRA_PAYLOAD_FIELDS` | string | `""` | e.g. `, "variant_type": "bike_fitting"` — leading comma+space included in the value |
| `PRICING_FOOTER` | string | `""` | |

**Escape hatch (documented, not templated):** 6 of the 13 DIRECT branches use a call-line
shape this template's fixed structure doesn't cover at all — no `payload={}` spelled out
(`totally_well CRANIOSACRAL`, `intuitive_health_and_wellness EFT_MATRIX`: bare
`Call universal_router intent="confirm_service".`), or the filler-then-call sentence order
reversed (`raymond_terrace HOME_CARE_TYPE`: call description *then* "Speak..."), or curly
quotes plus the same reversed order (`village_remedies MASSAGE`/`PHYSIO`). Given this is
6/13 (nearly half) — a real, load-bearing minority, not noise — the generator's
`CLINIC_CONFIGS` shape should accept an optional `resolution_override` string per DIRECT
branch: when present, it fully replaces
`<<CONCERN_GUIDED_LINE>><<WORKING_VARS_BLOCK>>Call universal_router...HALT.` verbatim,
bypassing `APPOINTMENT_TYPE`/`APPOINTMENT_TYPE_ID`/`EXTRA_PAYLOAD_FIELDS` entirely for that
branch. This is the same escape-hatch shape as `patches`, just scoped to one branch's
resolution line instead of the whole file.

**Worked example** (`balrothery_physio::BIKE_FITTING`, byte-exact PASS):
```python
{
    'archetype': 'DIRECT',
    'branch_name': 'BIKE_FITTING',
    'intro_text': 'No new/returning distinction.',
    'concern_guided_line': (
        'Apply CONCERN-GUIDED RESOLUTION RULE case 2 when applicable (empathetic line + '
        'tool call in same turn, ONLY if a symptom is present in caller\'s message AND this '
        'is the first turn — no prior question asked in this node entry). All other cases: '
        'speak one filler phrase from the TOOL-CALL FILLER set, then the tool call, per '
        'CONFIRM_SERVICE FILLER RULE.\n'
    ),
    'working_vars_block': '',
    'appointment_type': 'Bike Fitting',
    'appointment_type_id': '1878546243978791940',
    'extra_payload_fields': ', "variant_type": "bike_fitting"',
    'pricing_footer': '',
}
```

**Worked example 2** (`yandina_podiatry::CHILDRENS_PODIATRY`, exercises `INTRO_TEXT` +
patient-status fields in `EXTRA_PAYLOAD_FIELDS`, byte-exact PASS):
```python
{
    'archetype': 'DIRECT',
    'branch_name': 'CHILDRENS_PODIATRY',
    'intro_text': (
        "Caller is booking a child's initial podiatry consultation.\n\n"
        "No gate — no new/returning distinction (children's initial only)."
    ),
    'concern_guided_line': (
        'Apply CONCERN-GUIDED RESOLUTION RULE case 2 when applicable (empathetic line + tool '
        'call in same turn, ONLY if a symptom is present in caller\'s message AND no gate '
        'question was asked). All other cases: speak one filler phrase from the TOOL-CALL '
        'FILLER set, then the tool call, per CONFIRM_SERVICE FILLER RULE.\n'
    ),
    'working_vars_block': '',
    'appointment_type': "Children's Podiatry – Initial Consultation ($120)",
    'appointment_type_id': '1962696870551629229',
    'extra_payload_fields': (
        ', "patient_status": "new", "variant_type": "private" [+ CONTEXT PIGGYBACK: add '
        'booking_for, family_member_name, timeframe_raw, practitioner_preference if '
        'captured anywhere in conversation]'
    ),
    'pricing_footer': 'Pricing not known — handled by PRICING QUERY.',
}
```

### 3.3 `_gate_duration.txt`

**Base:** composited (same reasoning as `_gate.txt` — no single branch happens to
embody every dominant convention at once); `acacia_healing NATUROPATHY` and 10 other
branches render byte-exact from it unmodified.

Shape: one 2-way gate (same generalization as GATE — patient-status, location,
practitioner-choice all attested), where **at least one** side's resolution is itself a
further question (duration, sub-type, location) rather than a flat ID.

```
### <<BRANCH_NAME>>

<<INTRO_TEXT>><<PRE_GATE_BYPASS>><<GATE_NUM>>. If {{booking_for}} == "other": ask VARIANT_OTHER ("<<GATE_QUESTION_OTHER>>"). Otherwise: ask VARIANT_SELF ("<<GATE_QUESTION_SELF>>"). Halt.
   Apply CONCERN-GUIDED RESOLUTION RULE case 1 when applicable.

<<OUTCOME_A_NUM>>. <<OUTCOME_A_LABEL>>
<<OUTCOME_A_BODY>>

<<OUTCOME_B_NUM>>. <<OUTCOME_B_LABEL>>
<<OUTCOME_B_BODY>>

<<PRICING_FOOTER>>
```

Note `OUTCOME_A_LABEL` here (unlike GATE's) has **no fixed trailing colon** in the
template — the label slot must supply its own, because real branches attach extra prose
directly onto the label line before the colon (e.g.
`"New patient -- TURN 1/2 GUARD: Even if the caller states a duration preference..."` is
the *entire* label — the colon that follows "GUARD" is not a section-header colon, it's
mid-sentence). Found this the hard way: `palm_beach_osteopathy MANUAL_LYMPHATIC_DRAINAGE`
/ `REMEDIAL_MASSAGE` both have this shape and were the reason the template's trailing `:`
was removed from the label line in favour of making it part of the slot value.

**Slot table:**

| Slot | Type | Default | Notes |
|---|---|---|---|
| `BRANCH_NAME`, `INTRO_TEXT`, `PRE_GATE_BYPASS`, `GATE_NUM`, `GATE_QUESTION_SELF/OTHER` | — | — | identical contract to `_gate.txt` |
| `OUTCOME_A_NUM` / `OUTCOME_B_NUM` | string | `"2"` / `"3"` | GATE+DURATION's dominant numbering does NOT skip 2 (unlike plain GATE) — confirmed against all 11 byte-exact passes |
| `OUTCOME_A_LABEL` / `OUTCOME_B_LABEL` | string, includes its own trailing `:` | `"New patient:"` / `"Returning patient:"` | see note above — can be a whole sentence, not just a two-word label |
| `OUTCOME_A_BODY` / `OUTCOME_B_BODY` | string (fully opaque) | required | the entire resolution for that side — may be a flat 1-ID resolution (DIRECT-shaped), a nested question with N answers (GATE-outcome-shaped or richer), or a redirect into another branch's flow. See §3.5 for how a config author should build this without hand-typing duplicate prose. |
| `PRICING_FOOTER` | string | `""` | in practice almost always `""` here — pricing is normally already inside the last `OUTCOME_B_BODY` |

**Why `OUTCOME_A_BODY`/`OUTCOME_B_BODY` are fully opaque, not decomposed further:**
attempted decomposition and gave up deliberately. The real shapes observed across the 18
GATE+DURATION branches include: a flat 1-ID resolution (majority of "New patient" sides);
a `TURN 1 / TURN 2` two-option duration question; a `TURN 1 / TURN 2` question with a
silent "DURATION PRE-SCAN" keyword shortcut bolted on (`cascade_womens_health
MUSCULOSKELETAL`/`WOMENS_HEALTH`); a 5-way sub-type question (`WOMENS_HEALTH`'s "New
patient" side); a location question with its own 2 sub-outcomes
(`raymond_terrace EPC_TYPE`); a full nested gate-shaped block
(`raymond_terrace STANDARD`, `intuitive_health_and_wellness CHINESE_MEDICINE`'s
4-way-with-one-path-having-a-3rd-level-duration-question). No 2–3 field slot set covers
this without either (a) silently dropping real structure for the more complex cases, or
(b) becoming a second, parallel implementation of SUBTYPE+GATE's path mechanism inside
GATE+DURATION. Given the config author (generator) is free to build each
`OUTCOME_*_BODY` string using whatever composition helper it wants (§3.5), decomposition
value isn't actually lost — it's just pushed one layer into the generator's own helper
functions instead of the `.txt` template.

### 3.4 `_subtype_gate.txt`

**Base:** `acacia_healing MOTIVATION_COACHING` (byte-exact PASS, along with 20 others —
this archetype had the highest pass rate of all four, see §5).

```
### <<BRANCH_NAME>>

<<PRE_DETECTION_TEXT>><<DETECTION_BLOCK>>

<<PATHS>>

<<PRICING_FOOTER>>
```

**Slot table:**

| Slot | Type | Default | Notes |
|---|---|---|---|
| `BRANCH_NAME` | string | required | |
| `PRE_DETECTION_TEXT` | string, must end `\n\n` or be `""` | `""` | clinic-specific framing before detection starts — e.g. `meraki ENERGY_HEALING`'s "BOOKABLE ENERGY SERVICES:" note, `palm_beach RED_LIGHT_THERAPY`'s "IMPORTANT:.../PRACTITIONER EXCEPTION:..." block, or `speeding_health MASSAGE_RACHEL`'s entire GENDER GATE flow (§3.4.1) |
| `DETECTION_BLOCK` | string (opaque, starts with the detection heading itself) | required | everything from `#### Sub-type detection (check FIRST...)` / `#### Practitioner detection...` / `#### Single/pack selection:` (or, for the degenerate numbered-label variant, `1. Check caller's message for...`) through to (not including) the blank line before the first path |
| `PATHS` | string (opaque) | required | the entire concatenation of every `#### <NAME> path` section (or, for the numbered-label variant, every `2a./2b./...` or `3. Map duration:`-style section) — **this is where pricing usually already lives**, per-path, not as a separate footer |
| `PRICING_FOOTER` | string | `""` | rarely used for this archetype — kept for symmetry with the other three, and because a couple of branches (`meraki ENERGY_HEALING`) do have one final "Pricing known:" line that's arguably branch-level rather than path-level; ambiguous, harmless either way since it's opaque text regardless of which slot it lands in |

**This archetype also covers the "flat N-way, no patient-status gate" cluster** that
doesn't fit GATE's rigid 2-outcome shape: `totally_well FASCIA` (4-way sub-type, numbered
`2a./2b./2c./2d.` labels, no `#### `), `totally_well PACKAGES` (3-way, same numbered
style), `speeding_health SPORTS_MASSAGE_GLEN` (3-way duration mapping, single inline
"3. Map duration:" step, no separately-headed paths at all), `ryde_health MASSAGENo
new/returning variant.` (4-way duration mapping, prose-only, no numbering or `#### ` at
all — "DURATION LOOKUP ORDER:" then "Duration → confirm_service mapping:"). All four fit
because `DETECTION_BLOCK`/`PATHS` genuinely don't care what heading convention is used
inside them — the template only asserts an outer skeleton (optional pre-text, detection,
blank line, paths, blank line, optional footer), which every one of these branches
satisfies even though their *internal* labelling conventions differ a lot. This was
confirmed empirically, not just argued: the byte-diff harness (§5) passes all four
without any special-casing in the extractor beyond "split before the first blank line
that's followed by a path-looking line, or (for branches with no `#### ` at all) don't
split at all and put everything in `PATHS`."

**Also covers `meraki_holistic_health LYMPHATIC_DRAINAGE`**, which is practitioner-choice
(not patient-status) as the detection question, with 3 named outcomes (Elena/Casey/no
preference) rather than 2 — doesn't fit GATE+DURATION's fixed 2-outcome-slot shape, but
fits SUBTYPE+GATE trivially (3 paths, one of which — "no preference" — is a one-line
redirect into another path's flow).

#### 3.4.1 Worked example — the degenerate "SUBTYPE" case (no path has a gate)

`kim_gatenby_acupuncture::ONLINE_TELEHEALTH`, byte-exact PASS:
```python
{
    'archetype': 'SUBTYPE+GATE',
    'branch_name': 'ONLINE_TELEHEALTH',
    'pre_detection_text': '',
    'detection_block': (
        'No patient status gate for any online type — all online appointment types are '
        'self-describing. Route directly after sub-type is resolved.\n\n'
        '#### Sub-type detection (check FIRST):\n'
        'Evaluate in order — stop at first match:\n'
        '1. Message contains "fertility" or "IVF" → ONLINE_FERTILITY path.\n'
        '... (full keyword table + fallback question + "On reply to step 5:" line)'
    ),
    'paths': (
        '#### ONLINE_FERTILITY path:\n'
        'working_type = "Online Fertility Initial Consultation"\n'
        'working_id = "452211"\n...\n\n'
        '#### ONLINE_NONFERTILITY_INITIAL path:\n...\n\n'
        '#### TELEHEALTH_30 path:\n...\n\n'
        '#### TELEHEALTH_SHORT path:\n...'
    ),
    'pricing_footer': '',
}
```

#### 3.4.2 Worked example — practitioner-choice outer question + a redirect path

`meraki_holistic_health::LYMPHATIC_DRAINAGE`, byte-exact PASS:
```python
{
    'archetype': 'SUBTYPE+GATE',
    'branch_name': 'LYMPHATIC_DRAINAGE',
    'pre_detection_text': (
        'Elena has separate initial and return appointment types. Casey has a single type '
        '(no gate required).\n\nIMPORTANT: Caller may say "lymphatic drainage", "lymphatic '
        'massage", "manual lymphatic", "MLD", or "lymph". Always ask for practitioner '
        'preference before routing.\n\n'
    ),
    'detection_block': (
        '1. Ask (SELF) "We have two practitioners for Lymphatic Drainage -- Elena or Casey. '
        'Do you have a preference?" (OTHER) "Do they have a preference between Elena or '
        'Casey?" Halt.'
    ),
    'paths': (
        '2. Elena:\n   Ask (SELF) "Have you had Lymphatic Drainage with us before?" ...\n\n'
        '3. Casey:\n   working_type = "Manual Lymphatic Drainage"\n   working_id = '
        '"1907182769075651738"\n   Speak one filler phrase...\n\n'
        '4. No preference / unsure:\n   Apply Elena\'s new/existing gate (step 2 above). '
        'Route to the matching Elena appointment type.'
    ),
    'pricing_footer': (
        'Pricing known:\n  Elena — Lymphatic Drainage Initial: $130/60min\n'
        '  Elena — Lymphatic Drainage Return: $105/60min\n'
        '  Casey — Manual Lymphatic Drainage: $140/60min'
    ),
}
```

### 3.5 Composer contract (for `generate_node2.py`, not built by this task)

Per-clinic `CLINIC_CONFIGS[<slug>]['branches']` should be a list of dicts, each with an
`archetype` key selecting which of the four `TEMPLATE_FILES`/`BRANCH_TEMPLATES` entries to
render, plus the fields from that archetype's slot table above. The branch composer joins
rendered branches with `"\n\n---\n\n"` (confirmed exact separator spacing against every
branch boundary in the corpus — see §3, "None include a trailing `---`"). Recommend a
small shared helper, e.g. `render_leaf(type, id, status=None, variant=None,
practitioner_preference=None, business_id=None, business_name=None, call_style="minimal"
| "full")`, used internally by GATE/DIRECT rendering AND by hand-built `OUTCOME_*_BODY` /
`PATHS` strings for GATE+DURATION/SUBTYPE+GATE — this keeps the "same shape, repeated"
value DRY in the generator even though the `.txt` templates themselves don't enforce it.

---

## 4. Normalised drift

Per the brief, differences that express *the same rule* with different wording were
folded to the most common form rather than kept as slots. Every item below changes
**wording or structural framing only** — never a service name, ID, spoken phrase's
substance, or logic branch.

### 4.1 Gate-question opening style — 3 variants folded to 1

| Style | Count (of ~64 gate-shaped branches surveyed) | Example |
|---|---|---|
| **A (chosen as template default):** `N. If {{booking_for}} == "other": ask VARIANT_OTHER ("Q"). Otherwise: ask VARIANT_SELF ("Q"). Halt.` | 33 | `acacia_healing` family |
| B: `N. Gate (...):\n   Apply CONCERN-GUIDED...\n   (SELF) Ask VARIANT_SELF: "Q" HALT. ...\n   (OTHER) Ask VARIANT_OTHER: "Q" HALT.` | 6 | `balrothery_physio PHYSIOTHERAPY`, `yandina_podiatry` x4 |
| C: same as B but without the `VARIANT_SELF`/`VARIANT_OTHER` macro names | 2 | `village_remedies ACUPUNCTURE`, `healing_hands NDIS_HAND` |

Style A was already the plurality and is also the only one of the three that's a single
self-contained sentence (B/C spread the same information across 4 lines with an embedded
`Apply CONCERN-GUIDED...` line in a different position) — picking it also normalizes away
the `CONCERN-GUIDED` line's position drift for free. Affects 8 branches in the final
byte-diff table (§5): `balrothery_physio PHYSIOTHERAPY`, `healing_hands_hand_therapy
HAND_THERAPY`/`NDIS_HAND`, `village_remedies ACUPUNCTURE`, `yandina_podiatry FOOT_PAIN`/
`HEEL_PAIN`/`SKIN_TOENAIL`, `speeding_health PILATES` (Style A already, but with an extra
"Do NOT proceed to step 2 or 3..." sentence folded away — see 4.1a).

**4.1a — trailing enforcement sentences folded away.** A handful of Style-A branches
append `" Do NOT proceed to step 2 or 3 until the caller answers."` or similar after
`Halt.` (e.g. `speeding_health PILATES`, `intuitive_health_and_wellness NATUROPATHY`).
This is pure reinforcement of what `Halt.` already means system-wide (see
`nodes/shared/system_prompt.txt`'s own `HALT` definition, referenced fleet-wide) — folded
to the bare `Halt.` sentence.

### 4.2 Outcome numbering — "skip 2" is the dominant GATE convention, kept as-is (not "fixed")

GATE-archetype outcome blocks are numbered `1(gate), 3(new), 4(existing)` in the
plurality of branches (30 "3. New patient:" + 22 "4. Returning patient:" occurrences vs.
16 "2. New patient:" + 12 "3. Returning patient:"). **This is very likely the exact same
class of copy-propagated numbering defect already documented for the `## RULES` section**
in `.claude/rules/node2-template-builder-plan.md` §6.1 ("21 of 25 clinics... number them
`1. 3. 4. 5. 5. 6.` — rule 2 missing") — just showing up in a different section of the
same files. Per the brief's own instruction ("pick the best/most common wording"), the
template defaults to the dominant `3./4.` form since that's what "most common" means
here — but this is **not the same as calling it correct**. Flagging for the user's
separate judgement, same as the RULES numbering bug: worth a deliberate decision (fix to
sequential `1/2/3`, or leave as the fleet's de facto style) rather than silently
perpetuating it. GATE+DURATION, by contrast, genuinely does NOT skip 2 in its dominant
form (confirmed against all 11 byte-exact GATE+DURATION passes, all numbered `1/2/3`) —
so this is specific to the GATE archetype, not universal.

### 4.3 Call-line style — two real conventions, one chosen as canonical

Exactly 23 of ~64 surveyed branches spell out the full `payload={...}` JSON inline
("full"); another 23 just say `call universal_router intent="confirm_service", per
CONFIRM_SERVICE FILLER RULE.` and rely entirely on the shared `## CONFIRM_SERVICE CALL
FORMAT` section (present once, outside `CATEGORY BRANCHES`, in every file) to construct
the actual payload from `working_type`/`working_id`/etc. This is a genuine 50/50,
clinic-level (not random) convention split — `meraki_holistic_health`,
`palm_beach_osteopathy`, `intuitive_health_and_wellness`, `plantar_fascia_clinic`,
`taylor_square_osteo_chiro`, `totally_well` consistently use "minimal"; `village_remedies`,
`acacia_healing`, `balrothery_physio`, `healing_hands_hand_therapy`, `yandina_podiatry`,
`cascade_womens_health` consistently use "full". **Not normalized away** — modeled as the
fully opaque `OUTCOME_*_CALL_LINE` slot (§3.1) precisely because both are legitimate,
stable, clinic-level choices, not noise. The template's *default value* (used when a
config doesn't override it) is the minimal form, matching the base branches
(`MYOTHERAPY`/`NATUROPATHY`) — but a generator config is expected to supply the clinic's
real convention explicitly for every branch, not rely on the default, once wired up for
real. Filler-phrase-before-call ordering is dominant either way (120 "speak then call" vs.
51 "call... then mention speak") and both base branches already use it.

### 4.4 Curly quotes — 4 clinics, cosmetic only

`meraki_holistic_health` (1 branch), `plantar_fascia_clinic` (1), `taylor_square_osteo_chiro`
(1), `village_remedies` (2, only in `MASSAGE`/`PHYSIO` — `ACUPUNCTURE` in the same file
uses straight quotes) use `“”` instead of `"` in places, apparently from being
copy-pasted through a word processor at some point. Normalized to straight quotes
fleet-wide — doesn't affect model behaviour (Haiku doesn't distinguish curly vs. straight
quotes semantically) and is exactly the kind of typographic drift the brief calls out as
worth cleaning up. Affects `taylor_square_osteo_chiro GENERAL_BOOKING`'s diff row in §5.

### 4.5 `CONFIRM_SERVICE FILLER RULE` capitalisation — not a real choice, left alone

136 lowercase `"per CONFIRM_SERVICE FILLER RULE"` vs. 92 capitalized `"Per..."` occurrences
initially looked like a normalizable pair, but they're not actually the same rule
differently worded — capitalisation here is ordinary English sentence-position grammar
(mid-sentence after a comma → lowercase; start of a new sentence after a period →
capital). Each template's fixed text already reproduces the grammatically correct form
for its position; no slot needed.

### 4.6 Missing working-vars pre-declaration — NOT normalized (kept as a real gap, §5)

`ryde_health`'s `ACUPUNCTURE`/`CHIROPRACTIC`/`PHYSIOTHERAPY` skip the
`working_type =`/`working_id =` pre-declaration lines that ~90% of GATE branches have,
going straight from the outcome header to the `Call universal_router...` line with the
type/id spelled out only inline in the payload. Initially considered folding this into
"drift" (add the lines everyone else has) but decided against it: unlike the gate-question
style or numbering, this isn't "the same rule worded differently" — it's the *absence* of
declared intermediate state that OTHER parts of `ryde_health`'s own file might reasonably
assume aren't there. Left as a genuine template mismatch, documented in §5, not papered
over.

---

## 5. Verification

Methodology: a throwaway Python harness (`render.py` + `verify*.py`, in the session
scratchpad, not committed) that (1) auto-extracts a slot config from each branch's real
source text via regex/string-split, (2) renders it through the matching archetype
template using pure `<<SLOT>>` string substitution — the same mechanism
`generate_node8.py` already uses in this repo — and (3) diffs the rendered output against
the original branch text (trailing-blank-line-normalized only; internal content
untouched). Each of the 4 templates was iterated against real failures until the
extractor's remaining gaps were genuine structural/stylistic variance, not extractor
bugs — confirmed by manually reading every failure's diff, not just trusting the pass
count.

**Summary (76 branches — 4 recommended-for-`patches` branches excluded, they were never
attempted against a template on purpose):**

| Archetype | Byte-exact PASS | DIFF (confirmed = intentional normalisation only, §4) | NOPARSE (genuine structural variant, not attempted) | Total |
|---|---|---|---|---|
| GATE | 6 | 10 | 7 | 23 |
| DIRECT | 7 | 0 | 6 | 13 |
| GATE+DURATION | 11 | 0 | 7 | 18 |
| SUBTYPE+GATE | 22 | 0 | 0 | 22 |
| **Total** | **46** | **10** | **20** | **76** |

46/76 (61%) byte-exact on the first structural design, with a further 10/76 (13%)
confirmed to differ *only* in the exact ways §4 documents as intentional (every DIFF's
unified diff was read, not just counted — none contained an unexpected change). That's
56/76 (74%) either byte-exact or exact-modulo-documented-normalisation. The remaining
20/76 (26%) are real gaps — every one individually named and reasoned about below, not a
silent bucket.

### 5.1 PASS — byte-exact (45)

GATE (6): `meraki_holistic_health` MYOTHERAPY, VIRTUAL_WELLNESS; `totally_well`
ADVANCED_LYMPHATIC (Tanya Ly only), CLINICAL_LYMPHATIC, NATUROPATHY (Tanya Ly only),
POST_SURGICAL (Rosario Fernandez or Tanya Ly).

DIRECT (7): `balrothery_physio` BIKE_FITTING, RUNNING_GAIT; `healing_hands_hand_therapy`
TELEHEALTH; `yandina_podiatry` BULK_BILLED_REFERRAL, CHILDRENS_PODIATRY, DIABETIC_FOOT,
FOLLOW_UP_NAIL_SKIN.

GATE+DURATION (11): `acacia_healing` ACCESS_BARS, HEALING_WITH_NUTRITION,
LYMPHATIC_DRAINAGE, NATUROPATHY; `alpine_osteopaths` OSTEOPATHY; `cascade_womens_health`
MUSCULOSKELETAL, WOMENS_HEALTH; `palm_beach_osteopathy` MANUAL_LYMPHATIC_DRAINAGE,
REMEDIAL_MASSAGE; `the_rehab_podiatrist` PODIATRY; `totally_well` LYMPHOEDEMA (Tanya Ly
only — Lymphoedema & Lipoedema Management).

SUBTYPE+GATE (22, i.e. all of them): `acacia_healing` MOTIVATION_COACHING,
REMEDIAL_MASSAGE, STRUCTURAL_INTEGRATION; `cascade_womens_health` HYDROTHERAPY;
`intuitive_health_and_wellness` BREATHWORK, MASSAGE, REIKI; `kim_gatenby_acupuncture`
ONLINE_TELEHEALTH; `meraki_holistic_health` ACUPUNCTURE, ENERGY_HEALING,
LYMPHATIC_DRAINAGE, MASSAGE; `palm_beach_osteopathy` OSTEOPATHY, RED_LIGHT_THERAPY;
`ryde_health` MASSAGENo new/returning variant., PILATES_CONDITIONING; `speeding_health`
FREE_CONSULTATION, MASSAGE_RACHEL, SPORTS_MASSAGE_GLEN; `totally_well` FASCIA (Rosario
Fernandez or Tanya Ly — Fascia & Cellulite Treatments), PACKAGES (TotallyWell Package
Deals), RELAXATION_MASSAGE.

### 5.2 DIFF — confirmed intentional-normalisation-only (10, all GATE)

Every row below: the unified diff touches *only* the gate-question wording/style (§4.1),
the outcome-numbering-adjacent framing, or curly-quote normalisation (§4.4) — never a
service name, ID, or added/removed logic. Full diffs were generated and read; abbreviated
here.

| Branch | What differs |
|---|---|
| `balrothery_physio PHYSIOTHERAPY` | Style B → A (§4.1) |
| `healing_hands_hand_therapy HAND_THERAPY` | Style B → A |
| `healing_hands_hand_therapy NDIS_HAND` | Style C → A |
| `speeding_health PILATES` | Style A already; trailing "Do NOT proceed..." sentence dropped (§4.1a) |
| `taylor_square_osteo_chiro GENERAL_BOOKING` | curly → straight quotes only (§4.4) |
| `totally_well PREGNANCY (Rosario Fernandez or Ruby De Paulo)` | non-patient-status "Ask sub-type:" opening → Style A framing (still 2-way, same question text, same 2 outcomes) |
| `village_remedies ACUPUNCTURE` | Style C → A |
| `yandina_podiatry FOOT_PAIN` | Style B → A |
| `yandina_podiatry HEEL_PAIN` | Style B → A |
| `yandina_podiatry SKIN_TOENAIL` | Style B → A |

### 5.3 NOPARSE — genuine structural gaps, not attempted via auto-extraction (21)

Every one of these was read by hand (not just regex-failed) to confirm it's a real
structural variant, not an extractor bug. Grouped by root cause:

**No inline question text — question defined elsewhere in the file (2):**
`intuitive_health_and_wellness NATUROPATHY`, `plantar_fascia_clinic PODIATRY`. Both say
`ask VARIANT_OTHER. Otherwise: ask VARIANT_SELF.` with no `("...")` — the actual spoken
question is defined once, by name, in a `TEMPLATES`-style block elsewhere in the file
(outside `CATEGORY BRANCHES`, so outside this task's extraction scope). Structurally these
ARE plain GATE branches; a real `generate_node2.py` config would just hardcode the actual
question text (which the config author reads from the whole file, not just this section),
sidestepping the issue entirely. Not a template design problem.

**No working_type/working_id pre-declaration (3):** `ryde_health` ACUPUNCTURE,
CHIROPRACTIC, PHYSIOTHERAPY. See §4.6 — deliberately not normalized away.

**Gate question isn't self/other-variant at all (3):** `raymond_terrace_and_tea_gardens_osteopaths`
DVA_TYPE (GATE), EPC_TYPE, STANDARD (GATE+DURATION). All three use a single **location**
question ("Are you coming to Raymond Terrace or Tea Gardens?") that's asked identically
regardless of `booking_for` — no VARIANT_SELF/VARIANT_OTHER split at all. The templates'
fixed "ask VARIANT_OTHER (...). Otherwise: ask VARIANT_SELF (...)." framing assumes a
split exists; forcing these through would produce a redundant (not wrong, just verbose)
self/other branching for a question that doesn't need one. Recommend: either accept the
harmless redundancy (set `GATE_QUESTION_SELF == GATE_QUESTION_OTHER`), or extend the
generator (not the template) with a `single_question` flag that swaps the two-clause gate
line for a plain `<<GATE_NUM>>. <<GATE_QUESTION>> HALT.` line when set. Not built here —
flagging the choice rather than silently picking one.

**Non-standard outcome-block shape (0 remaining):** `cascade_womens_health HYDROTHERAPY`,
`totally_well RELAXATION_MASSAGE`, and `speeding_health FREE_CONSULTATION` all originally
failed GATE extraction for this reason (an extra keyword-condition line before
`working_type`, both outcomes described inline under one header, or `2a.`/`2b.` lettered
sub-labels plus a pre-scan shortcut) — all three were reclassified to SUBTYPE+GATE and
now PASS byte-exact; see the correction note in §2. Kept as their own category here only
as a record of why the initial GATE attempt failed for these three specifically.

**One outcome doesn't resolve to an ID at all (1):** `yandina_podiatry SPORTS_INJURY`.
"New patient" outcome is a *redirect* ("Sports injury initial appointments aren't
available to book by phone... is there something else I can help with...") with zero
tool call, not a `working_type`/`working_id` resolution — a real, valid GATE variant the
template's rigid `working_type =` / `working_id =` fixed lines don't accommodate for that
one side. Recommend a `resolution_override` per-outcome escape hatch identical in spirit
to DIRECT's (§3.2), scoped to a single `OUTCOME_*` slot group instead of the whole branch.

**No Style-A gate-open line at all (GATE+DURATION, 7):** `intuitive_health_and_wellness
CHINESE_MEDICINE`, `kim_gatenby_acupuncture` ACUPUNCTURE_INPERSON, FERTILITY,
`raymond_terrace...` EPC_TYPE, STANDARD (also in the "location, not self/other" group
above — counted once here), `speeding_health CLINICAL_THERAPY`, `totally_well
REMEDIAL_MASSAGE`. All use Style B or C gate-opening (§4.1) — the GATE+DURATION
auto-extractor only implements Style-A matching (a scope cut made to manage the task's
time budget, not a design limitation — the same flexible SELF/OTHER-pattern matching
built for the GATE extractor would work here too, un-ported). Manually spot-checked
`kim_gatenby_acupuncture ACUPUNCTURE_INPERSON` by hand: confirms the archetype fits
(2-way gate → new:1 ID, existing: TURN1/TURN2 45-or-60-minute question), it would render
as a DIFF (Style B → A), not a real gap, if the extractor were extended. Recommend
porting the GATE extractor's flexible question-matching into the GATE+DURATION path
before relying on this list as final — it's very likely all 7 resolve to DIFF, not
NOPARSE, the same way the analogous GATE cases did.

**DIRECT call-line shape not covered (6):** `cascade_womens_health TELEHEALTH`,
`intuitive_health_and_wellness EFT_MATRIX`, `raymond_terrace_and_tea_gardens_osteopaths
HOME_CARE_TYPE`, `totally_well CRANIOSACRAL (Tanya Ly only)`, `village_remedies MASSAGE`,
`PHYSIO`. See the DIRECT escape-hatch note in §3.2 — recommend `resolution_override`.

---

## 6. Branches recommended for `patches`, not an archetype (4)

| Branch | Why |
|---|---|
| `ryde_health OSTEOPATHYDr Deepak Yagnik has dedicated appointment type IDs.` (sic) | GATE+MULTI shape — silent practitioner-based fork on both gate outcomes, no caller-facing 2nd question. Genuine singleton; see §1.2. Also: this branch's own `### ` header is malformed — the clinic's branch note ("Dr Deepak Yagnik has dedicated appointment type IDs.") is welded directly onto the branch name with no separating newline (`nodes/clinics/ryde_health/node_2_service_resolution.txt:379`). **This is the same bug already flagged and assigned to someone else per the task brief — noted here only so this branch's config in the generator handles the real (malformed) name sanely; not fixed, not re-flagged as new.** |
| `ryde_health MASSAGENo new/returning variant.` (sic) | Same malformed-header bug, same file, line 415 (`nodes/clinics/ryde_health/node_2_service_resolution.txt:415`). This branch itself DOES fit SUBTYPE+GATE cleanly (§2) — only the header text is malformed, not the archetype fit. Flagging here for the same reason as above (config should use the real, malformed name), not proposing a fix. |
| `intuitive_health_and_wellness HOLISTIC_EXPAND` | Not a resolution at all — a 3-line redirect stub ("caller asked what 'other holistic modalities' means... output OTHER_HOLISTIC_EXPAND template verbatim... treat the caller's next response as a new category selection"). Never calls `confirm_service`, never sets `working_type`/`working_id`. Structurally closer to a routing rule than a branch. |
| `totally_well LYMPHATIC_DISAMBIGUATION` | Same shape as `HOLISTIC_EXPAND` — asks a clarifying question then routes to two OTHER named branches (`CLINICAL_LYMPHATIC`, `ADVANCED_LYMPHATIC`) rather than resolving itself. No `working_type`/`working_id`, no `confirm_service` call. |
| *(discussed, not formally recommended)* `intuitive_health_and_wellness CHIROPRACTIC` | Considered for `patches` — three elaborate special-case pre-gate branches (NET/Emotional, Family, Infant) each with their own resolution, stacked ahead of a standard gate+duration fallback. Technically renderable via GATE+DURATION's opaque `PRE_GATE_BYPASS` slot (it's just opaque text), but doing so would stretch the archetype's *intent* past usefulness — this is the single most idiosyncratic branch in the entire 80-branch corpus. Listed as `**P**` in the §2 table; a generator author could reasonably choose to model it as GATE+DURATION instead given the mechanism technically supports it — flagging the judgement call rather than pretending there's one obviously correct answer. |

---

## 7. `mri_first` — out of scope, not a fit for any of the four archetypes

`mri_first`'s equivalent section is headed `## DISAMBIGUATION BRANCHES`, not
`## CATEGORY BRANCHES` (confirmed: no `## CATEGORY BRANCHES` string appears anywhere in
`nodes/clinics/mri_first/node_2_service_resolution.txt`). Its 11 `### `-level entries
(`HIP_GROUP`, `HAND_GROUP`, `SHOULDER_GROUP`, `WRIST_GROUP`, `ANKLE_GROUP`, `ELBOW_GROUP`,
`SCAPULA_GROUP`, `TMJ_GROUP`, `HAMSTRING_GROUP`, `FOOT_GROUP`, `SPINE_GROUP`) are a
different *kind* of thing entirely: pure anatomical disambiguation for a radiology
clinic — "is that on the left or right side?" / "one side or both?" — with **zero**
patient-status concept anywhere (no `booking_for`, no `VARIANT_SELF`/`VARIANT_OTHER`, no
new/existing distinction at all), because MRI scan appointment types are keyed purely by
body region + laterality, not by whether the caller has been seen before. Each group is a
`MANDATORY TURN 1 (ask) → TURN 2 (route by 2-3 answer options) → confirm_service` shape —
structurally closest to a *degenerate GATE outcome* (one flat question, 2-3 answers, no
patient-status anywhere), but forcing all 11 through the GATE template would require
stripping out GATE's entire `booking_for`/`VARIANT_SELF`/`VARIANT_OTHER` mechanism, which
is present in literally every other GATE-archetype branch in the fleet and is core to
what makes GATE "GATE" rather than a generic single-question-flat-answer template.
Recommendation: **do not fold mri_first's DISAMBIGUATION BRANCHES into this template
system.** If mri_first (or a future similarly-shaped radiology/imaging clinic) needs
templating, it warrants its own small `_disambiguation.txt` archetype built specifically
around "ask a body-part/side/count question, resolve to 1-of-N flat IDs, no patient
status ever" — a genuinely different family, not a config of any of the four templates
here. Out of scope for this task; noted so it isn't silently dropped from consideration
later.

---

## 8. Live bugs spotted (not fixed, per the task brief)

1. **`intuitive_health_and_wellness/node_2_service_resolution.txt` line 228–233 — missing
   `---` separator between `HOLISTIC_EXPAND` and `CHINESE_MEDICINE`.** Every other branch
   boundary in the CATEGORY BRANCHES section (in this file and every other Family A file)
   is `<content>\n\n---\n\n### NEXT`. Here, `### HOLISTIC_EXPAND`'s 3-line body is followed
   directly by `### CHINESE_MEDICINE` with no separator at all — confirmed by grep
   (`^### \|^## \|^---$` line listing: line 228 `### HOLISTIC_EXPAND`, line 233
   `### CHINESE_MEDICINE`, no `---` between them, while every other adjacent pair in the
   same file does have one). This is a genuine, live formatting defect — harmless at
   runtime (the model reads `### ` headers, not `---` separators, to tell branches apart)
   but worth a one-line fix (add `\n---\n` before line 233) whenever someone is next in
   that file for an unrelated reason.
2. **`ryde_health/node_2_service_resolution.txt` lines 379 and 415 — malformed branch
   headers**, already known per the task brief (`### OSTEOPATHYDr Deepak Yagnik has
   dedicated appointment type IDs.` and `### MASSAGENo new/returning variant.` — the
   clinic's own descriptive note welded onto the branch name with no separating
   newline). Not re-flagging as new; noted in §6 only so the generator's config for these
   two branches uses the real (malformed) names rather than silently "fixing" them.
3. **GATE-archetype outcome numbering skips "2" in the plurality of branches** (§4.2) —
   very likely the same class of copy-propagated numbering defect already documented in
   `.claude/rules/node2-template-builder-plan.md` §6.1 for the `## RULES` section, showing
   up independently in `## CATEGORY BRANCHES` too. Not fixed (kept as the template
   default per "most common wording"); flagged for a deliberate decision.

---

## 9. MIGRATION LANDED — actual state as of 2026-08-16

Sections 1–8 above are the *design study*, written before any branch was wired into
`scripts/node2_configs.py`. This section records what the generator actually does today.
Where the two disagree, this section wins.

### What shipped

**40 of 84 branches now render from an archetype template.** Every migrated branch was
verified by byte-exact round-trip — extract slots from the branch's own text, re-render
through the template, require character-for-character equality with the original — so the
migration provably changed **zero characters** of any clinic's prompt. Proved twice over:
per-branch at extraction time, and fleet-wide afterwards by generating every clinic's
full body from the pre-migration and post-migration configs and diffing (0 clinics
differed).

| Archetype | Branches |
|---|---|
| GATE+DURATION | 16 |
| DIRECT | 9 |
| SUBTYPE+GATE | 9 |
| GATE | 4 |
| DIRECT+WORKING | 2 |
| **RAW (bootstrap, unmigrated)** | **44** |

`DIRECT+WORKING` was added in a follow-up pass: the same "no gate, one appointment type"
shape as `DIRECT`, but resolved via `working_type =`/`working_id =` variables and a bare
`Call universal_router intent="confirm_service".` instead of an inline JSON payload. Only
2 of the 10 branches originally filed under "no gate; resolution shape off-template" fit
it (`cascade_womens_health TELEHEALTH`, `totally_well CRANIOSACRAL`) — the rest
(`raymond_terrace`'s location-keyed branches, `ryde_health`'s duration-lookup and
group/private-nested branches, `totally_well PACKAGES`' 3-way sub-type,
`intuitive_health_and_wellness EFT_MATRIX`'s redirect-then-route flow) have genuinely
different multi-outcome shapes a single new archetype can't honestly cover — confirmed by
the same round-trip requirement rejecting all of them, not by inspection alone.

The remaining 44 across 14 clinics are itemised by reason below — none is an unexplained
leftover.

### Templates were generalised, not the prompts

§5's 46/76 byte-exact figure was measured against a throwaway extractor with its own
templates. Against the committed templates the true starting figure was 22/84. Closing
the gap meant adding slots for variance the templates had baked in as fixed text — the
fidelity-first direction, i.e. the template bends to the corpus, never the corpus to the
template:

- `_gate.txt`, `_gate_duration.txt`: `. Halt.` → `<<GATE_HALT_TAIL>>` (clinics append
  reinforcement like `ZERO TOOL CALLS THIS TURN. HALT. Do not enter step 2 or 3 until…`,
  which is behavioural text, not decoration); the fixed CONCERN-GUIDED line →
  `<<GATE_CONCERN_LINE>>` (parenthetical variants); new `<<POST_OUTCOMES_BLOCK>>` for
  branches carrying a sub-step after outcome B (e.g. totally_well's package path).
- `_direct.txt`: the fixed `Call universal_router: …` prefix → `<<CALL_LEAD>>` ending
  before `universal_router:` (absorbs both `Call ` and `Speak one filler phrase…, then
  call `, and the Call/call case difference), plus `<<CALL_TAIL>>` for `. HALT.` vs
  `. Per CONFIRM_SERVICE FILLER RULE. HALT.`, and `<<INTRO_BLOCK>>` covering the gap after
  the heading (some branches have no blank line there).

The gate line's `If {{booking_for}} == "other": ask VARIANT_OTHER ("…"). Otherwise: ask
VARIANT_SELF ("…")` skeleton, the `working_type`/`working_id` outcome shape, and the
`confirm_service` payload skeleton all stay template-owned — those are the invariants a
fleet-wide contract change would otherwise have to touch in 84 places.

### Matching is round-trip-verified, and archetype fit is separately enforced

Two templates are permissive enough to match branches they don't describe: SUBTYPE+GATE is
four blobs separated by blank lines, and DIRECT's blobs will bury a whole gate question
plus one of its two outcomes. Both round-trip byte-exact while filing the branch under the
wrong archetype — RAW with a misleading label, which is worse than RAW. So acceptance also
requires: SUBTYPE+GATE must contain the `#### ` detection/paths structure; DIRECT must have
no VARIANT_SELF/VARIANT_OTHER and exactly one `confirm_service` call. `PRICING_FOOTER` is
constrained to `(?:Pricing.*)?` — all 50 real footers open with "Pricing", and without the
constraint the trailing blob absorbed the tail of the last outcome block in 20 branches.

### Follow-up pass: 10 more branches word-normalized onto Style A (2026-08-16, same day)

The 24-branch "gate present but not Style A" bucket was the one deliberately left as a
content decision, not a mechanical task (see "Open decision" above). Given explicit
go-ahead, 10 of those 24 were migrated by hand — reworded onto the canonical
`If {{booking_for}} == "other": ask VARIANT_OTHER (...). Otherwise: ask VARIANT_SELF
(...).` wrapper, with every other word (the question text, any reinforcement/HALT-tail
sentence, the outcome labels, `working_type`/`working_id`, and the `confirm_service` call)
copied verbatim from the branch's own current text:

- `balrothery_physio` PHYSIOTHERAPY, `healing_hands_hand_therapy` NDIS_HAND + HAND_THERAPY,
  `village_remedies` ACUPUNCTURE, `yandina_podiatry` FOOT_PAIN + HEEL_PAIN + SKIN_TOENAIL —
  the numbered-`Gate (mandatory...)`/`(SELF)`/`(OTHER)` wrapper folded onto Style A.
- `totally_well` PREGNANCY — same wrapper fold; the underlying two-way question is a
  sub-type choice ("Pregnancy Massage or Pregnancy Lymphatic Drainage"), not a
  new/existing-patient gate — GATE's skeleton is content-agnostic (it's just "ask a
  self/other-variant two-way question, route to one of two IDs"), so this is a legitimate
  fit, not a misclassification.
- `plantar_fascia_clinic` PODIATRY, `taylor_square_osteo_chiro` GENERAL_BOOKING — these
  two were curly-quote bugs, not wording drift (`"other"`/`"First Appointment"` etc. typed
  with smart quotes throughout the branch, matching the already-known 8-clinic curly-quote
  defect class). Straightened first, which alone brought `taylor_square_osteo_chiro`'s
  gate wrapper to a byte-exact match; `plantar_fascia_clinic`'s question text was inlined
  from the same clinic's own `slots['VARIANT_SELF']`/`['VARIANT_OTHER']` values (used
  elsewhere in the same file's `## TEMPLATES` section) — not invented text, the exact
  words the file already commits to about itself.

**Deliberately excluded from this batch, and why:**
- `totally_well` RELAXATION_MASSAGE — its two duration outcomes share ONE trailing call
  line under a single "3. Duration resolved:" heading, not two separately-numbered
  outcomes each with their own call line. Forcing it into GATE's two-outcome/two-call-line
  shape would restructure the instruction, not just reword the wrapper.
- `cascade_womens_health` HYDROTHERAPY, `intuitive_health_and_wellness` MASSAGE/BREATHWORK/
  REIKI, `meraki_holistic_health` LYMPHATIC_DRAINAGE, `ryde_health`'s three branches, and
  `speeding_health`'s three branches — each has real per-outcome structure GATE can't
  express without inventing content (condition-list lines before an outcome, nested
  sub-disambiguation, inline-payload-only outcomes with no `working_type`/`working_id`
  pair, pre-gate keyword-bypass jump targets to differently-labelled outcomes). Forcing
  these through would have meant writing new instruction text, not normalizing existing
  wording — out of scope for a drift-alignment pass.

**Verification (not byte-exact by design — this pass intentionally changes wording):**
every one of the 10 was hand-reviewed side by side (before/after printed in full, not just
diffed) before being written. After writing: `generated_body()` compared per-clinic against
this session's own pre-pass snapshot confirmed **exactly the 7 touched clinics changed and
no others**; the loss gate's 12 `LOST` lines are precisely the old `(SELF)/(OTHER)`-style
wrapper sentences these 10 branches used to contain (nothing else); the quote-glyph gate
stayed at **0 straight→curly** (38 curly→straight, up from 21, both curly-quote branches'
full text now clean). Fleet dry-run: 28/29, zero WARN/ERROR/unresolved tokens.

Archetype tally after this pass: GATE 14 (was 4), GATE+DURATION 16, SUBTYPE+GATE 9,
DIRECT 9, DIRECT+WORKING 2, **RAW 34** (was 44) — 50 of 84 branches now template-driven.

### The 34 still on RAW, by reason

| # | Reason | Where |
|---|---|---|
| 14 | **Gate present but not Style A, and not migrated this pass.** Each has real per-outcome structure GATE can't express without inventing content (condition-list lines before an outcome, nested sub-disambiguation, inline-payload-only outcomes with no `working_type`/`working_id` pair, pre-gate keyword-bypass jump targets to differently-labelled outcomes, or a shared trailing call line across outcomes instead of one each). Forcing these through would mean writing new instruction text, not normalizing existing wording. | cascade, ihw ×3, meraki, ryde ×3, speeding ×3, totally_well |
| 8 | **No gate; resolution shape off-template.** Each is a genuinely distinct multi-outcome shape (location-keyed, duration-lookup, nested group/private, 3-way sub-type, redirect-then-route) — not further consolidatable without a bespoke archetype per shape. | ihw, raymond ×4, ryde ×2, totally_well |
| 5 | **Style A gate, outcome blocks off-template.** Gate matches; the outcomes have a shape the GATE/GATE+DURATION bodies don't model. | ihw ×2, totally_well ×3 |
| 4 | **§6: recommended for `patches`.** Unchanged from the design study. | ihw HOLISTIC_EXPAND + CHIROPRACTIC, totally_well LYMPHATIC_DISAMBIGUATION, ryde OSTEOPATHY |
| 3 | **Whole-flow blocks, not category branches** (the Family D fold). Correctly RAW permanently. | luminance_health, sports_therapy_by_andy, sydney_spine |

### Two generator defects found and fixed while migrating

1. **CRLF doubling.** 60 of 84 branch texts carry literal `\r\n` from however they were
   extracted into `node2_configs.py`. The writer opens in text mode, so writing them back
   would have produced `\r\r\n` throughout the CATEGORY BRANCHES section of 15 clinics on
   the very first real (non-dry-run) write. Both existing gates whitespace-normalise every
   line, so neither could see it. Fixed by `_normalise_newlines()` in
   `scripts/generate_node2.py`, applied in `compose_branches()` and once more over the
   assembled body.
2. **Curly quotes introduced into live prompts.** The Family A and E templates hardcoded
   the URGENCY QUALIFIER line with smart quotes — including `timeframe_raw=”today”`, a
   curly quote inside a value, which is the same defect class already reported against 8
   clinics' JSON payload examples. `canon()` folds curly onto straight, so the loss and
   added gates were both blind to it. Straightened in both templates; a third gate
   (`n2_quotes.py`) now reports every quote-glyph flip in either direction. Result:
   **0 straight→curly, 21 curly→straight** — the generator now only ever removes smart
   quotes, never adds them.

---

## 10. SECOND MIGRATION PASS — 2026-08-19/20

Supersedes §9's counts. **RAW 34 → 23; 62 of 85 branches now render from a template.**
(§9's denominator was 84; the fleet has since gained `body_logic_remedial_myotherapy`.)

Every migration in this pass was accepted only on **byte-exact round-trip through the real
generator path** (`generate_node2.compose_branches`), and the whole pass was gated fleet-wide:
a generated-body snapshot of all 29 in-scope clinics taken before the first edit is
**character-for-character identical** to the snapshot taken after the last one — `CHANGED
CLINICS: 0`, `TOTAL LOST = 0`, `TOTAL ADDED = 0`, `straight->curly 0`. `generate_node2.py
--diff` then reports `SAME - byte-identical` for all 29 clinics, and `--dry-run` exits 0 with
zero WARN/ERROR. **Zero characters of any clinic's prompt changed.**

### What moved (12 branches)

| Archetype | Branches |
|---|---|
| GATE | `intuitive_health_and_wellness` NATUROPATHY*, `totally_well` CLINICAL_LYMPHATIC / ADVANCED_LYMPHATIC / POST_SURGICAL |
| GATE+DURATION | `intuitive_health_and_wellness` CHINESE_MEDICINE* |
| DIRECT+WORKING | `cascade_womens_health` TELEHEALTH* |
| **QUESTION+ROUTE** (new) | `speeding_health` MASSAGE_RACHEL / SPORTS_MASSAGE_GLEN, `totally_well` RELAXATION_MASSAGE |
| **GATE+INLINE** (new) | `ryde_health` ACUPUNCTURE / CHIROPRACTIC / PHYSIOTHERAPY |

`*` = needed a per-branch `patches` entry (see below).

The `totally_well` trio had been filed under "Style A gate, outcome blocks off-template". That
was true when written but is not any more: the `PRE_GATE_BYPASS` and `POST_OUTCOMES_BLOCK`
slots added during §9's own generalisation pass are exactly the shape those branches need
(a package-signal bypass ahead of the gate, and a package sub-step after the outcomes). They
now render through the **unmodified** `_gate.txt` with no patches at all.

### Two new archetypes, and the bar they had to clear

A template whose slots are two arbitrary free-text blobs is *RAW with extra steps* — it owns no
invariant, so a fleet-wide wording change still means editing N configs by hand. Both new
templates were required to own something that actually changes fleet-wide:

- **`_question_route.txt` (QUESTION+ROUTE)** — no new/existing gate at all: one disambiguating
  question (duration / gender / delivery mode), then an inline `key -> working_type,
  working_id` map whose entries **share one trailing call line**. Neither `_gate.txt` nor
  `_gate_duration.txt` can render this: both hardcode the `{{booking_for}}` gate sentence, and
  both give every outcome its own call line. The slot that earns the template is `CALL_LINE` —
  that sentence is the single most change-prone line in the corpus (it already changed once
  fleet-wide, in the `CONFIRM_SERVICE SILENT` -> `FILLER` migration), so it is owned explicitly
  rather than buried inside a blob. This is precisely the "shared trailing call line" shape
  §9 excluded from the GATE reword pass — correctly, since forcing it into GATE would have
  restructured the instruction; a purpose-built archetype does not.
- **`_gate_inline.txt` (GATE+INLINE)** — the gate expressed as a `TURN 1 — MANDATORY` spoken
  instruction gated on `{{patient_status}}`, with each outcome calling `confirm_service`
  through an **inline payload** instead of `working_type`/`working_id` vars. Distinct from
  GATE on both counts. It owns a lot: the entire TURN-1 scaffold (including the explicit
  `Do NOT call universal_router or backup_universal_router on this turn` line) and the full
  payload skeleton with its `[+ CONTEXT PIGGYBACK: ...]` clause. The template was derived
  *from* a real branch by tokenising it, so every fixed character is byte-faithful by
  construction rather than by retyping.

Both were held to a **>=3 member** bar, decided from a mechanical signature census of all 35
RAW branches rather than from reading prose. The census is the reason no third archetype was
added: outside these two clusters the distribution is a long tail of **20 signatures with
exactly one member** — differing in question style, outcome-head style (`2.` vs `2a.`),
`working_type` indent (3 / 4 / 5 / 7 spaces), per-outcome vs shared call lines, and nesting
depth. A template spanning those would own nothing.

### `patches` used instead of reshaping a shared template

Three mechanical wrapper deviations were absorbed per-branch, because reshaping either gate
template would have forced all 30 already-migrated GATE/GATE+DURATION branches to change with
it — a large blast radius for a cosmetic difference, and one this doc's own concurrency
warnings argue against taking on:

- **NOPAREN** (`NATUROPATHY`, `CHINESE_MEDICINE`) — the gate line carries no `("question")`
  parenthetical; those clinics keep the question text only in their own `## TEMPLATES` section.
- **NOBLANK** (`CHINESE_MEDICINE`) — no blank line between the `###` heading and step 1.
- **no-blank-before-working-vars** (`TELEHEALTH`) — the working-var block runs straight on from
  the CONCERN-GUIDED line.

### Archetype fit is enforced separately from round-trip — and it rejected a branch

`body_logic_remedial_myotherapy` MYOTHERAPY_REMEDIAL_MASSAGE round-trips byte-exact through
`_gate_duration.txt`, and was **still rejected**. Its real shape is gate -> 3-way patient status
(new / existing / existing-elsewhere, via a location follow-up) -> per-status duration question
-> 8 appointment types, across five top-level steps. GATE+DURATION's free-form
`POST_OUTCOMES_BLOCK` will silently swallow steps 4-5, leaving `OUTCOME_A`/`OUTCOME_B` bound to
what are really dispatch steps — a branch that renders perfectly while its slot names lie about
what they hold. Per §9's own rule, *RAW with a misleading label is worse than RAW*. A mechanical
guard now enforces this: any further top-level numbered step after the two outcomes is a hard
reject. It is the only branch the guard currently catches, and it stays RAW deliberately.

### The 23 still on RAW

| # | Where | Why |
|---|---|---|
| 6 | `intuitive_health_and_wellness` HOLISTIC_EXPAND, CHIROPRACTIC, MASSAGE, BREATHWORK, EFT_MATRIX, REIKI | HOLISTIC_EXPAND is a redirect stub and CHIROPRACTIC is a §6 `patches` candidate (both unchanged from the design study); EFT_MATRIX is a redirect-then-route flow with its own `wrap_up` branch; MASSAGE/BREATHWORK/REIKI each carry 3+ outcome blocks with a *nested* question and map inside each. |
| 3 | `raymond_terrace_and_tea_gardens_osteopaths` STANDARD, DVA_TYPE, EPC_TYPE | Location-keyed, with `working_business_id`/`working_business_name` pairs; EPC_TYPE nests a second sub-question inside one location outcome. DVA_TYPE alone would fit a question+per-outcome template — a single member, below the bar. |
| 3 | `ryde_health` OSTEOPATHY, MASSAGE, PILATES_CONDITIONING | OSTEOPATHY forks on an already-known `practitioner_preference` (§6 `patches` candidate); MASSAGE and PILATES have nested group/private and `####` sub-structure. |
| 3 | `totally_well` LYMPHATIC_DISAMBIGUATION, FASCIA, PACKAGES | §6 `patches` candidate, plus two `2a.`/`2b.`-style multi-outcome shapes. |
| 3 | `luminance_health`, `sports_therapy_by_andy`, `sydney_spine` | Whole-flow blocks, not category branches (the Family D fold). **Correctly RAW permanently.** |
| 5 | `body_logic` MYOTHERAPY_REMEDIAL_MASSAGE, `cascade` HYDROTHERAPY, `meraki` LYMPHATIC_DRAINAGE, `speeding` FREE_CONSULTATION, `yandina` SPORTS_INJURY | Singleton shapes (see the census above) — each would need its own bespoke archetype. |

None is an unexplained leftover, and the remaining tail is now genuinely structural rather than
merely unattempted: every one of the 23 was mechanically tested against all seven archetypes
and rejected with a specific, recorded reason.

### Gate tooling was rebuilt, and belongs in the repo

§9's gates (`n2_loss.py`, `n2_added.py`, `n2_quotes.py`, `n2_cmp_configs.py`) were throwaway
scratchpad scripts and no longer exist. They were rebuilt for this pass as a single
snapshot-and-compare pair: render every clinic's body without touching disk, then diff two
snapshots for changed clinics, lost lines, added lines, and quote-glyph flips in both
directions. Rebuilding a verification harness from scratch each time is how a gate quietly
stops being run — worth landing this one under `nodes/node2_templates/` or `scripts/` rather
than leaving the next pass to rediscover it a third time.
