# Family B (`GATE_FIRST`) — `node_2_b_gate_first.txt` slot reference

Template file: `nodes/node2_templates/node_2_b_gate_first.txt`

Clinics in this family: `evolution_physiotherapy_and_performance`, `new_med_skin`.

## Base clinic

**Base: `new_med_skin`.** It is the larger, more feature-rich file (381 body lines vs. evolution's 296) and exercises more of Family B's structural surface: multi-variant categories (FACIAL_VOLUME, BIO_REMODELLING) alongside single-appointment categories, DISAMBIGUATION guards in the category table, an Overlap rule for compound multi-service requests, and a Scan E variant-already-set skip that evolution's file has no equivalent of. Building the template so `DEFAULT_SLOTS` mirrors new_med_skin's shape and evolution supplies a full override set is the more natural direction for a reusable template than the reverse (a minimal base with no modelled path for a future richer clinic to extend). evolution's one structural extra — the CLASS BOOKING SHORTCUT fast-path and its paired Scan A0b — has no counterpart in new_med_skin and is modelled as an optional slot instead (default empty).

The individual NORMALISED DRIFT picks below (§3) are chosen on clarity/completeness merits per item, independent of which clinic is "base" — the base designation determines the `DEFAULT_SLOTS` value for the ~45 per-clinic slots, not the wording of the ~8 boilerplate lines that are normalised rather than slotted.

## 1. Slot reference

**45 slots total** (19 short, inlined below; 26 long/multi-line, in §2). All 45 are used exactly once in the template; none are orphaned. 2 are optional (empty-string default): `CLASS_BOOKING_SHORTCUT`, `PRACTITIONER_ONLY_EXTRA_NOTE` — for these, note the DEFAULT column is still new_med_skin's *actual* value per the base-clinic rule above (empty for the first, the extra note text for the second); "optional" describes that the *feature itself* is optional across the family, not that empty-string is always the fleet default.

### Short slots

| Slot | Description | Default (`new_med_skin`) | `evolution` override |
|---|---|---|---|
| `TURN_TYPE_A_VARIANT_LABEL` | TURN TYPE RULE's Type-A example clause naming which question(s) require a variant step | `variant questions (FACIAL_VOLUME/SKIN_PEELS)` | `the PHYSIOTHERAPY variant question` |
| `STEP0_HEADER_SUFFIX` | STEP 0 header's parenthetical note about what precedes it (references CLASS BOOKING SHORTCUT when present) | *(empty)* | ` after CLASS BOOKING SHORTCUT` |
| `COMPLAINT_EXAMPLE_LIST` | STEP C's parenthetical example list of symptom/condition phrases | `skin concern", "acne", "dry skin", "pain` | `back pain", "knee injury", "shoulder pain", "sprained ankle` |
| `NEW_PATIENT_APPT_ID` | appointment_type_id used for the mandatory new-patient consultation | `1480843963127571628` | `1319390333250836914` |
| `NEW_PATIENT_APPT_NAME` | appointment_type name used for the mandatory new-patient consultation | `Consultation For New Patients` | `Initial physiotherapy consultation` |
| `HALT_EXAMPLE_CLAUSE` | HALT COMPLETELY line's parenthetical example of an alternate service/duration question to ignore | `service booking (PRF, skin` | `appointment type or duration question (standard, extended review` |
| `EXAMPLE_CALLER_SERVICE` | Worked EXAMPLE block: service the caller asks for in the sample opening line | `PRF` | `physio` |
| `NEW_PATIENT_CALL_LABEL` | Worked EXAMPLE block: short parenthetical description of the confirm_service call | `new patient` | `initial physiotherapy` |
| `EXAMPLE_HALT_DETAIL` | Worked EXAMPLE block: HALT line's list of things NOT asked about | `PRF type` | `duration` |
| `PAST_PRAC_EXCLUSION_GATE_LIST` | PAST PRACTITIONER LOOKUP GUARD exclusion bullet's list of branch-gate template names | `PET_VARIANT, PET_VARIANT_OTHER, duration question, sub-type question, programme question` | `PRAC_VARIANT_SELF, PRAC_VARIANT_OTHER, the PHYSIOTHERAPY variant question` |
| `CONFIRM_SERVICE_FIELD_LIST_TAIL` | CONFIRM_SERVICE PAYLOAD VARIABLES field list -- whether patient_status is included | *(empty)* | `, {{patient_status}}` |
| `VARIANT_SELF_PHRASE` | VARIANT_SELF template | `[category]` | `physiotherapy` |
| `VARIANT_OTHER_PHRASE` | VARIANT_OTHER template | `[category]` | `physiotherapy` |
| `PRAC_VARIANT_SELF_PHRASE` | PRAC_VARIANT_SELF template | `[first_name]` | `Benjamin` |
| `PRAC_VARIANT_OTHER_PHRASE` | PRAC_VARIANT_OTHER template | `[first_name]` | `Benjamin` |
| `QUICK_MATCH_STEP1_TEXT` | SERVICE MATCHING PRIORITY step 1 -- text after 'If the caller's term appears there,' | `that category immediately. This is MANDATORY—` | `EXERCISE CLASS or PHYSIOTHERAPY immediately per the match — this is MANDATORY, ` |
| `PRAC_MATCH_EXAMPLE_A` | PRACTITIONER-ONLY PATH PATTERN A's worked example (first-name phonetic match) | `Rachel" / "Rachael" → "Rachel Leoni` | `Ben" / "Benjamin" → "Benjamin Butler-Bonnice` |
| `PRAC_MATCH_EXAMPLE_C` | PRACTITIONER-ONLY PATH PATTERN C's worked example (partial/first-syllable match) | `Lee-oh" / "Leony" / "Leone" → "Leoni" → Rachel Leoni` | `Bonnice" / "Bonis" / "Butler" → "Butler-Bonnice" → Benjamin Butler-Bonnice` |
| `PRACTITIONER_ONLY_EXTRA_NOTE` | Optional trailing note in PRACTITIONER-ONLY PATH (new_med_skin only, empty by default) *(optional)* | `Ask the gate or category question before listing the practitioner's services.` | *(empty)* |

### Long / multi-line slots

| Slot | Description |
|---|---|
| `CLASS_BOOKING_SHORTCUT` | Optional fast-path section evaluated before STEP 0 for a class/group-session shortcut service. Empty when the clinic has no such shortcut. *(optional)* |
| `NEW_PATIENT_SCRIPT` | NEW PATIENT ACTION's verbatim spoken script (PART 1) -- names the initial service and the practitioner |
| `PAST_PRAC_PHASE_B` | PAST PRACTITIONER LOOKUP GUARD PHASE B -- full lookup-response handling paragraph (practitioner/location resolution shape differs by clinic) |
| `RULES_SPOKEN_OUTPUT_EXCEPTION` | RULES section's sentence describing which turns may combine spoken output with a tool call (CONCERN-GUIDED clause differs because each clinic's concern-guided path ends differently) |
| `CONCERN_GUIDED_RULE_BODY` | CONCERN-GUIDED RESOLUTION RULE's full body -- what happens once the rule fires (differs: evolution ends in a spoken variant question with no tool call; new_med_skin calls the tool same-turn) |
| `IMPLIED_SERVICE_RULE_BODY` | IMPLIED-SERVICE CONFIRMATION RULE's full body |
| `AFTER_ROUTER_CALL_NOTE` | Closing sentence describing what happens after universal_router is called |
| `SERVICE_ALIAS_QUICK_MATCH_ENTRIES` | SERVICE ALIAS QUICK-MATCH bullet list mapping caller phrases straight to a category (per-clinic service vocabulary) |
| `RESCHEDULE_REENTRY_ACTION` | RESCHEDULE RE-ENTRY GUARD's action once patient_status is already established (ask a variant question vs go straight to CATEGORY RESOLUTION) |
| `INFO_PIVOT_IMPLIED_SERVICE_LOGIC` | INFO PIVOT RETURN GUARD's handling once {{implied_service}} is set (evolution: single gated category shortcut; new_med_skin: matches CATEGORY TABLE, branches on whether that category still needs a variant question) |
| `MENU_LIST_PHRASE` | MENU_LIST template -- the spoken service-menu recap phrase |
| `NOT_OFFERED_FIRST_PHRASE` | NOT_OFFERED template, first use in the call |
| `NOT_OFFERED_SECOND_PHRASE` | NOT_OFFERED template, second+ use in the call |
| `CONCRETE_EXAMPLES_LIST` | CONCRETE EXAMPLES worked bullet list under SERVICE MATCHING PRIORITY |
| `CATEGORY_TABLE_ENTRIES` | CATEGORY TABLE's full entry list (one block per category, caller-phrase -> CATEGORY mapping) plus the closing 'BEFORE outputting NOT_OFFERED' MANDATORY CHECK line -- entirely per-clinic content |
| `VARIANT_FIRST_SCOPE_TEXT` | VARIANT-FIRST RULE's SCOPE line and main body sentence -- names which categories require the variant question before booking |
| `CATEGORY_BRANCHES_BODY` | CATEGORY BRANCHES section's every category's full branch definition (variant questions, working_type/working_id mappings, Overlap rule where present). Entirely per-clinic; this is the largest slot in the template. |
| `PRAC_MATCH_EXAMPLE_B` | PRACTITIONER-ONLY PATH PATTERN B's worked example (surname token extraction) |
| `PRACTITIONER_ONLY_GATE_LOGIC` | PRACTITIONER-ONLY PATH's gate logic before 'On response:' (evolution: single practitioner/single category, ask gate directly; new_med_skin: look up practitioner_services, gate only if multi-category) |
| `PRACTITIONER_ONLY_RESPONSE_BODY` | PRACTITIONER-ONLY PATH's Yes/No outcome lines after 'On response:' |
| `SCAN_ON_ENTRY_EARLY_ITEMS` | SCAN ON ENTRY's early lettered items before Scan J (evolution: A0b class-shortcut scan + C + D; new_med_skin: C + D + E variant-already-set skip) |
| `SCAN_J_NEW_OUTCOME` | Scan J's 'new' patient_status outcome -- maps to the new-patient appointment type |
| `STEP1_RESCHEDULE_GUARD_ACTION` | STEP 1's action when RESCHEDULE RE-ENTRY GUARD fired |
| `STEP1_SCAN_C_ACTION` | STEP 1's action when Scan C resolved a variant/branch selection |
| `STEP1_CATEGORY_MATCH_BLOCK` | STEP 1's handling once the caller's message matches a category in the CATEGORY TABLE, plus the 'yes/ok/sure' implied-service shortcut |
| `STEP1_IMPLIED_SERVICE_FALLBACK` | STEP 1's fallback handling when the caller's message matches nothing but {{implied_service}} is set |

