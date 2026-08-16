# Node 2 Family A — Slot Reference, Drift Decisions, Verification

Generated as part of the 2026-08-14 migration session that drove `TOTAL LOST` from 389 to 0
across all 17 in-scope Family A clinics (`mri_first` excluded — see `EXCLUDED_CLINICS` in
`scripts/generate_node2.py`). Machinery: `scripts/generate_node2.py` (generator + `DEFAULT_SLOTS`),
`nodes/node2_templates/node_2_a_category.txt` (template), `scripts/node2_configs.py`
(auto-generated per-clinic config — do not hand-edit).

## How to read this document

- **Slot table**: every `<<SLOT>>` token in `node_2_a_category.txt`, its fleet default, and which
  of the 17 in-scope clinics override it. A slot with 0 overrides exists purely as a future
  escape valve (currently unused).
- **Normalised drift**: every case where a clinic's original wording was declared an accepted
  variant of the template's canonical wording (case b) rather than modelled as a slot (case a),
  with before/after text and why the meaning is identical.
- **Verification**: the final acceptance-gate run and diff sizes.
- **Open items**: patches used instead of slots (and why), things left unresolved, and live bugs
  spotted in clinic files during this work (reported, not fixed, per instructions).

---

## 1. Slot table

### MINI-FRAMEWORK

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `BLOCKING_EXAMPLE_SERVICE` | Service name used in the PRE-ROUTING SILENCE bad-example sentence | `appointment` | 9 clinics (per-clinic service name) |
| `VARIANT_TURN_SEQUENCING` | Optional extra MINI-FRAMEWORK rule line | `''` | 7 clinics |
| `TONE_BLOCK` | Optional `- TONE:` line | `''` | 10 clinics |
| `LOCATION_RULE` | Text after `- LOCATION RULE:` | single-location boilerplate | 3 clinics (multi-location / Node-3-handles-it wording) |
| `TURN_TYPE_RULE_LINE` | Whole `- TURN TYPE RULE:` line | generic case-(c) wording | 4 clinics — **see §2, this was a real regression catch, not cosmetic** |
| `MINI_FRAMEWORK_EXTRA` | Any additional MINI-FRAMEWORK lines not otherwise owned | `''` | 9 clinics |

### PAST PRACTITIONER LOOKUP GUARD

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `GATE_QUESTION_NAMES` | Named gate questions in the EXCLUSION bullet | `VARIANT_SELF, VARIANT_OTHER, duration question, sub-type question` | 16 clinics |
| `PAST_PRAC_SERVICE_UNKNOWN` | PHASE B fallback sentence when only practitioner resolved | generic "ask which service" line | 2 clinics |