## 2. Long slot values

### `CLASS_BOOKING_SHORTCUT`

Optional fast-path section evaluated before STEP 0 for a class/group-session shortcut service. Empty when the clinic has no such shortcut.

**Default (`new_med_skin`):**

*(empty)*

**`evolution_physiotherapy_and_performance` override:**

```

## CLASS BOOKING SHORTCUT (evaluate BEFORE STEP 0 -- no patient status gate for classes)
If the caller's current message this turn contains any of: "exercise class", "clinical exercise class", "clinical exercise", "group class", "class", "classes", "group session", "exercise group":
Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "1319393805438294453", "appointment_type": "Clinical exercise class"}. Add to payload if captured in conversation: booking_for, family_member_name, timeframe_raw, practitioner_preference. Per CONFIRM_SERVICE FILLER RULE. HALT.
```

### `NEW_PATIENT_SCRIPT`

NEW PATIENT ACTION's verbatim spoken script (PART 1) -- names the initial service and the practitioner

**Default (`new_med_skin`):**

```
As you're new, I'll need to set you up for a new patient consultation first -- Dr Leoni will guide the best course of action from there.
```

**`evolution_physiotherapy_and_performance` override:**

```
As you're new, I'll need to set you up with an initial physiotherapy consultation first -- Benjamin will assess you and go from there.
```

### `PAST_PRAC_PHASE_B`

PAST PRACTITIONER LOOKUP GUARD PHASE B -- full lookup-response handling paragraph (practitioner/location resolution shape differs by clinic)

**Default (`new_med_skin`):**

```
PHASE B — LOOKUP RESPONSE (evaluate first): the entry immediately preceding this agent turn is a details_past tool result AND the caller has not spoken since. If multiple_past_appointments is true: speak the message field verbatim, HALT, and wait for the caller to pick by number or date/time; on the next turn re-call details_past with appointment_date and appointment_time from the matching past_appointments entry. Otherwise read practitioner_preference, practitioner_id, appointment_type, appointment_type_id, business_id, and business_name from the response. When business_id is present, set confirmed_business_id = business_id and confirmed_location from business_name (fuzzy-match against this clinic location names). Store all other working context silently. If appointment_type_id is present and not "none", enter the matching service/category branch for that appointment type (skip LOCATION GATE when confirmed_location is already set; otherwise run LOCATION GATE or gate questions as this clinic requires). If only practitioner is resolved and service is still unknown, speak one brief line naming the practitioner and ask which service — use this clinic's service menu. HALT when a spoken question was required.
```

**`evolution_physiotherapy_and_performance` override:**

```
PHASE B — LOOKUP RESPONSE (evaluate first): the entry immediately preceding this agent turn is a details_past tool result AND the caller has not spoken since. If multiple_past_appointments is true: speak the message field verbatim, HALT, and wait for the caller to pick by number or date/time; on the next turn re-call details_past with appointment_date and appointment_time from the matching past_appointments entry. Otherwise read appointment_type and appointment_type_id from the response. Store the returned practitioner as confirmed_practitioner / confirmed_practitioner_id (single-practitioner clinic -- do not announce the match). If appointment_type_id is present and not "none", proceed directly to STEP 1 using that appointment_type_id and appointment_type. If appointment_type_id is absent or "none", ask the PHYSIOTHERAPY variant question (standard appointment or extended review). HALT. If the result has a message field and no usable appointment_type, speak that message verbatim first.
```

### `RULES_SPOKEN_OUTPUT_EXCEPTION`

RULES section's sentence describing which turns may combine spoken output with a tool call (CONCERN-GUIDED clause differs because each clinic's concern-guided path ends differently)

**Default (`new_med_skin`):**

```
Spoken output is permitted only on turns that ask the caller a question and do not end in a tool call. The only exceptions are CONCERN-GUIDED turns, where one brief affirming sentence precedes the universal_router call, and confirm_service tool calls, which speak exactly one filler phrase from the TOOL-CALL FILLER set immediately before the call per CONFIRM_SERVICE FILLER RULE. All other turns ending in a tool call: tool call only, zero spoken output before or after.
```

**`evolution_physiotherapy_and_performance` override:**

```
Spoken output is permitted only on turns that ask the caller a question and do not end in a tool call. The only exceptions are CONCERN-GUIDED turns, where one brief affirming sentence precedes the spoken variant question, and confirm_service tool calls, which speak one filler phrase from the TOOL-CALL FILLER set first per CONFIRM_SERVICE FILLER RULE. All other turns ending in a tool call: tool call only, zero spoken output before or after.
```

### `CONCERN_GUIDED_RULE_BODY`

CONCERN-GUIDED RESOLUTION RULE's full body -- what happens once the rule fires (differs: evolution ends in a spoken variant question with no tool call; new_med_skin calls the tool same-turn)

**Default (`new_med_skin`):**

```
CONCERN-GUIDED RESOLUTION RULE: Fires when the caller's current message contains a physical symptom, condition, or goal (e.g. "my skin is really dry", "I have acne"). Does not fire on affirmatives ("yes", "sure", "I have"), generic booking language, or messages that require inference -- STEP C already acknowledged those. Only fires when the message explicitly uses specific symptom vocabulary. When it fires: speak one brief empathetic sentence connecting their concern to the selected treatment, then call universal_router in the same turn. The spoken line and tool call are the entirety of that turn's output.
```

**`evolution_physiotherapy_and_performance` override:**

```
CONCERN-GUIDED RESOLUTION RULE: Fires when the caller's current message contains a physical symptom, condition, or goal (e.g. "my back is really sore", "I've hurt my knee"). Does not fire on affirmatives ("yes", "sure", "I have"), generic booking language, or messages that require inference -- STEP C already acknowledged those. Only fires when the message explicitly uses specific symptom vocabulary. When it fires: speak one brief empathetic sentence, then ask the PHYSIOTHERAPY variant question (standard appointment or extended review) in the same turn. HALT. Do NOT call universal_router this turn -- the variant has not been chosen yet.
```

### `IMPLIED_SERVICE_RULE_BODY`

IMPLIED-SERVICE CONFIRMATION RULE's full body

**Default (`new_med_skin`):**

```
IMPLIED-SERVICE CONFIRMATION RULE: Fires when {{implied_service}} resolves to a category via quick-match or CATEGORY TABLE (i.e. the caller named a service on a prior turn and it is now being resolved after the gate answer). Speak exactly ONE brief confirmation line: "Let's get you booked in for a [appointment_type_name]." Then call universal_router in the same turn. The spoken line and tool call are the entirety of that turn's output. NEVER output MENU_LIST in this case.
```

**`evolution_physiotherapy_and_performance` override:**

```
IMPLIED-SERVICE CONFIRMATION RULE: Fires when {{implied_service}} resolves to PHYSIOTHERAPY via quick-match or CATEGORY TABLE (i.e. the caller named a service on a prior turn and it is now being resolved after the gate answer). SCOPED EXCEPTION: because PHYSIOTHERAPY always requires the variant question (see VARIANT-FIRST RULE), this rule does not speak a confirmation line or call universal_router directly -- instead, ask the PHYSIOTHERAPY variant question (standard appointment or extended review). HALT. NEVER output MENU_LIST in this case.
```

### `AFTER_ROUTER_CALL_NOTE`

Closing sentence describing what happens after universal_router is called

**Default (`new_med_skin`):**

```
After calling universal_router, this node's job is finished -- the tool call, preceded only by the single mandated filler phrase for confirm_service calls (per CONFIRM_SERVICE FILLER RULE), is the entirety of that turn's output.
```

**`evolution_physiotherapy_and_performance` override:**

```
After calling universal_router, this node's job is finished -- the tool call is the entirety of that turn's output.
```

### `SERVICE_ALIAS_QUICK_MATCH_ENTRIES`

SERVICE ALIAS QUICK-MATCH bullet list mapping caller phrases straight to a category (per-clinic service vocabulary)

**Default (`new_med_skin`):**

```
- "botox" / "preventative lines" / "muscle relaxant" / "neurotoxin" / "wrinkle relaxer" -> FACIAL_LINES (Wrinkles & Lines)
- "filler" / "dermal filler" / "volume" / "lip filler" / "cheek filler" / "chin augmentation" / "lip plumping" / "cheek definition" -> FACIAL_VOLUME (Contouring & Fillers)
- "acne" / "peel" / "ZO peel" / "chemical peel" / "exfoliation" / "glycolic" / "salicylic" / "TCA peel" / "brightening" / "sun damage" / "age spots" / "texture" -> SKIN_PEELS
- "hydration" / "booster" / "NCTF" / "profhilo" / "skin booster" / "micro hydration" / "moisture boost" / "radiance" / "glow" -> SKIN_QUALITY (Micro-Hydration)
- "LED" / "light therapy" / "phototherapy" / "red light" / "infrared" / "photobiomodulation" -> LED Light Therapy
- "HIFU" / "Liftera" / "ultrasound" / "skin tightening" / "lift" / "laxity" / "sagging" / "jawline" / "neck tightening" / "thermal lift" -> LIFTERA
- "PRF" / "platelet" / "PRP" / "regenerative" / "hair loss" / "collagen stimulation" -> PRF
- "bioremodelling" / "bio-remodelling" / "bio remodelling" / "profhilo" / "structural hydration injection" / "remodelling injection" / "skin remodelling" -> BIO_REMODELLING (Bio-remodelling Injections)
- "biostimulator" / "bio stimulator" / "collagen stimulator" / "sculptra" / "radiesse" / "collagen-stimulating" / "collagen biostimulator" -> BIOSTIMULATOR (Collagen-Stimulating Biostimulator)
- "regenerative biotech" / "signal cell therapy" / "biotech therapy" / "signal-cell skin" / "scalp biotech" / "cell therapy" -> REGENERATIVE (Regenerative Biotech Therapy)
```

**`evolution_physiotherapy_and_performance` override:**

```
- "exercise class" / "clinical exercise class" / "clinical exercise" / "group class" / "class" / "classes" / "group session" / "exercise group" -> EXERCISE CLASS
- "physio" / "physiotherapy" / "physical therapy" / "appointment" / "treatment" -> PHYSIOTHERAPY
- "back pain" / "neck pain" / "shoulder pain" / "knee pain" / "hip pain" / "joint pain" / "muscle pain" -> PHYSIOTHERAPY
- "sports injury" / "injury" / "sprain" / "strain" / "pulled muscle" -> PHYSIOTHERAPY
- "rehab" / "rehabilitation" / "recovery" -> PHYSIOTHERAPY
- "review" / "follow up" / "check up" / "reassessment" -> PHYSIOTHERAPY
```

### `RESCHEDULE_REENTRY_ACTION`

RESCHEDULE RE-ENTRY GUARD's action once patient_status is already established (ask a variant question vs go straight to CATEGORY RESOLUTION)

**Default (`new_med_skin`):**

```
  Go directly to CATEGORY RESOLUTION using the caller's current message or MENU_LIST if no service named.
```

**`evolution_physiotherapy_and_performance` override:**

```
  Ask the PHYSIOTHERAPY variant question (standard appointment or extended review). HALT.
```

### `INFO_PIVOT_IMPLIED_SERVICE_LOGIC`

INFO PIVOT RETURN GUARD's handling once {{implied_service}} is set (evolution: single gated category shortcut; new_med_skin: matches CATEGORY TABLE, branches on whether that category still needs a variant question)

**Default (`new_med_skin`):**

```
    IF {{implied_service}} is set -> match implied_service to CATEGORY TABLE -> enter that branch:
      - If the matched category is FACIAL_VOLUME, SKIN_PEELS, or BIO_REMODELLING AND working_variant_type is not already set: this category's variant question still applies -- ask that branch's variant question (spoken only, no tool call). HALT. Wait for the caller's reply; on the next turn speak one filler phrase from the TOOL-CALL FILLER set, then map the reply to the branch's working_id and call universal_router intent="confirm_service" with info_pivot_source="node_8" in payload. Per CONFIRM_SERVICE FILLER RULE.
      - Otherwise (the matched category has no variant question, or working_variant_type is already set from an earlier turn): speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router intent="confirm_service" with info_pivot_source="node_8" in payload. Per CONFIRM_SERVICE FILLER RULE. The filler phrase plus the tool call is the entirety of that turn's output.
    IF {{appointment_type_id}} != "none" -> proceed directly to CATEGORY RESOLUTION -> speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router intent="confirm_service" with info_pivot_source="node_8" in payload. Per CONFIRM_SERVICE FILLER RULE. The filler phrase plus the tool call is the entirety of that turn's output.
```

**`evolution_physiotherapy_and_performance` override:**

```
    IF {{implied_service}} is set and resolves to PHYSIOTHERAPY -> ask the PHYSIOTHERAPY variant question (standard appointment or extended review). HALT.
    IF {{appointment_type_id}} != "none" -> proceed directly to CATEGORY RESOLUTION -> speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router intent="confirm_service" with info_pivot_source="node_8" in payload. Per CONFIRM_SERVICE FILLER RULE.
```

### `MENU_LIST_PHRASE`

MENU_LIST template -- the spoken service-menu recap phrase

**Default (`new_med_skin`):**

```
consultations for Autologous Platelet Rich Fibrin, Facial Lines and Wrinkles, Facial Volume and Contouring, Professional Skin Peels, Skin Quality and Micro-Hydration, LED Light Therapy, Liftera, Bio-remodelling Injections, Collagen-Stimulating Biostimulator, and Regenerative Biotech Therapy.
```

**`evolution_physiotherapy_and_performance` override:**

```
physiotherapy consultations and clinical exercise classes here -- which would you like to book?
```

### `NOT_OFFERED_FIRST_PHRASE`

NOT_OFFERED template, first use in the call

**Default (`new_med_skin`):**

```
offer consultations for Autologous Platelet Rich Fibrin, Facial Lines and Wrinkles, Facial Volume and Contouring, Professional Skin Peels, Skin Quality and Micro-Hydration, LED Light Therapy, Liftera, Bio-remodelling Injections, Collagen-Stimulating Biostimulator, and Regenerative Biotech Therapy. Would you like to book one of thos
```

**`evolution_physiotherapy_and_performance` override:**

```
have physiotherapy consultations and clinical exercise classes. Which would you lik
```

### `NOT_OFFERED_SECOND_PHRASE`

NOT_OFFERED template, second+ use in the call

**Default (`new_med_skin`):**

```
e list this call): "We don't have [term] here either -- did any of the services I mentioned sound like it might
```

**`evolution_physiotherapy_and_performance` override:**

```
is call): "We don't have [term] here either -- would a physiotherapy consultation or an exercise class
```

### `CONCRETE_EXAMPLES_LIST`

CONCRETE EXAMPLES worked bullet list under SERVICE MATCHING PRIORITY

**Default (`new_med_skin`):**

```
- Caller: "botox" → Found in QUICK-MATCH under FACIAL_LINES → set working_type="Wrinkles & Lines", working_id="1706874590543750904" → Call universal_router. DO NOT say "we don't offer botox".
- Caller: "filler" → Found in QUICK-MATCH under FACIAL_VOLUME → Ask variant question (Contouring or Reversal). DO NOT say "we don't offer fillers".
- Caller: "LED therapy" → Found in QUICK-MATCH under LED → working_type="LED light Therapy", working_id="1649827716951713108" → Call universal_router.
- Caller: "Botox for forehead" → Contains "botox" → resolve as FACIAL_LINES immediately. Ignore "forehead" modifier—category match is sufficient.
```

**`evolution_physiotherapy_and_performance` override:**

```
- Caller: "physio" → Found in QUICK-MATCH under PHYSIOTHERAPY → Ask the variant question (standard appointment or extended review). DO NOT say "we don't offer physio".
- Caller: "back pain" → Found in QUICK-MATCH under PHYSIOTHERAPY → Ask the variant question (standard appointment or extended review). DO NOT say "we don't offer that".
- Caller: "I need a follow up" → Found in QUICK-MATCH under PHYSIOTHERAPY → Ask the variant question (standard appointment or extended review).
- Caller: "shoulder pain from tennis" → Contains "pain" → resolve as PHYSIOTHERAPY immediately. Ignore "tennis" modifier—category match is sufficient.
```

### `CATEGORY_TABLE_ENTRIES`

CATEGORY TABLE's full entry list (one block per category, caller-phrase -> CATEGORY mapping) plus the closing 'BEFORE outputting NOT_OFFERED' MANDATORY CHECK line -- entirely per-clinic content

**Default (`new_med_skin`):**