### CONTEXT PIGGYBACK

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `CONTEXT_PIGGYBACK_INTRO` | First header sentence | colon-ending boilerplate | 7 clinics |
| `CONTEXT_PIGGYBACK_SCOPING` | Second header sentence (payload nesting rule) | boilerplate | 1 clinic (palm_beach — full rewrite as "CONFIRM_SERVICE PAYLOAD SCOPING:") |
| `FAMILY_MEMBER_NAME_LINE` | The `- family_member_name:` bullet | 1-example boilerplate | 6 clinics (drop/add examples, reworded capture rule) |
| `PIGGYBACK_PRACTITIONER_PREF_LINE` | The `- practitioner_preference:` bullet | plain "any practitioner name mentioned" | 1 clinic (palm_beach — PATTERN A/B/C validation-required version) |
| `PATIENT_STATUS_LINE` | The `- patient_status:` bullet | 7-synonym boilerplate | 3 clinics (extra synonyms: "initial appointment", "as a new patient") |
| `EXTRA_PIGGYBACK_FIELDS` | Any additional piggyback bullets/notes (broadened to non-dash lines this session, e.g. inline gender-question guidance) | `''` | all 17 (every clinic has ≥1 extra field) |
| `BOOKING_FOR_PRIORITY_RULE` | Optional `BOOKING_FOR PRIORITY RULE` line | `''` | 7 clinics |
| `PIGGYBACK_TRAILING_EXTRA` | Any note between `BOOKING_FOR_PRIORITY_RULE` and `TIMEFRAME_RAW SURVIVAL RULE` | `''` | 4 clinics (e.g. totally_well's `PAYLOAD NESTING:` note) |

### RULES / CONFIRM_SERVICE CALL FORMAT

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `RULE_PRICING` | Rule 2 text | generic pricing rule | 7 clinics |
| `RULE_NO_UNPROMPTED_MENU` | Rule 9 text | generic menu rule | 1 clinic |
| `RULES_EXTRA` | Additional numbered rules (auto-renumbered from 12) | `''` | 4 clinics |
| `CONFIRM_SERVICE_OMIT_RULE` | Omit/always-include line | boilerplate | 7 clinics |
| `CONFIRM_SERVICE_EXTRA` | Additional CONFIRM_SERVICE CALL FORMAT lines | `''` | 7 clinics |

### INFO PIVOT RETURN GUARD

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `INFO_PIVOT_AMBIGUITY_CHECK` | Optional pre-FIRST ambiguity check block | `''` | 1 clinic |
| `INFO_PIVOT_FIRST_LINE` | The `- FIRST: IF {{implied_service}}...` line | generic CATEGORY-TABLE-match wording | 5 clinics (name own branches/matching style) |
| `INFO_PIVOT_VARIANT_LINE` | One or more lines between FIRST and the (still-hardcoded, NORMALISED-covered) `- If {{patient_status}} is already set...` boilerplate | generic variant-question wording | 6 clinics |
| `INFO_PIVOT_NEITHER_FALLBACK` | The `- IF neither ->` line | `output MENU_LIST verbatim. HALT.` | 4 clinics (`ask VARIANT_SELF. HALT.` for near-single-category clinics) |
| `RETURNING_QUESTION_BRANCHES` | Branch list named in Scan J's returning-patient clause | `no branches at this clinic have one` | 5 clinics |

### TEMPLATES

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `MENU_LIST_BLOCK`, `NOT_OFFERED_FIRST/SECOND`, `VARIANT_SELF/OTHER`, `GUIDANCE_QUESTION`, `TEMPLATES_EXTRA` | Pre-existing slots, unchanged this session | various | most/all clinics |
| `PRAC_VARIANT_SELF` / `PRAC_VARIANT_OTHER` | Practitioner-specific gate question | `Have you/they seen [first_name] before?` | 4 clinics (alpine→Milan, cascade→Melanie, kim_gatenby→Kim, the_rehab→Alex) — **new this session, see §2** |

### VARIANT-FIRST RULE

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `VARIANT_FIRST_PREAMBLE` | Optional content before `SCOPE:` | `''` | 1 clinic (totally_well — PERMITTED EXCEPTIONS block) |
| `VARIANT_FIRST_SCOPE` | Text after `SCOPE:` | boilerplate | 16 clinics |
| `VARIANT_FIRST_MANDATORY_LINE` | The "For any branch that begins with..." line | generic wording | 9 clinics (name specific branches, add a Scan-J-pre-set exception clause) |
| `VARIANT_FIRST_BRANCHES` | Pre-existing slot, unchanged | branch list | 12 clinics |
| `VARIANT_FIRST_EXTRA` | Escape valve between BRANCHES and TURN 1 | `''` | 0 (unused — totally_well's exceptions block landed in `VARIANT_FIRST_PREAMBLE` instead, see §4) |
| `VARIANT_FIRST_TURN1_LINE` | TURN 1 line | boilerplate | 1 clinic (palm_beach) |
| `VARIANT_FIRST_TURN2_LINE` | TURN 2 line | boilerplate | 5 clinics (4 of these are the declared-normalised short form, see §2 — the 5th, palm_beach, is a genuine rewrite) |
| `VARIANT_FIRST_POST_TURN2` | Optional paragraph between TURN 2 and the trailing line | `''` | 1 clinic (alpine — CRITICAL COMBINED ANSWER GATE) |
| `VARIANT_FIRST_TRAILING_LINE` | Closing "ABSENCE of patient history" line | boilerplate | 1 clinic (palm_beach) |

### CONCERN-GUIDED RESOLUTION RULE

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `CONCERN_EXAMPLES` | Pre-existing slot, unchanged | symptom examples | 7 clinics |
| `CONCERN_GUIDED_BODY` | Whole "Two cases: ..." body (case 1/2 text, PART1/2 wording, any 3rd case, trailing exception notes) | 2-case boilerplate | **all 17** (every clinic customizes case-1 empathy-line wording, the gate-question reference, or has a 3rd/different case — see §2) |

### CATEGORY RESOLUTION / CATEGORY TABLE / SYMPTOM RESOLUTION

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `CATEGORY_RESOLUTION_INTRO` | Line under `## CATEGORY RESOLUTION` before URGENCY STRIP | `On entry, evaluate...` | 1 clinic (totally_well — STEP A/B + ABSOLUTE RULE) |
| `CROSS_CATEGORY_DISAMBIGUATION`, `CATEGORY_TABLE_INTRO/HEADING/TABLE/TAIL`, `SYMPTOM_RESOLUTION_BODY`, `KB_SECTIONS` | Pre-existing slots, unchanged | various | most/all clinics (per-clinic data, expected) |

### CATEGORY BRANCHES / optional whole sections

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `CATEGORY_BRANCHES` | Composed branch list (RAW bootstrap) | — | all (per-clinic, by design) |
| `OVERLAP_RULE_SECTION`, `PRACTITIONER_ONLY_PATH_SECTION`, `BOOKING_PARTY_CORRECTION_SECTION` | Pre-existing optional sections, unchanged | absent/present | various |
| `EXTRA_SECTIONS_BEFORE_CATEGORY_RESOLUTION` | New escape valve before `## CATEGORY RESOLUTION` | `''` | 1 clinic (acacia — AMBIGUOUS TURN 2 REPLY + CONFIRM_SERVICE EXECUTION REMINDER, 2 whole new sections) |
| `EXTRA_SECTIONS_AFTER_UNIVERSAL_ESCAPES` | New escape valve before `## RESCHEDULE RE-ENTRY GUARD` | `''` | 1 clinic (plantar_fascia — ENTRY CHECKLIST) |
| `EXTRA_SECTIONS_BEFORE_TOOL_CALL` | New escape valve before `## TOOL CALL` | `''` | 1 clinic (plantar_fascia — CONTEXT PIGGYBACK CHECKPOINT + TIMEFRAME_RAW CHECKPOINT) |

### SCAN ON ENTRY

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `SCAN_C_BLOCK` | The `C. ...` line + `SCAN C SCOPE:` line (or a clinic's own preamble+C content, e.g. totally_well's PRE-STEP/EXECUTION ORDER) | duration-question boilerplate | 17 clinics (see §2 — the "kind" of question varies: duration/APPT_TYPE/billing-variant/clarifying-selection) |
| `SCAN_E_BLOCK` | The `E. ...` line + optional `SCAN E EXCEPTION:` line | long single-paragraph boilerplate | 16 clinics — **the majority fleet form is actually the SHORT 2-line form, not this default; see §2** |
| `SCAN_EXTRA`, `SCAN_J_SECTION`, `SCAN_K_SECTION` | Pre-existing slots, unchanged | various | various |

### HARD RULE / STEP 1 / TOOL CALL

| Slot | Description | Fleet default | Overridden by |
|---|---|---|---|
| `HARD_RULE_BODY` | Pre-existing slot, unchanged | boilerplate | 16 clinics |
| `STEP1_EXTRA` | Pre-existing slot, unchanged | `''` | 8 clinics |
| `STEP1_YESOK_LINE` | The `IF caller said "yes"/"ok"/"sure"...` line | `-> match implied_service to category ->` wording | 3 clinics (`-> match to branch ->` wording) |
| `STEP1_IMPLIED_SERVICE_LINE` | Nested `IF {{implied_service}} is set ->` line | same wording family | 3 clinics |
| `STEP1_NO_IMPLIED_SERVICE_FALLBACK` | Nested `IF no implied_service ->` line (may be multi-line) | `OUTPUT MENU_LIST template verbatim. HALT.` | 13 clinics |
| `MENU_LIST_MANDATORY_TRIGGER` | Pre-existing slot, unchanged | boilerplate | 7 clinics |
| `TOOL_CALL_PRACTITIONER_PREF_LINE` | The `- Must include practitioner_preference...` line | plain boilerplate | 2 clinics (intuitive — CANONICAL ANCHOR rule; palm_beach — RLT exception) |
| `TOOL_CALL_EXTRA` | Broadened this session to catch non-dash lines (e.g. plantar_fascia's `**BEFORE EVERY CONFIRM_SERVICE CALL...**` block) | `''` | 3 clinics |

---

## 2. Normalised drift (case b — declared intentional, no slot)

Every entry below: an original clinic line whose *meaning* is identical to the template's
canonical wording, differing only in punctuation, dash glyph, header nesting level, or numbering
— accepted as-is rather than modelled as a slot.

| Pattern name | Before (clinic) | After (template) | Why identical | Clinics |
|---|---|---|---|---|
| `rules-renumber` | any `N. ...` numbered RULES line | re-numbered canonical rule | pure numbering drift; content itself is separately captured via `RULES_EXTRA` when genuinely new — **caveat**: this pre-existing (not introduced this session) pattern is broad enough that it also silently accepts one stale, contradictory rule in `taylor_square_osteo_chiro` (rule 5, "zero spoken output... before or after", pre-dating the 2026-08-12/13 CONFIRM_SERVICE FILLER RULE fix). Confirmed via fleet-wide grep this is the only clinic carrying that exact stale phrase — not spot-checked further. See §4. | most |
| `info-pivot-body` | `- If {{patient_status}} is already set...` / `- THEN: IF {{appointment_type_id}}...` in any wording | canonical wording | same routing logic, wording-only drift (parens vs colon, minor rephrasing); pre-existing pattern, unchanged this session | most |
| `pre-routing-silence` | `- PRE-ROUTING SILENCE: ...` any wording | canonical | same rule, wording drift | 10 |
| `blocking-example` | `BLOCKING EXAMPLE ...` any wording | canonical | same rule, wording drift | 9 |
| `confirm-filler-rule` | `- CONFIRM_SERVICE FILLER RULE: ...` any wording | canonical | same rule | 8 |
| `allowed-parameters` | `ALLOWED PARAMETERS for confirm_service: ...` any wording | canonical | same rule | 8 |
| `confirm-payload` | `intent="confirm_service", called_number...` payload skeleton | canonical | same JSON skeleton | 6 |
| `scan-c-resolved` | `IF SCAN C resolved a branch selection ->...` comma/period + optional trailing `HALT.` variants | canonical | same instruction, trailing-punctuation-only drift | 4 |
| `valid-intents-dash` | `- VALID INTENTS: ...protocol violation {–\|—\|--}` never call... | en-dash version | **same content, dash-glyph only.** `canon()` deliberately keeps em-dash/en-dash distinct (maps to `--`/`-` respectively) elsewhere in this file, so this needed an explicit accept rather than relying on that global mapping — added narrowly to this one line rather than changing `canon()`'s behaviour fleet-wide. | 3 (palm_beach uses ASCII `--`, balrothery/village_remedies use em-dash `—`; template uses en-dash `–`) |
| `time-only-guard` | `TIME-ONLY GUARD ...` any wording, including a much longer "MANDATORY ZERO-TOOL-CALL RULE" variant (taylor_square) | canonical short form | same rule, taylor_square's version is a verbose restatement of the identical instruction | 3 |
| `confirm-nesting` | `When calling universal_router with intent="confirm_service"...` any wording | canonical | same instruction | 2 |
| `urgency-qualifier` | `- URGENCY QUALIFIER: ...` any wording | canonical | same rule | 2 |
| `category-table-hdr` | `## CATEGORY TABLE` (level-2 header) | `### CATEGORY TABLE` (level-3, nested under CATEGORY RESOLUTION) | heading *level* only — actual intro/rows/tail content already captured via the `CATEGORY_TABLE*` slots regardless of nesting; markdown heading depth has no runtime effect on the LLM | 1 (balrothery) |
| `past-prac-phaseB` | `PHASE B ...` any wording | canonical | same rule | 1 |
| `menu-mandatory` | `MENU_LIST MANDATORY TRIGGER:` / `SINGLE SERVICE GATE:` | canonical | same rule, label variant | 1 |
| `prac-pattern` | `PATTERN A/B/C match...` sub-lines | — | continuation lines of a practitioner-validation block already captured elsewhere | 1 |
| `blocking-example`, `separator`, etc. | — | — | pre-existing boilerplate patterns, unchanged this session | — |

**Removed this session:** `turn-type-rule` (was `^- TURN TYPE RULE:`, unconditionally accepting
any wording). This was actively masking a real regression — see §4 — and was replaced with the
`TURN_TYPE_RULE_LINE` slot instead.

---

## 3. Verification

### Final acceptance-gate run (`n2_loss.py`, all 17 in-scope clinics)

```
clinic                                        orig  lost  norm  status
--------------------------------------------------------------------------------
acacia_healing                                 558     0    10  OK
alpine_osteopaths                              238     0     9  OK
balrothery_physio                              228     0     8  OK
cascade_womens_health                          322     0     9  OK
healing_hands_hand_therapy                     246     0    10  OK
intuitive_health_and_wellness                  494     0     9  OK
kim_gatenby_acupuncture                        307     0     7  OK
meraki_holistic_health                         560     0     9  OK
palm_beach_osteopathy                          425     0    11  OK
plantar_fascia_clinic                          275     0     9  OK
raymond_terrace_and_tea_gardens_osteopaths     307     0    13  OK
speeding_health                                330     0     6  OK
taylor_square_osteo_chiro                      221     0     6  OK
the_rehab_podiatrist                           195     0     9  OK
totally_well                                   552     0    10  OK
village_remedies                               185     0     8  OK
yandina_podiatry                               320     0    13  OK

TOTAL LOST: 0
```

`taylor_square_osteo_chiro` (the template's base clinic) confirmed stable at 0 throughout —
regression-tested after every extraction re-run in this session.

### `--diff` line counts (informational — diff size, not a pass/fail signal)

| Clinic | + | – |
|---|---|---|
| acacia_healing | 381 | 382 |
| alpine_osteopaths | 56 | 60 |
| balrothery_physio | 90 | 48 |
| cascade_womens_health | 19 | 21 |
| healing_hands_hand_therapy | 152 | 126 |
| intuitive_health_and_wellness | 303 | 294 |
| kim_gatenby_acupuncture | 127 | 128 |
| meraki_holistic_health | 420 | 422 |
| palm_beach_osteopathy | 50 | 44 |
| plantar_fascia_clinic | 53 | 47 |
| raymond_terrace_and_tea_gardens_osteopaths | 139 | 131 |
| speeding_health | 31 | 24 |
| taylor_square_osteo_chiro | 36 | 35 |
| the_rehab_podiatrist | 109 | 58 |
| totally_well | 362 | 347 |
| village_remedies | 87 | 31 |
| yandina_podiatry | 243 | 214 |

### Addition review

Computed "pure-added" lines (added lines with no textually-matching removed line, i.e. lines
that are genuinely new rather than moved/reworded) for every clinic and read all of them.
Findings:

- The overwhelming majority are fleet-boilerplate lines that were **already hardcoded in the
  template before this session** (TOOL ROLES, RULES renumbering, `ALLOWED PARAMETERS`, `BLOCKING
  EXAMPLE`, `MENU_LIST MANDATORY TRIGGER`, standard TOOL CALL bullets, default
  `PRAC_VARIANT_SELF/OTHER`) landing on clinics that didn't previously have that exact boilerplate.
  This predates this session's slot work (confirmed against `taylor_square_osteo_chiro`'s own
  `--diff`, which shows the identical class of addition despite zero clinic-specific content
  changing) — not something introduced here. See §4 for the two clinics where this is most visible.
- One genuine regression was caught and fixed this session: `TURN_TYPE_RULE_LINE` — see §4.
- No other addition found reads as contradicting a clinic's own logic.

---

## 4. Open items

### Patches used instead of slots, and why

All of these are genuinely single- or two-clinic content that didn't warrant a fleet-wide slot:

| Clinic(s) | What | Why patches, not a slot |
|---|---|---|
| `palm_beach_osteopathy`, `totally_well` | Their own multi-line `D. If caller names a practitioner...` scan step | Only 2 clinics diverge from the fleet-default D. line (10/17 clinics already match it verbatim); a slot would add substitution machinery for 15 clinics that never use it |
| `palm_beach_osteopathy`, `totally_well`, `plantar_fascia_clinic`, `village_remedies` | Their own `## RESCHEDULE RE-ENTRY GUARD` body (4 different replacement texts) | Each of these 4 differs in a genuinely distinct way (payload-direct vs. cross-reference vs. Scan-J-ordering note); no shared "shape" to slot |
| `kim_gatenby_acupuncture` | STEP 1's `IF caller's message matches a category...` line, extended with its own branch-name examples | Single clinic |
| `raymond_terrace_and_tea_gardens_osteopaths` | Whole `## VARIANT-FIRST RULE` section replaced with `## STANDARD BRANCH — MANDATORY QUESTION ORDER` | This clinic doesn't have a VARIANT-FIRST RULE at all in the fleet sense (its "gate" is a two-turn LOCATION-then-NEW/RETURNING sequence) — a structurally different concept, not a wording variant of the same rule. Whole-block patch is the honest representation. |
| `village_remedies` | `- TOOL ROLES:` line, `CONFIRM_SERVICE CALL FORMAT` intro line | Single clinic each |
| `yandina_podiatry` | `MENU_LIST OUTPUT HARD RULE:` line, referencing its own MENU_LIST's exact starting phrase | Single clinic |

### Unresolved / left as pre-existing (not introduced or fixed this session)

- **`the_rehab_podiatrist` has no `## SCAN ON ENTRY`, `## HARD RULE`, `## STEP 1`, or `## TOOL
  CALL` sections in its original file at all** — its whole booking flow is simple enough not to
  need them. The generator still emits the full fleet-boilerplate versions of all four (since
  those sections are unconditionally present in the template), meaning this clinic gains ~47
  lines of generic-but-harmless scaffolding it never had. This predates this session (these
  sections were already unconditionally hardcoded before any of today's slot work) — flagged
  here rather than fixed, since removing it would be a scope decision beyond "drive LOST to 0."
- **`village_remedies` gains empty `VARIANT_SELF: ""` / `VARIANT_OTHER: ""` template lines** —
  it has no generic self/other gate question (its ACUPUNCTURE branch inlines its own question
  text), so these render as empty-quoted labels. Cosmetic only, never referenced elsewhere in
  its file. Same pre-existing-slot situation as above, not introduced this session.
- **`rules-renumber` normalisation is broader than pure numbering drift** (see §2) — it
  papers over taylor_square's one stale, contradictory RULES-section line. Not audited
  fleet-wide for other instances of the same class; only spot-checked that this specific
  stale phrase doesn't appear in any other clinic.
- **`plantar_fascia_clinic`'s own `## ENTRY CHECKLIST` section** (preserved verbatim via the new
  `EXTRA_SECTIONS_AFTER_UNIVERSAL_ESCAPES` slot) contains hardcoded line-number cross-references
  ("line 24–30", "line 96", "line 234–251", "line 260+") into its own file. These were already
  fragile in the original file (any hand-edit would have gone stale) and remain exactly as
  fragile post-migration — not made worse, not fixed.

### Live bugs spotted (reported, not fixed, per instructions)

- **`balrothery_physio` / `healing_hands_hand_therapy`'s INFO PIVOT RETURN GUARD drops the
  booking_for=="other" branch.** Both clinics' `INFO_PIVOT_VARIANT_LINE` reads roughly "ask
  VARIANT_SELF. HALT." unconditionally, with no check for `{{booking_for}} == "other"` (unlike
  the template's own `- If that category requires a variant question...: ask the variant
  question (if {{booking_for}} == "other": ask VARIANT_OTHER; otherwise: ask VARIANT_SELF)`).
  A caller returning from an info-pivot detour on a third-party booking (e.g. "book my wife in
  for physio" → info question → return) would be asked "Have **you** had physiotherapy..."
  instead of "Have **they**...". Present in the clinics' own original files, unrelated to this
  migration — reproduced verbatim as required for fidelity, not corrected.
- **`balrothery_physio` / `healing_hands_hand_therapy`'s `## CONCERN-GUIDED RESOLUTION RULE`
  section says "Two cases:" but numbers them 1 and 3** (no case 2) — a copy-paste numbering
  error present in both clinics' original files, reproduced verbatim via the new
  `CONCERN_GUIDED_BODY` slot per the fidelity requirement.

---

## 5. Build sequence used this session

1. Read the generator, template, extractor, and loss-gate scripts; ran the loss gate to confirm
   the starting 389/181/208 split matched the brief exactly.
2. Dumped every clinic's full verbose lost-line list, then the raw `## SCAN ON ENTRY`, `##
   CONCERN-GUIDED RESOLUTION RULE`, `## STEP 1`, `## INFO PIVOT RETURN GUARD`, `## VARIANT-FIRST
   RULE`, and `## CONTEXT PIGGYBACK` sections across all 17 clinics to classify every distinct
   drift pattern as case (a) slot or case (b) normalisation before writing any code.
3. Added ~30 new slots to the template + `DEFAULT_SLOTS`, extended `n2_extract.py`'s extraction
   logic (including two real bugs found and fixed mid-session: a `'---'` separator-line being
   mistaken for content, and a "next line only" heuristic that undercounted multi-line variant
   blocks), added 7 narrow single/two-clinic `patches`, and added 6 new `NORMALISED` patterns to
   `n2_loss.py`.
4. Iterated extract → measure → fix, re-measuring the full 17-clinic set every round (not just
   the clinic being worked on), per the required loop — caught and fixed a `taylor_square`
   regression (0→1) mid-way through from a `'---'`-swallowing bug.
5. Ran `--diff` across all 17 clinics and computed "pure-added" lines per clinic to check for
   wrongful additions independent of the LOST=0 signal — found and fixed one real regression
   (`TURN_TYPE_RULE_LINE`, previously silently overwritten by an overly-broad pre-existing
   normalisation) that LOST=0 alone would never have surfaced.