```
PRF (Autologous Platelet Rich Fibrin):
"PRF" / "platelet rich fibrin" / "platelet" / "PRP" / "autologous" / "micro needling prf" / "prf facial" / "prf hair" / "platelet therapy" / "regenerative therapy" / "stem cell" / "collagen stimulation" / "hair restoration" / "hair loss treatment" -> PRF

FACIAL_LINES (Wrinkles & Lines):
"wrinkles" / "lines" / "anti-wrinkle" / "frown lines" / "crow's feet" / "forehead lines" / "fine lines" / "botox" / "anti wrinkle" / "dynamic wrinkles" / "expression lines" / "static lines" / "bunny lines" / "smile lines" / "lip lines" / "marionette lines" / "jaw clenching" / "neurotoxin" / "muscle relaxant" / "botulinum" / "preventative lines" / "preventive wrinkles" / "wrinkle relaxer" -> FACIAL_LINES

FACIAL_VOLUME (Fillers & Contouring):
"filler" / "volume" / "contouring" / "lip filler" / "cheek filler" / "filler reversal" / "dissolve filler" / "hyaluronidase" / "facial volume" / "facial contouring" / "dermal filler" / "hyaluronic acid" / "volumizer" / "lips" / "cheeks" / "chin augmentation" / "lip plumping" / "cheek definition" / "underfiller" / "non-surgical facelift" / "sculptural" / "enhancement" / "restylane" / "juvederm" -> FACIAL_VOLUME

SKIN_QUALITY (Injectable Boosters - NOT peels):
DISAMBIGUATION: "skin booster" and "NCTF" are ALWAYS SKIN_QUALITY (injectable treatment). They are NEVER SKIN_PEELS. Check this first if unsure.
"skin booster" / "NCTF" / "micro hydration" / "skin quality" / "hydration" / "skin hydration" / "skin booster injection" / "profhilo" / "skin hydration injection" / "moisture boost" / "dehydrated skin" / "skin elasticity" / "radiance" / "glow" / "skincare injection" / "bio-stimulation" / "hydrolyzed" / "hyaluronic injectable" -> SKIN_QUALITY

SKIN_PEELS (Chemical & Topical Peels):
"peel" / "skin peel" / "chemical peel" / "ZO peel" / "exfoliation" / "acne treatment" / "skin brightening" / "anti-aging peel" / "hand rejuvenation" / "complexion" / "oil management" / "glycolic acid" / "salicylic acid" / "TCA peel" / "Jessner peel" / "mechanical exfoliation" / "texture" / "scars" / "post-inflammatory" / "hyperpigmentation" / "age spots" / "sun damage" / "surface" / "keratolysis" -> SKIN_PEELS

LED (Light Therapy):
"LED" / "LED light" / "LED therapy" / "light therapy" / "red light" / "LED facial" / "photobiomodulation" / "infrared light" / "amber light" / "light-based treatment" / "phototherapy" / "light healing" / "collagen induction" -> LED

LIFTERA (HIFU - High Intensity Focused Ultrasound):
"Liftera" / "HIFU" / "ultrasound facial" / "focused ultrasound" / "skin tightening" / "face lift" / "non surgical lift" / "thermal lift" / "micro-focus ultrasound" / "non-invasive lifting" / "sagging" / "laxity" / "lift and tighten" / "neck tightening" / "jawline definition" -> LIFTERA

BIO_REMODELLING (Bio-remodelling Injections):
DISAMBIGUATION: "bio-remodelling" and "bioremodelling" map here, NOT to SKIN_QUALITY (NCTF). Check this first if unsure.
"bioremodelling" / "bio-remodelling" / "bio remodelling" / "profhilo" / "structural hydration injection" / "remodelling injection" / "skin remodelling" / "structural hydration" / "bio remodelling injection" -> BIO_REMODELLING

BIOSTIMULATOR (Collagen-Stimulating Biostimulator):
"biostimulator" / "bio stimulator" / "collagen stimulator" / "sculptra" / "radiesse" / "collagen-stimulating" / "collagen biostimulator" / "biostimulant" / "collagen injection" -> BIOSTIMULATOR

REGENERATIVE (Regenerative Biotech Therapy):
"regenerative biotech" / "signal cell therapy" / "biotech therapy" / "signal-cell skin" / "scalp biotech" / "cell therapy" / "regenerative signal" / "biotech skin therapy" -> REGENERATIVE

If the caller's term plausibly spans multiple categories, ask "We have a few options that could be a good fit -- [relevant category names only, 'or'-separated]. Which of those were you thinking?" Halt. On response, match against CATEGORY TABLE normally.

BEFORE outputting NOT_OFFERED, MANDATORY CHECK: Re-scan SERVICE ALIAS QUICK-MATCH one more time to catch any term that might have been missed. If term appears in quick-match, resolve to that category immediately. If still no match -> NOT_OFFERED template. Halt. Retry on next turn.
```

**`evolution_physiotherapy_and_performance` override:**

```
EXERCISE CLASS (Clinical exercise class):
"exercise class" / "clinical exercise class" / "clinical exercise" / "group class" / "class" / "classes" / "group session" / "exercise group" -> EXERCISE CLASS

PHYSIOTHERAPY (Physiotherapy Consultation):
"physio" / "physiotherapy" / "physical therapy" / "treatment" / "appointment" / "back pain" / "neck pain" / "shoulder pain" / "knee pain" / "hip pain" / "ankle pain" / "elbow pain" / "wrist pain" / "sports injury" / "injury" / "sprain" / "strain" / "pulled muscle" / "muscle pain" / "joint pain" / "stiffness" / "rehab" / "rehabilitation" / "recovery" / "assessment" / "review" / "check up" / "follow up" / "mobility" / "posture" / "manual therapy" / "dry needling" -> PHYSIOTHERAPY

BEFORE outputting NOT_OFFERED, MANDATORY CHECK: Re-scan SERVICE ALIAS QUICK-MATCH one more time to catch any term that might have been missed. If term appears in quick-match, resolve to EXERCISE CLASS or PHYSIOTHERAPY immediately. If still no match -> NOT_OFFERED template. Halt. Retry on next turn.
```

### `VARIANT_FIRST_SCOPE_TEXT`

VARIANT-FIRST RULE's SCOPE line and main body sentence -- names which categories require the variant question before booking

**Default (`new_med_skin`):**

```
SCOPE: this rule only applies once CATEGORY RESOLUTION has already resolved the caller's message to FACIAL_VOLUME or SKIN_PEELS. When no category has been resolved yet, use MENU_LIST instead — never ask the variant question as a substitute for MENU_LIST.
For any turn where the resolved service branch is FACIAL_VOLUME or SKIN_PEELS: the FIRST spoken output for that branch MUST be the branch's variant question -- spoken only, no tool call. This rule fires based on the RESOLVED CATEGORY -- not on which turn the service was named. It applies whether the category was identified in the current turn, in a prior turn, or via any other means. HALT after the variant question. Do NOT call universal_router -- not even pre-emptively -- until the caller answers with a specific sub-type. The variant question and the tool call happen in SEPARATE turns.
```

**`evolution_physiotherapy_and_performance` override:**

```
SCOPE: this rule applies once CATEGORY RESOLUTION has resolved the caller's message to PHYSIOTHERAPY. It does NOT apply to EXERCISE CLASS — exercise classes route directly to confirm_service without a variant question. When no category has been resolved yet, use MENU_LIST instead — never ask the variant question as a substitute for MENU_LIST.
The FIRST spoken output once PHYSIOTHERAPY is resolved MUST be the variant question below -- spoken only, no tool call. This rule fires based on the RESOLVED CATEGORY -- not on which turn the service was named. It applies whether the category was identified in the current turn, in a prior turn, via SERVICE ALIAS QUICK-MATCH, via {{implied_service}}, or via any other means. HALT after the variant question. Do NOT call universal_router -- not even pre-emptively -- until the caller answers with a specific sub-type. The variant question and the tool call happen in SEPARATE turns.
```

### `CATEGORY_BRANCHES_BODY`

CATEGORY BRANCHES section's every category's full branch definition (variant questions, working_type/working_id mappings, Overlap rule where present). Entirely per-clinic; this is the largest slot in the template.

**Default (`new_med_skin`):**

```
### PRF
Single appointment type. No variant question.
working_type = "Facial or Hair Single Session  (PRF + Micro Needling + LED light)", working_id = "1547596617815696896". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.

### FACIAL_LINES
Single appointment type. No variant question.
working_type = "Wrinkles & Lines", working_id = "1706874590543750904". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.


### FACIAL_VOLUME
Ask: (SELF/null) "Were you after a Facial Contouring and Volume consultation, or a Filler Reversal consultation?"
Ask (OTHER): "Were they after a Facial Contouring and Volume consultation, or a Filler Reversal consultation?"
Store service_hint = "Facial Volume and Contouring". Halt.
Facial Contouring and Volume -> working_type = "Facial Contouring & Volume", working_id = "1706888090540320507". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.
Filler Reversal -> working_type = "Consultation for Filler Reversal", working_id = "1546836301691495818". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.


### SKIN_PEELS
Ask: (SELF/null) "What area are you looking to address -- acne or oily skin, anti-aging, skin brightening and tone, hand rejuvenation, general exfoliation and rejuvenation, or hydration and barrier support?"
Ask (OTHER): "What area are they looking to address -- acne or oily skin, anti-aging, skin brightening and tone, hand rejuvenation, general exfoliation and rejuvenation, or hydration and barrier support?"
Store service_hint = "Professional Skin Peels". Halt.
Concern mapping:
Acne / oily skin / complexion / breakouts -> working_type = "Professional Skin Peels", working_id = "1547637214324729353"
Anti-aging / aging / fine lines / surface rejuvenation -> working_type = "Professional Skin Peels", working_id = "1547635013883799048"
Brightening / skin tone / texture / pigmentation -> working_type = "Professional Skin Peels", working_id = "1547660944723682830"
Hands / hand skin / hand rejuvenation -> working_type = "Professional Skin Peels", working_id = "1547656979739059724"
Exfoliation / rejuvenation / general peel / stimulator peel -> working_type = "Professional Skin Peels", working_id = "1547981211350083106"
Hydration / barrier / dry skin / hydration treatment -> working_type = "Professional Skin Peels", working_id = "1547985948304746020"
Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router once the concern is mapped. Per CONFIRM_SERVICE FILLER RULE.

### Overlap rule
If caller names two or more services in a single message:
  - Identify all matches against the CATEGORY TABLE in order of mention.
  - Store all matched categories as a list internally (e.g. match_1, match_2, match_3).
  - Acknowledge all of them by name: "I can get you booked for [match_1], [match_2], and [match_3] -- let's start with [match_1]."
  - Proceed with match_1 only. Enter its branch normally.
  - Store remaining matches as pending_services in order.
  - Call universal_router for match_1. The tool call is the turn.
  - Name all services upfront -- silently dropping any named service is a compliance failure.

### SKIN_QUALITY
Note: "skin booster", "NCTF", "micro hydration", "skin quality" → this branch. These are injectable treatments -- do NOT confuse with SKIN_PEELS (chemical peels).
Single appointment type. No variant question.
working_type = "NCTF Skin Booster Full Face & Neck + LED light", working_id = "1542568447097972528". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.

### LED
Single appointment type. No variant question.
working_type = "LED light Therapy", working_id = "1649827716951713108". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.

### LIFTERA
Single appointment type. No variant question.
working_type = "Liftera - HIFU - Facial & Neck", working_id = "1709882585678620111". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.

### BIO_REMODELLING
Ask: (SELF/null) "Were you after Bio-remodelling Injections for structural hydration, or the Deep Structural Bio-remodelling treatment for volume restoration?"
Ask (OTHER): "Were they after Bio-remodelling Injections for structural hydration, or the Deep Structural Bio-remodelling treatment for volume restoration?"
Store service_hint = "Bio-remodelling Injections". Halt.
Structural hydration / injections / Profhilo / hydration bio-remodelling -> working_type = "Bio-remodelling Injections (Structural Hydration)", working_id = "1947798329073083981". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.
Deep structural / volume restoration / adipose / fat restoration -> working_type = "Deep Structural Bio-remodelling (Adipose Tissue Restoration)", working_id = "1947806074266461774". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.

### BIOSTIMULATOR
Single appointment type. No variant question.
working_type = "Collagen-Stimulating Biostimulator", working_id = "1947784906704692812". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.

### REGENERATIVE
Single appointment type. No variant question.
working_type = "Regenerative Biotech Therapy (Signal-Cell Skin & Scalp Therapy) + LED light", working_id = "1947811726971905615". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.

```

**`evolution_physiotherapy_and_performance` override:**

```
### PHYSIOTHERAPY
Ask: (SELF/null) "Would you like a standard appointment, or would you prefer the longer extended review?"
Ask (OTHER): "Would they like a standard appointment, or would they prefer the longer extended review?"
Store service_hint = "Physiotherapy Consultation". Halt.
Standard / regular / normal / usual / shorter one -> working_type = "Standard physiotherapy consultation", working_id = "1319391494854941107". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE.
Extended / extended review / the review / longer / longer one / full -> working_type = "Physiotherapy extended review consultation", working_id = "1319396627315694009". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE.

### EXERCISE CLASS
No variant question needed -- route directly.
Apply CONCERN-GUIDED RESOLUTION RULE case 2 when applicable (empathetic line + tool call in same turn, ONLY if routing here directly from the caller's first message with no prior question asked this entry). All other cases: speak one filler phrase from the TOOL-CALL FILLER set, then the tool call, per CONFIRM_SERVICE FILLER RULE.
Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "1319393805438294453", "appointment_type": "Clinical exercise class"}. Add to payload if captured: booking_for, family_member_name, timeframe_raw, practitioner_preference. HALT.

---
```

### `PRAC_MATCH_EXAMPLE_B`

PRACTITIONER-ONLY PATH PATTERN B's worked example (surname token extraction)

**Default (`new_med_skin`):**

```
Rachel Lee-oh-nee" / "Rachel Leoney" / "Rachel Leone" → surname tokens → "Leoni" → Rachel Leoni
```

**`evolution_physiotherapy_and_performance` override:**

```
Benjamin Butler Bonus" / "Benjamin Butler-Bonis" → surname tokens → "Butler-Bonnice" → Benjamin Butler-Bonnice
```

### `PRACTITIONER_ONLY_GATE_LOGIC`

PRACTITIONER-ONLY PATH's gate logic before 'On response:' (evolution: single practitioner/single category, ask gate directly; new_med_skin: look up practitioner_services, gate only if multi-category)

**Default (`new_med_skin`):**

```
Look up in {{practitioner_services}}.
If the practitioner offers multiple categories -- ask the gate question first (MENU or MENU_OTHER). Halt.
```

**`evolution_physiotherapy_and_performance` override:**

```
This clinic has a single practitioner offering a single category (PHYSIOTHERAPY) -- ask the gate question first (MENU or MENU_OTHER) if {{patient_status}} is not already set. Halt.
```

### `PRACTITIONER_ONLY_RESPONSE_BODY`

PRACTITIONER-ONLY PATH's Yes/No outcome lines after 'On response:'

**Default (`new_med_skin`):**

```
No -> patient_status = "new", working_type = "Consultation For New Patients", working_id = "1480843963127571628". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.
Yes -> patient_status = "existing". Output MENU_LIST template verbatim. Halt. On response, enter the matching category branch. Store practitioner_preference = [matched name] throughout.
```

**`evolution_physiotherapy_and_performance` override:**

```
No -> patient_status = "new". Go to NEW PATIENT ACTION.
Yes -> patient_status = "existing". Store practitioner_preference = "Benjamin Butler-Bonnice". Ask the PHYSIOTHERAPY variant question (standard appointment or extended review). HALT.
```

### `SCAN_ON_ENTRY_EARLY_ITEMS`

SCAN ON ENTRY's early lettered items before Scan J (evolution: A0b class-shortcut scan + C + D; new_med_skin: C + D + E variant-already-set skip)

**Default (`new_med_skin`):**

```
C. If agent's last turn was a variant question AND caller responded with a clear selection: map to the corresponding path for the active branch (FACIAL_VOLUME or SKIN_PEELS).
D. If caller names a practitioner in current message -> store practitioner_preference. EDGE CASE: If agent's last turn was a variant question and caller said a practitioner name instead of a selection (Scan C did not fire): re-ask the variant question using PRAC_VARIANT template.
E. If working_variant_type already set when entering a category branch that asks a variant question -> skip the question, map directly.
```

**`evolution_physiotherapy_and_performance` override:**

```
A0b. CLASS SHORTCUT (evaluate FIRST, before C/D/J and before STEP 0): If caller's current message contains "exercise class", "clinical exercise class", "clinical exercise", "group class", "class", "classes", "group session", or "exercise group" → speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "1319393805438294453", "appointment_type": "Clinical exercise class"}. Add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured. Per CONFIRM_SERVICE FILLER RULE. HALT.

C. If agent's last turn was the PHYSIOTHERAPY variant question AND caller responded with a clear selection (standard or extended review): map to the corresponding working_id (see PHYSIOTHERAPY branch).
D. If caller names a practitioner in current message -> store practitioner_preference. EDGE CASE: If agent's last turn was the PHYSIOTHERAPY variant question and caller said a practitioner name instead of a selection (Scan C did not fire): re-ask the variant question using PRAC_VARIANT template.
```

### `SCAN_J_NEW_OUTCOME`

Scan J's 'new' patient_status outcome -- maps to the new-patient appointment type

**Default (`new_med_skin`):**

```
Consultation For New Patients", working_id = "1480843963127571628". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT
```

**`evolution_physiotherapy_and_performance` override:**

```
Initial physiotherapy consultation", working_id = "1319390333250836914". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE
```

### `STEP1_RESCHEDULE_GUARD_ACTION`

STEP 1's action when RESCHEDULE RE-ENTRY GUARD fired

**Default (`new_med_skin`):**

```
go directly to CATEGORY RESOLUTION. Treat as existing patient. HALT after category resolution
```

**`evolution_physiotherapy_and_performance` override:**

```
ask the PHYSIOTHERAPY variant question (standard appointment or extended review). HALT. Treat as existing patient
```

### `STEP1_SCAN_C_ACTION`

STEP 1's action when Scan C resolved a variant/branch selection

**Default (`new_med_skin`):**

```
branch selection -> map to working_id for active branch
```

**`evolution_physiotherapy_and_performance` override:**

```
variant selection -> map to working_id (see PHYSIOTHERAPY branch: Standard physiotherapy consultation or Physiotherapy extended review consultation)
```

### `STEP1_CATEGORY_MATCH_BLOCK`

STEP 1's handling once the caller's message matches a category in the CATEGORY TABLE, plus the 'yes/ok/sure' implied-service shortcut

**Default (`new_med_skin`):**

```
IF caller's message matches a category in the CATEGORY TABLE -> go to that branch's step 1 (its mandatory first question). Do NOT skip ahead to step 2/3 or call confirm_service directly -- matching a category is not the same as having answered its gate question.
IF caller said "yes" / "ok" / "sure" with no service term AND {{implied_service}} is set -> run {{implied_service}} through SERVICE ALIAS QUICK-MATCH first, then CATEGORY TABLE if no quick-match hit. If a category resolves: apply IMPLIED-SERVICE CONFIRMATION RULE (speak "Let's get you booked in for a [appointment_type_name]." THEN call universal_router in the same turn). NEVER output MENU_LIST. Example: {{implied_service}}="botox" -> FACIAL_LINES -> say "Let's get you booked in for a Wrinkles & Lines appointment." + call router.
```

**`evolution_physiotherapy_and_performance` override:**

```
IF caller's message matches EXERCISE CLASS in the CATEGORY TABLE OR SERVICE ALIAS QUICK-MATCH resolves to EXERCISE CLASS -> EXERCISE CLASS branch (confirm_service directly, no variant question). HALT.
IF caller's message matches PHYSIOTHERAPY in the CATEGORY TABLE -> ask the PHYSIOTHERAPY variant question (standard appointment or extended review). HALT.
IF caller said "yes" / "ok" / "sure" with no service term AND {{implied_service}} is set -> run {{implied_service}} through SERVICE ALIAS QUICK-MATCH first, then CATEGORY TABLE if no quick-match hit. If EXERCISE CLASS resolves -> EXERCISE CLASS branch. HALT. If PHYSIOTHERAPY resolves -> ask the PHYSIOTHERAPY variant question (standard appointment or extended review). HALT. NEVER output MENU_LIST.
```

### `STEP1_IMPLIED_SERVICE_FALLBACK`

STEP 1's fallback handling when the caller's message matches nothing but {{implied_service}} is set

**Default (`new_med_skin`):**

```
IF {{implied_service}} is set -> run {{implied_service}} through SERVICE ALIAS QUICK-MATCH first, then CATEGORY TABLE. If resolved: apply IMPLIED-SERVICE CONFIRMATION RULE (spoken confirmation + router call). If no match found after both checks -> OUTPUT MENU_LIST template verbatim. HALT.
```

**`evolution_physiotherapy_and_performance` override:**

```
IF {{implied_service}} is set -> run {{implied_service}} through SERVICE ALIAS QUICK-MATCH first, then CATEGORY TABLE. If EXERCISE CLASS resolves -> EXERCISE CLASS branch. HALT. If PHYSIOTHERAPY resolves -> ask the PHYSIOTHERAPY variant question (standard appointment or extended review). HALT. If no match found after both checks -> OUTPUT MENU_LIST template verbatim. HALT.
```

## 3. NORMALISED DRIFT

8 places where both clinics carry the same rule spelled differently, judged genuinely identical in meaning, and folded into one canonical literal in the template rather than a per-clinic slot. Each is a real diff in the mechanical verification below (§4) — that is expected; it is what "normalise" means here.

### 1. CONFIRM_SERVICE FILLER RULE — trailing sentence

new_med_skin's copy has one extra trailing sentence ("Speaking one filler phrase avoids that failure mode.") that evolution's lacks — a strict superset, not a contradiction. Adopted new_med_skin's fuller version for both. Affects: evolution's verification diff.

**evolution's original wording:**
```
- CONFIRM_SERVICE FILLER RULE: Any turn that calls universal_router with intent="confirm_service" speaks exactly one filler phrase from the TOOL-CALL FILLER set (e.g. "One moment.") immediately before the tool call, then HALTs -- the same TOOL-CALL FILLER pattern every other tool call in this node already follows. Do not speak anything else in this turn -- no acknowledgement of the caller's answer, no preview or announcement of the booking, no repeating the service or duration back. Exactly one filler phrase, then the tool call, nothing more. This rule replaces the prior CONFIRM_SERVICE SILENT RULE (fully-silent, zero-text tool call) -- confirmed live on 2026-08-12/13 that a fully-silent, user-triggered tool-call-only turn can fail to generate at all on ElevenLabs' platform (reproduced twice, deterministic, conversation IDs conv_9601kzv1zz2aebjsgqv17p68fhd3 and conv_8501kzv43wxse3g86660bbv993hn).
```
**new_med_skin's original wording:**
```
- CONFIRM_SERVICE FILLER RULE: Any turn that calls universal_router with intent="confirm_service" speaks exactly one filler phrase from the TOOL-CALL FILLER set (e.g. "One moment.") immediately before the tool call, then HALTs -- the same TOOL-CALL FILLER pattern every other tool call in this node already follows. Do not speak anything else in this turn -- no acknowledgement of the caller's answer, no preview or announcement of the booking, no repeating the service or duration back. Exactly one filler phrase, then the tool call, nothing more. This rule replaces the prior CONFIRM_SERVICE SILENT RULE (fully-silent, zero-text tool call) -- confirmed live on 2026-08-12/13 that a fully-silent, user-triggered tool-call-only turn can fail to generate at all on ElevenLabs' platform (reproduced twice, deterministic, conversation IDs conv_9601kzv1zz2aebjsgqv17p68fhd3 and conv_8501kzv43wxse3g86660bbv993hn). Speaking one filler phrase avoids that failure mode.
```
**Template default (adopted from new_med_skin):**
```
- CONFIRM_SERVICE FILLER RULE: Any turn that calls universal_router with intent="confirm_service" speaks exactly one filler phrase from the TOOL-CALL FILLER set (e.g. "One moment.") immediately before the tool call, then HALTs -- the same TOOL-CALL FILLER pattern every other tool call in this node already follows. Do not speak anything else in this turn -- no acknowledgement of the caller's answer, no preview or announcement of the booking, no repeating the service or duration back. Exactly one filler phrase, then the tool call, nothing more. This rule replaces the prior CONFIRM_SERVICE SILENT RULE (fully-silent, zero-text tool call) -- confirmed live on 2026-08-12/13 that a fully-silent, user-triggered tool-call-only turn can fail to generate at all on ElevenLabs' platform (reproduced twice, deterministic, conversation IDs conv_9601kzv1zz2aebjsgqv17p68fhd3 and conv_8501kzv43wxse3g86660bbv993hn). Speaking one filler phrase avoids that failure mode.
```

### 2. PRE-ROUTING SILENCE — parenthetical vs. inline cross-reference

Differ only in whether "per CONFIRM_SERVICE FILLER RULE" is parenthesised. Adopted evolution's non-parenthetical form (matches the phrasing used everywhere else this cross-reference appears in both files). Affects: new_med_skin's verification diff.

**evolution's original wording:**
```
- PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only — never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen via tool calls only, preceded by nothing more than the single mandated filler phrase per CONFIRM_SERVICE FILLER RULE. Availability is unknown in this node.
```
**new_med_skin's original wording:**
```
- PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only — never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen via tool calls only, preceded by nothing more than the single mandated filler phrase (per CONFIRM_SERVICE FILLER RULE). Availability is unknown in this node.
```
**Template default (adopted from evolution):**
```
- PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only — never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen via tool calls only, preceded by nothing more than the single mandated filler phrase per CONFIRM_SERVICE FILLER RULE. Availability is unknown in this node.
```

### 3. URGENCY QUALIFIER — curly vs. straight quotes

Byte-identical except new_med_skin uses typographic quote marks (U+201C/U+201D) where evolution and the rest of the fleet use straight ASCII quotes. Confirmed programmatically: translating new_med_skin's curly quotes to straight makes the two lines identical. Adopted straight quotes (evolution's form, and the fleet convention). Affects: new_med_skin's verification diff.

**evolution's original wording:**
```
- URGENCY QUALIFIER: When the caller uses "emergency", "urgent", "as soon as possible", or "same day", this signals they want the earliest available appointment TODAY — it is NOT a medical emergency. Do NOT mention A&E, emergency departments, NHS lines, or any medical emergency resources. Treat urgency language as timeframe_raw="today" and resolve the service normally.
```
**new_med_skin's original wording:**
```
- URGENCY QUALIFIER: When the caller uses “emergency”, “urgent”, “as soon as possible”, or “same day”, this signals they want the earliest available appointment TODAY — it is NOT a medical emergency. Do NOT mention A&E, emergency departments, NHS lines, or any medical emergency resources. Treat urgency language as timeframe_raw=”today” and resolve the service normally.
```
**Template default (adopted from evolution):**
```
- URGENCY QUALIFIER: When the caller uses "emergency", "urgent", "as soon as possible", or "same day", this signals they want the earliest available appointment TODAY — it is NOT a medical emergency. Do NOT mention A&E, emergency departments, NHS lines, or any medical emergency resources. Treat urgency language as timeframe_raw="today" and resolve the service normally.
```

### 4. LOCATION RULE — curly vs. straight quotes

Same curly-vs-straight-quote drift as item 3, one quote pair. Adopted straight quotes. Affects: new_med_skin's verification diff.

**evolution's original wording:**
```
- LOCATION RULE: This clinic has ONE location. NEVER ask the caller about location. Do not ask "which location" or any variation.
```
**new_med_skin's original wording:**
```
- LOCATION RULE: This clinic has ONE location. NEVER ask the caller about location. Do not ask “which location” or any variation.
```
**Template default (adopted from evolution):**
```
- LOCATION RULE: This clinic has ONE location. NEVER ask the caller about location. Do not ask "which location" or any variation.
```

### 5. NEW PATIENT ACTION PART 1 — missing clarifying parenthetical

evolution's PART 1 carries a clarifying parenthetical (don't ALSO speak a separate filler phrase before this verbatim script) that new_med_skin's copy lacks. The TURN TYPE RULE already defines this as a Type C-2 combined turn for both clinics, so the parenthetical is a defensive restatement, not new logic. Adopted evolution's fuller form for both. Affects: new_med_skin's verification diff.

**evolution's original wording:**
```
  PART 1 (spoken first): Say VERBATIM (this is the turn's mandatory spoken line -- do not add a separate filler phrase before or after it): "..."
```
**new_med_skin's original wording:**
```
  PART 1 (spoken first): Say VERBATIM: "..."
```
**Template default (adopted from evolution):**
```
  PART 1 (spoken first): Say VERBATIM (this is the turn's mandatory spoken line -- do not add a separate filler phrase before or after it): "<<NEW_PATIENT_SCRIPT>>"
```

### 6. NEW PATIENT ACTION PART 2 — spelled-out field list vs. DRY cross-reference

Both require the same five optional context fields and the same fixed patient_status="new" — new_med_skin just references the shared CONFIRM_SERVICE PAYLOAD VARIABLES block instead of repeating it, while evolution spells the list out again plus an explicit "it is fixed, never omit it" emphasis. Given Node 2 is HALT-critical (per repo CLAUDE.md), adopted evolution's more explicit/defensive form for both. Affects: new_med_skin's verification diff.

**evolution's original wording:**
```
  PART 2 (same turn, immediately after speech): Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "...", "appointment_type": "...", "patient_status": "new"}. patient_status is always "new" here -- it is fixed, never omit it. Also add these fields to the payload if non-empty: {{booking_for}}, {{family_member_name}}, {{practitioner_preference}}, {{timeframe_raw}}, {{preferred_gender}}.
```
**new_med_skin's original wording:**
```
  PART 2 (same turn, immediately after speech): Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "...", "appointment_type": "...", "patient_status": "new"}. Plus CONFIRM_SERVICE PAYLOAD VARIABLES if non-empty (see above).
```
**Template default (adopted from evolution):**
```
  PART 2 (same turn, immediately after speech): Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "<<NEW_PATIENT_APPT_ID>>", "appointment_type": "<<NEW_PATIENT_APPT_NAME>>", "patient_status": "new"}. patient_status is always "new" here -- it is fixed, never omit it. Also add these fields to the payload if non-empty: {{booking_for}}, {{family_member_name}}, {{practitioner_preference}}, {{timeframe_raw}}, {{preferred_gender}}.
```

### 7. SERVICE MATCHING PRIORITY — numbering

new_med_skin's live file numbers these steps 1, 3, 4 (skips "2"). Steps 2 and 3 (by content, ignoring the printed digit) are otherwise byte-identical between clinics. Normalised to sequential 1/2/3. **Also listed under Bugs Spotted below** — this is a live numbering defect in new_med_skin's current production file, not just a template-authoring choice. Affects: new_med_skin's verification diff.

**evolution's original wording:**
```
1. FIRST: ...
2. SECOND: If no quick-match hit, scan the full CATEGORY TABLE below for the term.
3. THIRD: If still no match, use NOT_OFFERED response and ask the MENU_LIST.
```
**new_med_skin's original wording:**
```
1. FIRST: ...
3. SECOND: If no quick-match hit, scan the full CATEGORY TABLE below for the term.
4. THIRD: If still no match, use NOT_OFFERED response and ask the MENU_LIST.
```
**Template default (adopted from evolution):**
```
1. FIRST: <<QUICK_MATCH_STEP1_TEXT>>no exceptions. Prevents "service not offered" errors.
2. SECOND: If no quick-match hit, scan the full CATEGORY TABLE below for the term.
3. THIRD: If still no match, use NOT_OFFERED response and ask the MENU_LIST.
```

### 8. Final TOOL CALL closing line

Same constraint (nothing spoken beyond the one filler phrase), worded differently; new_med_skin's phrasing is more explicit about the HALT. Adopted new_med_skin's version. Affects: evolution's verification diff.

**evolution's original wording:**
```
Speak one filler phrase from the TOOL-CALL FILLER set immediately before this call, per CONFIRM_SERVICE FILLER RULE -- no other spoken output before or after.
```
**new_med_skin's original wording:**
```
Speak one filler phrase from the TOOL-CALL FILLER set immediately before this call, then HALT -- per CONFIRM_SERVICE FILLER RULE, the filler phrase plus the tool call is the entirety of this turn's output.
```
**Template default (adopted from new_med_skin):**
```
Speak one filler phrase from the TOOL-CALL FILLER set immediately before this call, then HALT -- per CONFIRM_SERVICE FILLER RULE, the filler phrase plus the tool call is the entirety of this turn's output.
```

## 4. Verification

Mechanical round-trip: for each clinic, every `<<SLOT>>` token in the template was substituted with that clinic's value from the table above, then runs of 3+ consecutive CRLF sequences were collapsed to 2 (matching the documented generator contract — this is also what makes the two optional slots collapse cleanly to nothing when empty). The result was diffed against that clinic's actual current `node_2_service_resolution.txt` body.

**Result: every line of every diff is accounted for by one of the 8 NORMALISED DRIFT items above, or by a blank-line-RUN-COUNT reduction (2 blank lines → 1) at spots where the source file itself already had two consecutive blank lines — confirmed by a second pass that canonicalises *all* blank-line runs (any run of 2+) to a single marker on *both* the rendered and original text before diffing again: the residual diff after that canonicalisation is byte-identical to the 8 drift items and nothing else, for both clinics.** The double-blank-line spots are themselves pre-existing in the source files (confirmed directly against both raw files — see the `## UNIVERSAL ESCAPES` section, identical in both clinics, and new_med_skin's category-branch separators) and are not something template construction could avoid: any global "3+ newlines → 2" collapse — the documented, needed-for-empty-optional-slots behaviour — will also flatten a genuine pre-existing double-blank-line to a single one, regardless of slot boundaries. No content was lost; only a pre-existing whitespace inconsistency was normalised the same way the collapse rule normalises an empty optional slot's neighbouring blank lines.

Raw diff output (`nodes/node2_templates/node_2_b_gate_first.txt` + slot values, post-collapse, vs. current clinic files):

```diff
=== evolution_physiotherapy_and_performance ===
rendered length: 33493   original length: 33395
--- original
+++ rendered(template+slots, post-collapse)
@@ -2,7 +2,7 @@
 - CALLER CONTEXT: caller_name = {{patient_name_raw}} (may be empty -- use when set and natural, e.g. addressing the caller by name).
 - TOOL ROLES: `universal_router` sets routing variables only.
 - TURN TYPE RULE: Each turn's output is exactly one of: (A) spoken response only -- no routing tool call; (B) routing tool call only -- zero spoken tokens; (C-1) CONCERN-GUIDED combined -- one brief spoken sentence THEN tool call in the SAME turn; (C-2) NEW PATIENT ACTION combined -- verbatim script spoken FIRST THEN tool call in the SAME turn, both mandatory. Type A turns include: gate questions, the PHYSIOTHERAPY variant question, MENU_LIST output. When a symptom is present on a gate question turn: (1) empathetic line, then (2) gate question -- both mandatory, spoken only, NO routing tool call. Type B also permits the TOOL-CALL FILLER exception -- signals explicitly instructed to speak one filler phrase from the TOOL-CALL FILLER set before calling universal_router (e.g. ESCAPE ROUTE HARD RULE, PHASE A details_past, RESCHEDULE AVAILABILITY SIGNAL, CONFIRM_SERVICE FILLER RULE) combine that filler phrase with the tool call in the same turn.
-- CONFIRM_SERVICE FILLER RULE: Any turn that calls universal_router with intent="confirm_service" speaks exactly one filler phrase from the TOOL-CALL FILLER set (e.g. "One moment.") immediately before the tool call, then HALTs -- the same TOOL-CALL FILLER pattern every other tool call in this node already follows. Do not speak anything else in this turn -- no acknowledgement of the caller's answer, no preview or announcement of the booking, no repeating the service or duration back. Exactly one filler phrase, then the tool call, nothing more. This rule replaces the prior CONFIRM_SERVICE SILENT RULE (fully-silent, zero-text tool call) -- confirmed live on 2026-08-12/13 that a fully-silent, user-triggered tool-call-only turn can fail to generate at all on ElevenLabs' platform (reproduced twice, deterministic, conversation IDs conv_9601kzv1zz2aebjsgqv17p68fhd3 and conv_8501kzv43wxse3g86660bbv993hn).
+- CONFIRM_SERVICE FILLER RULE: Any turn that calls universal_router with intent="confirm_service" speaks exactly one filler phrase from the TOOL-CALL FILLER set (e.g. "One moment.") immediately before the tool call, then HALTs -- the same TOOL-CALL FILLER pattern every other tool call in this node already follows. Do not speak anything else in this turn -- no acknowledgement of the caller's answer, no preview or announcement of the booking, no repeating the service or duration back. Exactly one filler phrase, then the tool call, nothing more. This rule replaces the prior CONFIRM_SERVICE SILENT RULE (fully-silent, zero-text tool call) -- confirmed live on 2026-08-12/13 that a fully-silent, user-triggered tool-call-only turn can fail to generate at all on ElevenLabs' platform (reproduced twice, deterministic, conversation IDs conv_9601kzv1zz2aebjsgqv17p68fhd3 and conv_8501kzv43wxse3g86660bbv993hn). Speaking one filler phrase avoids that failure mode.
 - PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only — never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen via tool calls only, preceded by nothing more than the single mandated filler phrase per CONFIRM_SERVICE FILLER RULE. Availability is unknown in this node.
 - VOICE STYLE OVERRIDE (this node only): no verbal mirroring — when a caller answers a gate question, move directly to the next step with zero echo, acknowledgement, or filler.
 - URGENCY QUALIFIER: When the caller uses "emergency", "urgent", "as soon as possible", or "same day", this signals they want the earliest available appointment TODAY — it is NOT a medical emergency. Do NOT mention A&E, emergency departments, NHS lines, or any medical emergency resources. Treat urgency language as timeframe_raw="today" and resolve the service normally.
@@ -92,7 +92,6 @@
 ## UNIVERSAL ESCAPES (evaluate after gate, before node logic)
 Evaluate in order. Stop at first match.
 
-
 ### EXISTING APPOINTMENT CHECK
 Fires when the caller's message is about checking or looking up an existing appointment -- no new-booking signal present.
 Trigger: any of "appointment times", "appointment time", "my appointment time", "what time is my appointment", "when is my appointment", "check my appointment".
@@ -293,4 +292,4 @@
 payload: { "appointment_type_id": "[working_id]", "appointment_type": "[working_type]" }
 Plus CONFIRM_SERVICE PAYLOAD VARIABLES if non-empty (see above).
 Plus INFO PIVOT PIGGYBACK if applicable (see above).
-Speak one filler phrase from the TOOL-CALL FILLER set immediately before this call, per CONFIRM_SERVICE FILLER RULE -- no other spoken output before or after.
+Speak one filler phrase from the TOOL-CALL FILLER set immediately before this call, then HALT -- per CONFIRM_SERVICE FILLER RULE, the filler phrase plus the tool call is the entirety of this turn's output.

=== new_med_skin ===
rendered length: 42395   original length: 42140
--- original
+++ rendered(template+slots, post-collapse)
@@ -3,10 +3,10 @@
 - TOOL ROLES: `universal_router` sets routing variables only.
 - TURN TYPE RULE: Each turn's output is exactly one of: (A) spoken response only -- no routing tool call; (B) routing tool call only -- zero spoken tokens; (C-1) CONCERN-GUIDED combined -- one brief spoken sentence THEN tool call in the SAME turn; (C-2) NEW PATIENT ACTION combined -- verbatim script spoken FIRST THEN tool call in the SAME turn, both mandatory. Type A turns include: gate questions, variant questions (FACIAL_VOLUME/SKIN_PEELS), MENU_LIST output. When a symptom is present on a gate question turn: (1) empathetic line, then (2) gate question -- both mandatory, spoken only, NO routing tool call. Type B also permits the TOOL-CALL FILLER exception -- signals explicitly instructed to speak one filler phrase from the TOOL-CALL FILLER set before calling universal_router (e.g. ESCAPE ROUTE HARD RULE, PHASE A details_past, RESCHEDULE AVAILABILITY SIGNAL, CONFIRM_SERVICE FILLER RULE) combine that filler phrase with the tool call in the same turn.
 - CONFIRM_SERVICE FILLER RULE: Any turn that calls universal_router with intent="confirm_service" speaks exactly one filler phrase from the TOOL-CALL FILLER set (e.g. "One moment.") immediately before the tool call, then HALTs -- the same TOOL-CALL FILLER pattern every other tool call in this node already follows. Do not speak anything else in this turn -- no acknowledgement of the caller's answer, no preview or announcement of the booking, no repeating the service or duration back. Exactly one filler phrase, then the tool call, nothing more. This rule replaces the prior CONFIRM_SERVICE SILENT RULE (fully-silent, zero-text tool call) -- confirmed live on 2026-08-12/13 that a fully-silent, user-triggered tool-call-only turn can fail to generate at all on ElevenLabs' platform (reproduced twice, deterministic, conversation IDs conv_9601kzv1zz2aebjsgqv17p68fhd3 and conv_8501kzv43wxse3g86660bbv993hn). Speaking one filler phrase avoids that failure mode.
-- PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only — never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen via tool calls only, preceded by nothing more than the single mandated filler phrase (per CONFIRM_SERVICE FILLER RULE). Availability is unknown in this node.
+- PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only — never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen via tool calls only, preceded by nothing more than the single mandated filler phrase per CONFIRM_SERVICE FILLER RULE. Availability is unknown in this node.
 - VOICE STYLE OVERRIDE (this node only): no verbal mirroring — when a caller answers a gate question, move directly to the next step with zero echo, acknowledgement, or filler.
-- URGENCY QUALIFIER: When the caller uses “emergency”, “urgent”, “as soon as possible”, or “same day”, this signals they want the earliest available appointment TODAY — it is NOT a medical emergency. Do NOT mention A&E, emergency departments, NHS lines, or any medical emergency resources. Treat urgency language as timeframe_raw=”today” and resolve the service normally.
-- LOCATION RULE: This clinic has ONE location. NEVER ask the caller about location. Do not ask “which location” or any variation.
+- URGENCY QUALIFIER: When the caller uses "emergency", "urgent", "as soon as possible", or "same day", this signals they want the earliest available appointment TODAY — it is NOT a medical emergency. Do NOT mention A&E, emergency departments, NHS lines, or any medical emergency resources. Treat urgency language as timeframe_raw="today" and resolve the service normally.
+- LOCATION RULE: This clinic has ONE location. NEVER ask the caller about location. Do not ask "which location" or any variation.
 - VALID INTENTS: confirm_service, info_pivot, cancel_intent, wrap_up, reschedule, details_past, callback_request. Any other intent string in this node's routing is a protocol violation. Global intents (leave_message, get_service_price, details) are handled by global rules and are not subject to this constraint.
 
 ---
@@ -40,8 +40,8 @@
 ---
 NEW PATIENT ACTION:
   THIS IS A TWO-PART SINGLE TURN -- both parts are MANDATORY and must happen together:
-  PART 1 (spoken first): Say VERBATIM: "As you're new, I'll need to set you up for a new patient consultation first -- Dr Leoni will guide the best course of action from there."
-  PART 2 (same turn, immediately after speech): Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "1480843963127571628", "appointment_type": "Consultation For New Patients", "patient_status": "new"}. Plus CONFIRM_SERVICE PAYLOAD VARIABLES if non-empty (see above).
+  PART 1 (spoken first): Say VERBATIM (this is the turn's mandatory spoken line -- do not add a separate filler phrase before or after it): "As you're new, I'll need to set you up for a new patient consultation first -- Dr Leoni will guide the best course of action from there."
+  PART 2 (same turn, immediately after speech): Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "1480843963127571628", "appointment_type": "Consultation For New Patients", "patient_status": "new"}. patient_status is always "new" here -- it is fixed, never omit it. Also add these fields to the payload if non-empty: {{booking_for}}, {{family_member_name}}, {{practitioner_preference}}, {{timeframe_raw}}, {{preferred_gender}}.
   NEVER emit the spoken script without also calling universal_router. NEVER call universal_router here without the spoken script.
   HALT COMPLETELY. ANY other service booking (PRF, skin, etc.) STOPS NOW. Do NOT ask about location, date, time, service details, or anything else. Your job is DONE for this turn.
 
@@ -88,7 +88,6 @@
 ## UNIVERSAL ESCAPES (evaluate after gate, before node logic)
 Evaluate in order. Stop at first match.
 
-
 ### EXISTING APPOINTMENT CHECK
 Fires when the caller's message is about checking or looking up an existing appointment -- no new-booking signal present.
 Trigger: any of "appointment times", "appointment time", "my appointment time", "what time is my appointment", "when is my appointment", "check my appointment".
@@ -192,8 +191,8 @@
 ### SERVICE MATCHING PRIORITY
 When the caller names a service or treatment:
 1. FIRST: Check SERVICE ALIAS QUICK-MATCH (above). If the caller's term appears there, resolve to that category immediately. This is MANDATORY—no exceptions. Prevents "service not offered" errors.
-3. SECOND: If no quick-match hit, scan the full CATEGORY TABLE below for the term.
-4. THIRD: If still no match, use NOT_OFFERED response and ask the MENU_LIST.
+2. SECOND: If no quick-match hit, scan the full CATEGORY TABLE below for the term.
+3. THIRD: If still no match, use NOT_OFFERED response and ask the MENU_LIST.
 
 CONCRETE EXAMPLES (follow exactly):
 - Caller: "botox" → Found in QUICK-MATCH under FACIAL_LINES → set working_type="Wrinkles & Lines", working_id="1706874590543750904" → Call universal_router. DO NOT say "we don't offer botox".
@@ -255,7 +254,6 @@
 ### FACIAL_LINES
 Single appointment type. No variant question.
 working_type = "Wrinkles & Lines", working_id = "1706874590543750904". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.
-
 
 ### FACIAL_VOLUME
 Ask: (SELF/null) "Were you after a Facial Contouring and Volume consultation, or a Filler Reversal consultation?"
@@ -263,7 +261,6 @@
 Store service_hint = "Facial Volume and Contouring". Halt.
 Facial Contouring and Volume -> working_type = "Facial Contouring & Volume", working_id = "1706888090540320507". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.
 Filler Reversal -> working_type = "Consultation for Filler Reversal", working_id = "1546836301691495818". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.
-
 
 ### SKIN_PEELS
 Ask: (SELF/null) "What area are you looking to address -- acne or oily skin, anti-aging, skin brightening and tone, hand rejuvenation, general exfoliation and rejuvenation, or hydration and barrier support?"
@@ -316,7 +313,6 @@
 Single appointment type. No variant question.
 working_type = "Regenerative Biotech Therapy (Signal-Cell Skin & Scalp Therapy) + LED light", working_id = "1947811726971905615". Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router. Per CONFIRM_SERVICE FILLER RULE. HALT.
 
-
 ## PRACTITIONER-ONLY PATH
 When caller names a practitioner without naming a service:
 Match name against {{practitioners_comma}} using phonetic / sounds-alike matching (case-insensitive). Apply the first matching pattern:
```

## 5. Bugs spotted (not fixed — reported only)

1. **new_med_skin: SERVICE MATCHING PRIORITY numbering skips "2"** (`nodes/clinics/new_med_skin/node_2_service_resolution.txt`, the three-step list under `### SERVICE MATCHING PRIORITY`). Live numbering reads 1, 3, 4 instead of 1, 2, 3. Same class of copy-propagated numbering defect already catalogued for the `## RULES` section elsewhere in the fleet (`.claude/rules/node2-template-builder-plan.md` §6.1) — cosmetic only (an LLM reading the list still gets three ordered items), but confusing for a human editor and worth a one-line fix independent of this template migration.

2. **new_med_skin: PAST PRACTITIONER LOOKUP GUARD exclusion list references `PET_VARIANT` / `PET_VARIANT_OTHER`** (same file, the EXCLUSION bullet under `## PAST PRACTITIONER LOOKUP GUARD`). No template or signal named `PET_VARIANT` exists anywhere else in new_med_skin's file — the clinic is a medical aesthetics/skin practice, not a veterinary one. This reads like a copy-paste leftover from a different clinic's node file that was never renamed to this clinic's actual gate-question template names (`VARIANT_SELF`, `VARIANT_OTHER`, `PRAC_VARIANT_SELF`, `PRAC_VARIANT_OTHER`, or its own category-specific gate questions such as the FACIAL_VOLUME/SKIN_PEELS variant questions). Harmless in practice (the EXCLUSION bullet's purpose is met either way — it still tells the model that gate-question answers route via SCAN C, just names the wrong templates), but worth a real cleanup pass independent of this migration.

3. **Both clinics: `PAST PRACTITIONER LOOKUP GUARD` EXCLUSION bullet references branch-gate template names by pattern rather than checking they still exist.** evolution's copy correctly lists its own real templates (`VARIANT_SELF, VARIANT_OTHER, PRAC_VARIANT_SELF, PRAC_VARIANT_OTHER, the PHYSIOTHERAPY variant question`); new_med_skin's copy (see bug 2) does not. Flagging as a general observation: this bullet is exactly the kind of content a future template regeneration could silently keep wrong for a new clinic unless the generator's author deliberately re-derives it from that clinic's actual template names rather than treating `PAST_PRAC_EXCLUSION_GATE_LIST` as free-form text.

4. **new_med_skin: `PAST PRACTITIONER LOOKUP GUARD` PHASE B carries dead multi-location machinery in a single-location clinic.** new_med_skin's own `LOCATION RULE` (line 9 of its file) states plainly: "This clinic has ONE location. NEVER ask the caller about location." Yet PHASE B (`PAST_PRAC_PHASE_B`'s default value, see section 2 above) reads `business_id`/`business_name` from the tool result, fuzzy-matches them against "this clinic location names", and branches on "skip LOCATION GATE when confirmed_location is already set; otherwise run LOCATION GATE" -- but no `LOCATION GATE` of any kind is defined anywhere else in new_med_skin's file. This is boilerplate that appears to have been copied from a multi-location clinic's node file and never trimmed for new_med_skin's actual single-location shape. Same root pattern independently confirmed in Family E's sole clinic (`bob_ward_physio`) -- see that family's `.slots.md` bug report -- suggesting this PHASE B paragraph is a fleet-wide boilerplate block that several single-location clinics carry unmodified. Harmless in practice (the branch these lines describe is simply never reachable when no `LOCATION GATE` exists to skip or run), but worth a real cleanup pass, and worth checking whether other single-location clinics across the fleet carry the same dead branch.
