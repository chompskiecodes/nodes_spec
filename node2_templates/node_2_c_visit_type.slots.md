# Slot Reference -- `node_2_c_visit_type.txt` (Family C / VISIT_TYPE)

## Base clinic

**Base: `shire_osteopath`.**

Chosen over `cath_lilburn` and `northern_physio` because it carries zero clinic-only structural extras of its own. `cath_lilburn` has two sections that exist nowhere else in Family C (`TEMPLATE VARIANT RESOLUTION -- SILENT RULE`, and an extra `BOOKING_FOR` line in `MINI-FRAMEWORK`) plus a third dimension (Zoom vs in-person, and an initial-cancer sub-branch) that `shire`/`northern` don't share. `northern_physio` is the explicitly-named outlier (task brief) -- it carries a ~70-line location subsystem (`LOCATION GATE`/`PENDING SERVICE KEY TABLE`/`LOCATION RESOLUTION`/`SERVICE-LOCATION RESTRICTIONS`) plus a practitioner-matching subsystem (`PRACTITIONER-ONLY PATH`/`PRACTITIONER-SERVICE VALIDATION`) that neither other clinic has, and a structurally much larger `PRIMARY FLOW`/`SERVICE BRANCHES` (billing-type resolution across 4 service branches vs. shire's 2). `shire_osteopath`'s INITIAL/SUBSEQUENT + duration + concession shape is the leanest, most representative 'trunk' -- every section either matches cath/northern directly or needs only a value-level slot, never a whole inserted section of shire's own that the others lack. The template is built by taking shire's exact body text and (a) replacing every differing span with a `<<SLOT>>` token, and (b) inserting optional, default-empty slots at the correct structural position for the sections cath and northern each carry that shire does not.

## Slot table

**34 slots** remain as `<<SLOT>>` tokens in the template (12 optional whole-section/whole-line
blocks defaulting to `''`, 22 non-optional slots with a non-empty fleet default). A 35th
differing span (RULES item 3) was fully normalised to literal boilerplate rather than kept as a
slot -- see NORMALISED DRIFT below -- so it does not appear in this table at all; its
before/after text is documented there instead. "Optional" = whole section present in only 1 or 2
of the 3 clinics, default `''`. Where a clinic's exact value equals the default (no override was
needed), the table still shows it explicitly per the task spec ("exact value for each of the 3
clinics") -- it is simply reproduced from the `default` row.

### `MF_BOOKING_FOR_LINE`

Optional extra MINI-FRAMEWORK line pre-declaring {{booking_for}} default + repeating the ABSOLUTE BAN. Present in cath only.  *(optional -- default empty string)*

**Default:** *(empty)*

**cath:** ```
- BOOKING_FOR: {{booking_for}} is pre-set (default "self"). Read it silently to choose (self)/(other) template variants. ABSOLUTE BAN: Never ask "Is this for yourself or someone else?", "Are you booking for yourself?", or any booking_for question — ever. booking_for is detected only from explicit third-party language the caller volunteers.
```

**shire:** *(empty)*

**northern:** *(empty)*

### `TYPE_A_TURNS_LIST`

TURN TYPE RULE's list of that clinic's own spoken-only (Type A) gate questions.

**Default:** ```
have-you-been-before question, subsequent-duration question, NOT_OFFERED question
```

**cath:** ```
initial-vs-followup question, in-person-vs-zoom question, cancer-vs-general question, follow-up duration question, NOT_OFFERED question
```

**shire:** ```
have-you-been-before question, subsequent-duration question, NOT_OFFERED question
```

**northern:** ```
billing question, private service question, pelvic floor qualifier question, location question, Epping disambiguation question, email escalation offer/name/confirm steps
```

### `TURN_TYPE_RULE_TYPE_B_TAIL`

TURN TYPE RULE's Type-B filler-exception clause, incl. that clinic's own example signal names.

**Default:** ```
These MUST NEVER include a universal_router call. Type B also permits the TOOL-CALL FILLER exception — signals explicitly instructed to speak one filler phrase from the TOOL-CALL FILLER set before calling universal_router (e.g. ESCAPE ROUTE HARD RULE, CONFIRM_SERVICE FILLER RULE) combine that filler phrase with the tool call in the same turn.
```

**cath:** ```
These MUST NEVER include a universal_router call. Type B also permits the TOOL-CALL FILLER exception — signals explicitly instructed to speak one filler phrase from the TOOL-CALL FILLER set before calling universal_router combine that filler phrase with the tool call in the same turn, including CONFIRM_SERVICE FILLER RULE.
```

**shire:** ```
These MUST NEVER include a universal_router call. Type B also permits the TOOL-CALL FILLER exception — signals explicitly instructed to speak one filler phrase from the TOOL-CALL FILLER set before calling universal_router (e.g. ESCAPE ROUTE HARD RULE, CONFIRM_SERVICE FILLER RULE) combine that filler phrase with the tool call in the same turn.
```

**northern:** ```
These MUST NEVER include a universal_router call. Type B also permits the TOOL-CALL FILLER exception -- signals explicitly instructed to speak one filler phrase from the TOOL-CALL FILLER set before calling universal_router (e.g. ESCAPE ROUTE HARD RULE, PHASE A details_past, RESCHEDULE AVAILABILITY SIGNAL, CONFIRM_SERVICE FILLER RULE) combine that filler phrase with the tool call in the same turn.
```

### `MF_CSFR_EXTRA_SENTENCE`

Optional trailing sentence appended to the CONFIRM_SERVICE FILLER RULE line. Present in northern only.  *(optional -- default empty string)*

**Default:** *(empty)*

**cath:** *(empty)*

**shire:** *(empty)*

**northern:** ```
 Speaking one filler phrase avoids that failure mode.
```

### `MF_PRE_ROUTING_SILENCE_LINE`

Whole PRE-ROUTING SILENCE line in MINI-FRAMEWORK.

**Default:** ```
- PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only — never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen via tool calls, preceded by nothing more than the single mandated filler phrase (per CONFIRM_SERVICE FILLER RULE). Availability is unknown in this node.
```

**cath:** ```
- PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only — never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen silently via tool calls. Availability is unknown in this node.
```

**shire:** ```
- PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only — never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen via tool calls, preceded by nothing more than the single mandated filler phrase (per CONFIRM_SERVICE FILLER RULE). Availability is unknown in this node.
```

**northern:** *(= default, no override)* ```
- PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only — never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen via tool calls, preceded by nothing more than the single mandated filler phrase (per CONFIRM_SERVICE FILLER RULE). Availability is unknown in this node.
```

### `MF_CONFIRM_SERVICE_PAYLOAD_LINE`

Whole CONFIRM_SERVICE PAYLOAD MUST-INCLUDE line (field list + LOCATION RULE differs per clinic).

**Default:** ```
- CONFIRM_SERVICE PAYLOAD MUST-INCLUDE (absolute): Every confirm_service payload MUST contain: appointment_type_id, appointment_type, booking_for (always — default "self"; use "other" if booking_for="other" was established at ANY point in the conversation). Also include variant_type, patient_status ("new" for initial appointments, "existing" for subsequent appointments), timeframe_raw, practitioner_preference, preferred_gender, caller_complaint, family_member_name if any of these were mentioned, family_member_phone if booking_for="other" and the caller stated a phone number for the third party — never ask for it. Never drop booking_for="other" across gate or variant turns.
```

**cath:** ```
- CONFIRM_SERVICE PAYLOAD MUST-INCLUDE (absolute): Every confirm_service payload MUST contain: appointment_type_id, appointment_type, booking_for (always — default "self"; use "other" if booking_for="other" was established at ANY point in the conversation). LOCATION RULE: for IN-PERSON services (variant_type is initial_inperson, initial_cancer, followup_45, or followup_60), include business_name="Catherine Lilburn" and business_id="CL-358054". For ZOOM services (variant_type is initial_zoom or followup_zoom), omit both business_name and business_id entirely. Also include variant_type, patient_status="any" (all services), timeframe_raw, practitioner_preference, preferred_gender, caller_complaint, family_member_name if any of these were mentioned, family_member_phone if booking_for="other" and the caller stated a phone number for the third party — never ask for it. Never drop booking_for="other" across gate or variant turns.
```

**shire:** ```
- CONFIRM_SERVICE PAYLOAD MUST-INCLUDE (absolute): Every confirm_service payload MUST contain: appointment_type_id, appointment_type, booking_for (always — default "self"; use "other" if booking_for="other" was established at ANY point in the conversation). Also include variant_type, patient_status ("new" for initial appointments, "existing" for subsequent appointments), timeframe_raw, practitioner_preference, preferred_gender, caller_complaint, family_member_name if any of these were mentioned, family_member_phone if booking_for="other" and the caller stated a phone number for the third party — never ask for it. Never drop booking_for="other" across gate or variant turns.
```

**northern:** ```
- CONFIRM_SERVICE PAYLOAD MUST-INCLUDE (absolute): Every confirm_service payload MUST contain: appointment_type_id, appointment_type, booking_for (always — default "self"; use "other" if booking_for="other" was established at ANY point in the conversation), business_name, business_id. Also include variant_type, patient_status, practitioner_preference, timeframe_raw, preferred_gender, caller_complaint, family_member_name if any of these were mentioned, family_member_phone if booking_for="other" and the caller stated a phone number for the third party — never ask for it. Never drop booking_for="other" across gate or variant turns.
```

### `MF_URGENCY_QUALIFIER_LINE`

Whole URGENCY QUALIFIER line (northern adds an NHS-lines mention).

**Default:** ```
- URGENCY QUALIFIER: When the caller uses "emergency", "urgent", "as soon as possible", or "same day", this signals they want the earliest available appointment TODAY — it is NOT a medical emergency. Do NOT mention A&E, emergency departments, or any medical emergency resources. Treat urgency language as timeframe_raw="today" and resolve the service normally.
```

**cath:** ```
- URGENCY QUALIFIER: When the caller uses "emergency", "urgent", "as soon as possible", or "same day", this signals they want the earliest available appointment TODAY — it is NOT a medical emergency. Do NOT mention A&E, emergency departments, or any medical emergency resources. Treat urgency language as timeframe_raw="today" and resolve the service normally.
```

**shire:** ```
- URGENCY QUALIFIER: When the caller uses "emergency", "urgent", "as soon as possible", or "same day", this signals they want the earliest available appointment TODAY — it is NOT a medical emergency. Do NOT mention A&E, emergency departments, or any medical emergency resources. Treat urgency language as timeframe_raw="today" and resolve the service normally.
```

**northern:** ```
- URGENCY QUALIFIER: When the caller uses "emergency", "urgent", "as soon as possible", or "same day", this signals they want the earliest available appointment TODAY — it is NOT a medical emergency. Do NOT mention A&E, emergency departments, NHS lines, or any medical emergency resources. Treat urgency language as timeframe_raw="today" and resolve the service normally.
```

### `NO_REASONING_BAN_TAIL`

NO-REASONING BAN sentence tail -- northern's is a materially different two-case rule (location-gate aware).

**Default:** ```
Service classification is an internal routing decision only — stating it aloud is a protocol violation. Speak one filler phrase from the TOOL-CALL FILLER set, then call confirm_service, per CONFIRM_SERVICE FILLER RULE.
```

**cath:** ```
Service classification is an internal routing decision only — stating it aloud is a protocol violation. Speak one filler phrase from the TOOL-CALL FILLER set, then call confirm_service, per CONFIRM_SERVICE FILLER RULE.
```

**shire:** ```
Service classification is an internal routing decision only — stating it aloud is a protocol violation. Speak one filler phrase from the TOOL-CALL FILLER set, then call confirm_service, per CONFIRM_SERVICE FILLER RULE.
```

**northern:** ```
Never say "That's an EPC appointment", "So you're claiming through a care plan", "That means Medicare", "That's a [service name] appointment", or any equivalent. Service classification is an internal routing decision only — stating it aloud is a protocol violation. Two cases: (a) confirmed_location is set → speak one filler phrase from the TOOL-CALL FILLER set (not "Got it."), then call confirm_service, per CONFIRM_SERVICE FILLER RULE; (b) confirmed_location not set → ask LOCATION_QUESTION in a single spoken turn, preceded by at most "Got it." (one word) and nothing else.
```

### `BS_PATIENT_STATUS_BULLET`

Optional patient_status detection bullet in BLOCKING SIGNALS. Present in shire only.  *(optional -- default empty string)*

**Default:** *(empty)*

**cath:** *(empty)*

**shire:** ```
- patient_status: "first time"/"never been"/"I've never been"/"I'm new"/"new"/"new patient"/"initial" -> "new" | "been before"/"returning"/"I've been"/"returning patient" -> "existing"
```

**northern:** *(empty)*

### `TIME_ONLY_GUARD_LINE`

Whole TIME-ONLY GUARD line.

**Default:** ```
TIME-ONLY GUARD: When the caller's message contains a time or date reference ("two o'clock", "today", "tomorrow", "three PM", etc.) but NO service term, this is NOT an availability check — it is a timing preference. Capture it as timeframe_raw silently. Do NOT call universal_router. Proceed to CATEGORY RESOLUTION and treat as no-service-term — ask the gate question. ZERO tool calls this turn.
```

**cath:** ```
TIME-ONLY GUARD: When the caller's message contains a time or date reference ("two o'clock", "today", "tomorrow", "three PM", etc.) but NO service term, this is NOT an availability check — it is a timing preference. Capture it as timeframe_raw silently. Do NOT call universal_router. Proceed to CATEGORY RESOLUTION and treat as no-service-term — ask the gate question. ZERO tool calls this turn.
```

**shire:** ```
TIME-ONLY GUARD: When the caller's message contains a time or date reference ("two o'clock", "today", "tomorrow", "three PM", etc.) but NO service term, this is NOT an availability check — it is a timing preference. Capture it as timeframe_raw silently. Do NOT call universal_router. Proceed to CATEGORY RESOLUTION and treat as no-service-term — ask the gate question. ZERO tool calls this turn.
```

**northern:** ```
TIME-ONLY GUARD: When the caller's message contains a time or date reference ("two o'clock", "today", "tomorrow", "three PM", etc.) but NO service term, this is NOT an availability check – it is a timing preference. Capture it as timeframe_raw silently. Do NOT call universal_router. Proceed to CATEGORY RESOLUTION and treat as no-service-term – ask the gate question or MENU_LIST. ZERO tool calls this turn.
```

### `PPLG_EXCLUSION_BULLET2`

PAST PRACTITIONER LOOKUP GUARD's EXCLUSION bullet 2 (branch gate question names).

**Default:** ```
- Any "yes"/"no" answer to a branch gate question (have-you-been-before question, subsequent-duration question) — those answers route via SCAN C.
```

**cath:** ```
- Any "yes"/"no" answer to a branch gate question (initial-vs-followup, in-person-vs-zoom, cancer-vs-general, duration question) — those answers route via SCAN C.
```

**shire:** ```
- Any "yes"/"no" answer to a branch gate question (have-you-been-before question, subsequent-duration question) — those answers route via SCAN C.
```

**northern:** ```
- Any "yes"/"no" answer to a branch gate question (VARIANT_SELF, VARIANT_OTHER, PET_VARIANT, PET_VARIANT_OTHER, duration question, sub-type question, programme question) — those answers route via SCAN C.
```

### `PPLG_PHASE_B_LINE`

PAST PRACTITIONER LOOKUP GUARD PHASE B (lookup-response handling) paragraph.

**Default:** ```
PHASE B — LOOKUP RESPONSE (evaluate first): the entry immediately preceding this agent turn is a details_past tool result AND the caller has not spoken since. If multiple_past_appointments is true: speak the message field verbatim, HALT, and wait for the caller to pick by number or date/time; on the next turn re-call details_past with appointment_date and appointment_time from the matching past_appointments entry. Otherwise read appointment_type, appointment_type_id, variant_type from the response. Store all working context silently. If appointment_type_id is present and not "none", enter the matching service branch for that appointment type. If only practitioner is resolved and service is still unknown, speak one brief line and ask whether it's an initial or follow-up appointment. HALT when a spoken question was required.
```

**cath:** ```
PHASE B — LOOKUP RESPONSE (evaluate first): the entry immediately preceding this agent turn is a details_past tool result AND the caller has not spoken since. If multiple_past_appointments is true: speak the message field verbatim, HALT, and wait for the caller to pick by number or date/time; on the next turn re-call details_past with appointment_date and appointment_time from the matching past_appointments entry. Otherwise read appointment_type, appointment_type_id, variant_type from the response. Store all working context silently. If appointment_type_id is present and not "none", enter the matching service branch for that appointment type (the single location Catherine Lilburn applies automatically for in-person; zoom services have no business_id). If only practitioner is resolved and service is still unknown, speak one brief line and ask whether it's an initial or follow-up appointment. HALT when a spoken question was required.
```

**shire:** ```
PHASE B — LOOKUP RESPONSE (evaluate first): the entry immediately preceding this agent turn is a details_past tool result AND the caller has not spoken since. If multiple_past_appointments is true: speak the message field verbatim, HALT, and wait for the caller to pick by number or date/time; on the next turn re-call details_past with appointment_date and appointment_time from the matching past_appointments entry. Otherwise read appointment_type, appointment_type_id, variant_type from the response. Store all working context silently. If appointment_type_id is present and not "none", enter the matching service branch for that appointment type. If only practitioner is resolved and service is still unknown, speak one brief line and ask whether it's an initial or follow-up appointment. HALT when a spoken question was required.
```

**northern:** ```
PHASE B — LOOKUP RESPONSE (evaluate first): the entry immediately preceding this agent turn is a details_past tool result AND the caller has not spoken since. If multiple_past_appointments is true: speak the message field verbatim, HALT, and wait for the caller to pick by number or date/time; on the next turn re-call details_past with appointment_date and appointment_time from the matching past_appointments entry. Otherwise read practitioner_preference, practitioner_id, appointment_type, appointment_type_id, business_id, and business_name from the response. When business_id is present, set confirmed_business_id = business_id and confirmed_location from business_name (fuzzy-match against this clinic location names). Store all other working context silently. If appointment_type_id is present and not "none", enter the matching service/category branch for that appointment type (skip LOCATION GATE when confirmed_location is already set; otherwise run LOCATION GATE or gate questions as this clinic requires). If only practitioner is resolved and service is still unknown, speak one brief line naming the practitioner and ask which service — use this clinic's service menu. HALT when a spoken question was required.
```

### `CONCERN_SYMPTOM_EXAMPLES`

CONCERN-GUIDED RESOLUTION RULE's symptom example list, clinic-appropriate.

**Default:** ```
(e.g. "fatigue", "digestive issues", "hormonal concerns")
```

**cath:** ```
(e.g. "fatigue", "digestive issues", "hormonal concerns")
```

**shire:** ```
(e.g. "fatigue", "digestive issues", "hormonal concerns")
```

**northern:** ```
(e.g. "back pain", "knee problem", "shoulder injury")
```

### `CONCERN_MANDATORY_QUESTION_LIST`

CONCERN-GUIDED RESOLUTION RULE's list of that clinic's mandatory first questions.

**Default:** ```
(have-you-been-before question, subsequent-duration question)
```

**cath:** ```
(initial-vs-followup, in-person-vs-zoom, cancer-vs-general)
```

**shire:** ```
(have-you-been-before question, subsequent-duration question)
```

**northern:** ```
(billing question, pelvic qualifier, location question)
```

### `RULES_ABSOLUTE_BAN_BLOCK`

RULES item 7 onward (ABSOLUTE BAN + any clinic-specific extra numbered rules).

**Default:** ```
7. ABSOLUTE BAN: Never ask "Is that for yourself or someone else?", "Are you booking for yourself?", or any variant. booking_for is detected passively from explicit third-party language only — never ask the caller to confirm it. If the caller says "for [name]" without a relationship word ("my wife", "my son", "a friend"), treat as self-booking and proceed directly to STEP 1.
```

**cath:** ```
7. ABSOLUTE BAN: Never ask "Is that for yourself or someone else?", "Are you booking for yourself?", or any variant. booking_for is detected passively from explicit third-party language only — never ask the caller to confirm it. If the caller says "for [name]" without a relationship word ("my wife", "my son", "a friend"), treat as self-booking and proceed directly to STEP 1.
```

**shire:** ```
7. ABSOLUTE BAN: Never ask "Is that for yourself or someone else?", "Are you booking for yourself?", or any variant. booking_for is detected passively from explicit third-party language only — never ask the caller to confirm it. If the caller says "for [name]" without a relationship word ("my wife", "my son", "a friend"), treat as self-booking and proceed directly to STEP 1.
```

**northern:** ```
7. IMPORTANT: This clinic has NO initial/new-patient appointment type for Physiotherapy. Never ask the caller if they are new or existing for a physio booking. The billing question replaces that distinction entirely.
8. Appointment type names in spoken output: say "Physiotherapy" (not "Physiotherapy Standard Appointment"), say "Exercise Physiology" (not "Exercise Phy Appointment"). Pelvic Floor F/U means follow-up.
9. ABSOLUTE BAN: Never ask "Is that for yourself or someone else?", "Are you booking for yourself?", or any variant. booking_for is detected passively from explicit third-party language only — never ask the caller to confirm it. If the caller says "for [name]" without a relationship word ("my wife", "my son", "a friend"), treat as self-booking and proceed directly to STEP 2.
```

### `RESCHEDULE_REENTRY_TAIL`

RESCHEDULE RE-ENTRY GUARD's final field name ('variant_type' or 'location').

**Default:** ```
variant_type
```

**cath:** ```
variant_type
```

**shire:** ```
variant_type
```

**northern:** ```
location
```

### `INFO_PIVOT_RETURN_LINE`

INFO PIVOT RETURN GUARD's confirm_service re-entry bullet (payload shape differs per clinic).

**Default:** ```
- If {{appointment_type_id}} != "none": CHECKPOINT — scan full conversation history for timeframe_raw. Speak one filler phrase from the TOOL-CALL FILLER set, per CONFIRM_SERVICE FILLER RULE, then call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "{{appointment_type_id}}", "appointment_type": "{{appointment_type}}", "variant_type": "{{variant_type}}", "patient_status": "{{patient_status}}", "info_pivot_source": "node_8"} [+ CONTEXT PIGGYBACK]. HALT.
```

**cath:** ```
- If {{appointment_type_id}} != "none": CHECKPOINT — scan full conversation history for timeframe_raw. Apply LOCATION RULE from CONFIRM_SERVICE PAYLOAD MUST-INCLUDE (include business fields only for in-person variant_types). CONFIRM_SERVICE FILLER RULE applies (speak one filler phrase from the TOOL-CALL FILLER set, then the tool call). Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "{{appointment_type_id}}", "appointment_type": "{{appointment_type}}", "variant_type": "{{variant_type}}", "patient_status": "any", [business_name/business_id if in-person per LOCATION RULE], "info_pivot_source": "node_8"} [+ CONTEXT PIGGYBACK]. HALT.
```

**shire:** ```
- If {{appointment_type_id}} != "none": CHECKPOINT — scan full conversation history for timeframe_raw. Speak one filler phrase from the TOOL-CALL FILLER set, per CONFIRM_SERVICE FILLER RULE, then call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "{{appointment_type_id}}", "appointment_type": "{{appointment_type}}", "variant_type": "{{variant_type}}", "patient_status": "{{patient_status}}", "info_pivot_source": "node_8"} [+ CONTEXT PIGGYBACK]. HALT.
```

**northern:** ```
- If {{appointment_type_id}} != "none": Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type_id": "{{appointment_type_id}}", "appointment_type": "{{appointment_type}}", "variant_type": "{{variant_type}}", "business_name": "{{confirmed_location}}", "business_id": "{{confirmed_business_id}}", "info_pivot_source": "node_8"}. Per CONFIRM_SERVICE FILLER RULE. HALT.
```

### `CSFR_CRITICAL_CHECKPOINT_BLOCK`

Optional whole CONFIRM_SERVICE FILLER RULE -- CRITICAL CHECKPOINT section. Present in cath+shire, absent northern.  *(optional -- default empty string)*

**Default:** ```
## CONFIRM_SERVICE FILLER RULE — CRITICAL CHECKPOINT
BEFORE every confirm_service call: speak exactly one filler phrase from the TOOL-CALL FILLER set (e.g. "One moment.") immediately before the tool call, then HALT — per CONFIRM_SERVICE FILLER RULE. Do not speak anything else before or after the tool call — no preamble, no acknowledgement, no preview or announcement of the booking. Exactly one filler phrase, then the tool call, nothing more.
```

**cath:** ```
## CONFIRM_SERVICE FILLER RULE — CRITICAL CHECKPOINT
BEFORE every confirm_service call: speak exactly one filler phrase from the TOOL-CALL FILLER set (e.g. "One moment.") immediately before the tool call, per CONFIRM_SERVICE FILLER RULE. Do not speak anything else in this turn — no acknowledgement of the caller's answer, no preview or announcement of the booking, no repeating the service or duration back. Exactly one filler phrase, then the tool call, nothing more.
```

**shire:** ```
## CONFIRM_SERVICE FILLER RULE — CRITICAL CHECKPOINT
BEFORE every confirm_service call: speak exactly one filler phrase from the TOOL-CALL FILLER set (e.g. "One moment.") immediately before the tool call, then HALT — per CONFIRM_SERVICE FILLER RULE. Do not speak anything else before or after the tool call — no preamble, no acknowledgement, no preview or announcement of the booking. Exactly one filler phrase, then the tool call, nothing more.
```

**northern:** *(empty)*

### `TIMEFRAME_RAW_CHECKPOINT_BLOCK`

Optional whole TIMEFRAME_RAW SURVIVAL CHECKPOINT section. Present in cath+shire (identical), absent northern.  *(optional -- default empty string)*

**Default:** ```
## TIMEFRAME_RAW SURVIVAL CHECKPOINT — MANDATORY BEFORE EVERY CONFIRM_SERVICE
Scan the FULL conversation history — if a time or date was mentioned at ANY point (5+ turns ago is included), it MUST appear as timeframe_raw in the payload. Omitting it when it was mentioned is a protocol violation. Do NOT rely only on the current or most recent turn.

---
```

**cath:** ```
## TIMEFRAME_RAW SURVIVAL CHECKPOINT — MANDATORY BEFORE EVERY CONFIRM_SERVICE
Scan the FULL conversation history — if a time or date was mentioned at ANY point (5+ turns ago is included), it MUST appear as timeframe_raw in the payload. Omitting it when it was mentioned is a protocol violation. Do NOT rely only on the current or most recent turn.

---
```

**shire:** ```
## TIMEFRAME_RAW SURVIVAL CHECKPOINT — MANDATORY BEFORE EVERY CONFIRM_SERVICE
Scan the FULL conversation history — if a time or date was mentioned at ANY point (5+ turns ago is included), it MUST appear as timeframe_raw in the payload. Omitting it when it was mentioned is a protocol violation. Do NOT rely only on the current or most recent turn.

---
```

**northern:** *(empty)*

### `CONFIRM_SERVICE_PAYLOAD_SHAPE_LINE`

CONFIRM_SERVICE CALL FORMAT's payload shape line (field list differs per clinic).

**Default:** ```
- payload: { "appointment_type": "[service name]", "appointment_type_id": "[numeric ID as string]", "variant_type": "[working_variant_type]", "patient_status": "[new|existing]", "info_pivot_source": "node_8" (only when returning from info pivot) }
```

**cath:** ```
- payload: { "appointment_type": "[Halaxy name]", "appointment_type_id": "[numeric ID as string]", "variant_type": "[working_variant_type]", "patient_status": "any", [business_name/business_id for in-person only — see LOCATION RULE], "info_pivot_source": "node_8" (only when returning from info pivot) }
```

**shire:** ```
- payload: { "appointment_type": "[service name]", "appointment_type_id": "[numeric ID as string]", "variant_type": "[working_variant_type]", "patient_status": "[new|existing]", "info_pivot_source": "node_8" (only when returning from info pivot) }
```

**northern:** ```
- payload: { "appointment_type": "[Cliniko name]", "appointment_type_id": "[working_id]", "variant_type": "[working_variant_type]" (if set), "patient_status": "[working_patient_status]" (if set — Pelvic Floor only), "business_name": "[confirmed_location]" (if set), "business_id": "[confirmed_business_id]" (if set), "info_pivot_source": "node_8" (only when returning from info pivot) }
```

### `CATEGORY_TABLE_BLOCK`

Optional whole CATEGORY TABLE section (appointment ID/duration/price/variant reference table). Present in cath+shire (both differ -- pure per-clinic data), absent northern.  *(optional -- default empty string)*

**Default:** *(empty)*

**cath:** ```
## CATEGORY TABLE
| Working ID | Service | Duration | Price | Variant |
|------------|---------|----------|-------|---------|
| 599759 | Initial appointment (in-person) | 75 min | $195 | initial_inperson |
| 599761 | Initial consultation - Cancer (in-person) | 90 min | $250 | initial_cancer |
| 599791 | Initial - Zoom appt | 75 min | $195 | initial_zoom |
| 599765 | Follow up - 45 mins (in-person) | 45 min | $100 | followup_45 |
| 599763 | Follow up - 60 mins (in-person) | 60 min | $125 | followup_60 |
| 599789 | Follow up - Zoom | 60 min | $125 | followup_zoom |

---
```

**shire:** ```
## CATEGORY TABLE
| Working ID | Service | Duration | Variant |
|------------|---------|----------|---------|
| 1592289604805862909 | Initial Appointment 60 min - standard | 60min | initial_standard |
| 1592303777140975108 | Initial Appointment 60 min - concession | 60min | initial_concession |
| 1592289604235437564 | Subsequent Appointment 40 min - standard | 45min | subsequent_standard |
| 1592305287727949317 | Subsequent Appointment 40 min- concession | 45min | subsequent_concession |
| 1729472131701417513 | Subsequent appointment 60 min - extended | 60min | subsequent_extended |
| Caller unsure | ask VARIANT_SELF. HALT. |

---
```

**northern:** *(empty)*

### `TEMPLATES_BODY`

The spoken question/NOT_OFFERED template phrasings body (between the ## TEMPLATES heading and URGENCY STRIP). 100% per-clinic content.

**Default:** *(empty)*

**cath:** ```
INITIAL_OR_FOLLOWUP (self):  "Is this your first visit with Catherine, or a follow-up?"
INITIAL_OR_FOLLOWUP (other): "Is this their first visit with Catherine, or a follow-up?"
INPERSON_OR_ZOOM (self):     "Are you looking for an in-person appointment, or would Zoom work for you?"
INPERSON_OR_ZOOM (other):    "Are they looking for an in-person appointment, or would Zoom work for them?"
CANCER_OR_GENERAL (self):    "Is this a general initial consultation, or focused on cancer support?"
CANCER_OR_GENERAL (other):   "Is this a general initial consultation for them, or focused on cancer support?"
FOLLOWUP_DURATION (self):    "Are you after a 45-minute or 60-minute appointment?"
FOLLOWUP_DURATION (other):   "Are they after a 45-minute or 60-minute appointment?"
NOT_OFFERED (first):  "I don't think we have [term] here — Catherine offers naturopathy consultations, both in-person and via Zoom. Would you like one of those?"
NOT_OFFERED (second): "We don't have [term] either. Did you want to book one of Catherine's consultations?"
```

**shire:** ```
CONCESSION_QUESTION (self):  "Are you booking at the standard rate, or do you have a concession card?"
CONCESSION_QUESTION (other): "Are they booking at the standard rate, or do they have a concession card?"
SUBSEQUENT_DURATION (self):  "Are you after a standard 45-minute appointment, or an extended 60-minute one?"
SUBSEQUENT_DURATION (other): "Are they after a standard 45-minute appointment, or an extended 60-minute one?"
NOT_OFFERED (first):  "We don't offer [term] here — we offer osteopathy. Have you been to Shire Osteopath before?"
NOT_OFFERED (second): "We don't have [term] here either — did osteopathy sound like it might help?"
VARIANT_SELF:  "Have you been to Shire Osteopath before?"
VARIANT_OTHER: "Have they been to Shire Osteopath before?"
```

**northern:** ```
BILLING_QUESTION (self):  "Are you making a private booking, or claiming through an insurance or health fund provider?"
BILLING_QUESTION (other): "Will they be making a private booking, or claiming through an insurance or health fund provider?"
PRIVATE_SERVICE_QUESTION (self):  "Are you looking to book Physiotherapy, Exercise Physiology, a Pelvic Floor appointment, or a Health Assessment?"
PRIVATE_SERVICE_QUESTION (other): "Are they looking to book Physiotherapy, Exercise Physiology, a Pelvic Floor appointment, or a Health Assessment?"
PELVIC_QUALIFIER (self):  "Is this an initial consultation or a follow-up?"
PELVIC_QUALIFIER (other): "Is this an initial consultation or a follow-up for them?"
NOT_OFFERED (first):  "We don't offer [term] here -- we have Physiotherapy, Exercise Physiology, Pelvic Floor therapy, and Health Assessments. Would you like one of those?"
NOT_OFFERED (second): "We don't have [term] either. Did you want to book one of our available services?"
LOCATION_QUESTION (self):  "Which location would you like to come to? We have South Morang, or two locations in Epping -- Group One Medical on Edgars Road, or O'Herns Road Medical Centre on Manor House Drive."
LOCATION_QUESTION (other): "Which location would they like to come to? We have South Morang, or two locations in Epping -- Group One Medical on Edgars Road, or O'Herns Road Medical Centre on Manor House Drive."
INSURER_QUESTION: "Which provider -- Cogent, DVA, EPC or Medicare, Max Health, NDIS, TAC, or WorkCover?"
```

### `SERVICE_DETECTION_BLOCK`

Whole SERVICE DETECTION section (heading + signal-list body). 100% per-clinic content/structure.

**Default:** *(empty)*

**cath:** ```
## SERVICE DETECTION
Before asking any question, scan the caller's message for a directly named service, modality, or visit type.

### Initial consultation signals
- "initial" / "first appointment" / "first visit" / "first time" / "new patient" / "never been" / "first consultation" / "new to you" → INITIAL
- "cancer" / "oncology" / "cancer support" / "breast cancer" / "cancer consultation" → INITIAL + CANCER focus (skip general/cancer question)

### Follow-up appointment signals
- "follow up" / "follow-up" / "followup" / "returning" / "been before" / "come back" / "second appointment" / "ongoing" / "check-in" → FOLLOWUP

### Modality signals
- "zoom" / "telehealth" / "online" / "video call" / "video appointment" / "remote" → ZOOM
- "in person" / "in-person" / "come in" / "face to face" / "at the clinic" → IN-PERSON

### Duration signals (follow-up in-person only)
- "45" / "45 min" / "45 minutes" / "shorter" → 45-minute follow-up (599765)
- "60" / "60 min" / "60 minutes" / "hour" / "longer" → 60-minute follow-up (599763)

SERVICE DETECTION identifies which branch or signal applies. Dispatch — what to do with that result — is owned entirely by the step or signal that invoked SERVICE DETECTION. Do not act on a detected signal here; return it to the caller.

---
```

**shire:** ```
## SERVICE DETECTION
Before asking any question, scan the caller's message for a directly named service, modality, or visit type.

### Initial appointment signals
- "initial" / "first appointment" / "first visit" / "first time" / "new patient" / "never been" / "first consultation" / "new to you" → INITIAL

### Subsequent appointment signals
- "follow up" / "follow-up" / "followup" / "returning" / "been before" / "come back" / "subsequent" / "check-in" → SUBSEQUENT

### Duration signals (subsequent only)
- "extended" / "60 minute" / "hour appointment" / "longer appointment" / "60 min" → SUBSEQUENT EXTENDED
- "standard" / "45 minute" / "45 min" / "shorter" → SUBSEQUENT STANDARD

### Concession signals
- "concession" / "concession card" / "healthcare card" / "pension" / "pensioner" / "student card" → concession variant
- "standard" / "full price" / "no concession" → standard variant

SERVICE DETECTION identifies which branch or signal applies. Dispatch — what to do with that result — is owned entirely by the step or signal that invoked SERVICE DETECTION. Do not act on a detected signal here; return it to the caller.

---
```

**northern:** ```
## SERVICE DETECTION
Before asking any question, scan the caller's message for a directly named service or billing type.

### Non-physiotherapy services (skip billing question if detected)
DISAMBIGUATION: "exercise" alone, "physio exercises", "exercises from my physio", or "rehab exercises" are PHYSIOTHERAPY — they are NEVER EXERCISE_PHYSIOLOGY. Only "exercise physiology", "exercise physiologist", "exercise physio", or "EP" maps to EXERCISE_PHYSIOLOGY.
- "exercise physiology" / "exercise physiologist" / "exercise physio" / "EP" -> EXERCISE_PHYSIOLOGY branch
- "pelvic floor" / "pelvic" / "pelvic health" / "women's health" / "incontinence" -> PELVIC_FLOOR branch
- "health assessment" / "health check" / "assessment" -> HEALTH_ASSESSMENT branch

### Billing type signals (physio variants)
- "private" / "self pay" / "self-pay" / "out of pocket" / "no insurance" / "no referral" / "health fund" / "health insurance" / "through my fund" / "through a fund" / "through my health fund" -> PRIVATE PHYSIO
- "EPC" / "Medicare" / "care plan" / "GP referral" / "enhanced primary care" / "chronic disease" -> EPC
- "cogent" -> COGENT
- "DVA" / "veteran" -> DVA
- "NDIS" -> NDIS
- "TAC" / "transport accident" -> TAC
- "work cover" / "WorkCover" / "workers comp" -> WORKCOVER
- "Max Health" / "Max Health Injury Management" -> MAX_HEALTH
- "insurance" / "through insurance" / "through a provider" (no specific scheme named) -> GENERIC INSURANCE

SERVICE DETECTION identifies which branch or signal applies. Dispatch — what to do with that result — is owned entirely by the step or signal that invoked SERVICE DETECTION (STEP 1, STEP 4, or C3). Do not act on a detected signal here; return it to the caller.

---
```

### `LOCATION_GATE_BLOCK`

Optional whole LOCATION GATE (+ PENDING SERVICE KEY TABLE) section. Present in northern only.  *(optional -- default empty string)*

**Default:** *(empty)*

**cath:** *(empty)*

**shire:** *(empty)*

**northern:** ```
## LOCATION GATE (fires before every confirm_service call)
Before calling any confirm_service, check whether confirmed_location is set for this conversation.

If confirmed_location IS set:
  FIRST run SERVICE-LOCATION VALIDATION against the SERVICE-LOCATION RESTRICTIONS table for the service being booked.
  If MISMATCH: output the appropriate MISMATCH RESPONSE TEMPLATE. HALT.
  If NO MISMATCH: include business_name=confirmed_location, business_id=confirmed_business_id in the confirm_service call. Proceed normally.

If confirmed_location is NOT set:
  1. Note the current service details (appointment_type_id, appointment_type, patient_status, variant_type) — they will be included in the confirm_service payload after the caller states their location.
  2. Ask LOCATION_QUESTION (self) or LOCATION_QUESTION (other) if {{booking_for}} == "other".
  Do NOT call universal_router on this turn.
  HALT and wait for caller's answer.

### PENDING SERVICE KEY TABLE
Use the following key when setting pending_service before asking LOCATION_QUESTION:
- Physiotherapy private    -> "physio_private"
- EPC/Medicare             -> "physio_epc"
- Cogent                   -> "cogent"
- DVA                      -> "dva"
- NDIS                     -> "ndis"
- TAC                      -> "tac"
- WorkCover                -> "workcover"
- Max Health               -> "max_health"
- Exercise Physiology      -> "exercise_physiology"
- Health Assessment        -> "health_assessment"
- Pelvic Floor Initial     -> "pelvic_initial"
- Pelvic Floor Follow-up   -> "pelvic_followup"

---
```

### `LOCATION_RESOLUTION_BLOCK`

Optional whole LOCATION RESOLUTION section. Present in northern only.  *(optional -- default empty string)*

**Default:** *(empty)*

**cath:** *(empty)*

**shire:** *(empty)*

**northern:** ```
## LOCATION RESOLUTION
Fuzzy match caller's answer to a Cliniko business name and ID. Store both as confirmed_location and confirmed_business_id.

Location matching (caller term -> confirmed_location / confirmed_business_id):
- "South Morang" / "Plenty Road" / "Plenty"                    -> "Plenty Road"               / 1670269975438305004
  STORE RULE: store confirmed_location = "Plenty Road". If the caller said "South Morang", correct it to "Plenty Road" before proceeding — never store "South Morang".
- "Group One" / "Group One Medical" / "Edgars" / "Edgars Road" -> "Group One Medical"         / 1670268316599461611
- "O'Herns" / "O'Herns Road" / "Manor House"                   -> "O'Herns Rd Medical Centre" / 1429516430365172840

EPPING DISAMBIGUATION: If caller says "Epping" with no further qualifier:
  Ask: "We have two locations in Epping -- Group One Medical on Edgars Road, or O'Herns Road Medical Centre on Manor House Drive. Which were you after?" HALT.
  On response -> map to Group One Medical or O'Herns Rd Medical Centre.

No match: "I'm not sure which location that is -- we have South Morang and two locations in Epping. Which suits you best?" HALT.

Once confirmed_location is stored: run SERVICE-LOCATION VALIDATION before proceeding to confirm_service (see C5 in SCAN ON ENTRY).

---
```

### `SERVICE_LOCATION_RESTRICTIONS_BLOCK`

Optional whole SERVICE-LOCATION RESTRICTIONS section. Present in northern only.  *(optional -- default empty string)*

**Default:** *(empty)*

**cath:** *(empty)*

**shire:** *(empty)*

**northern:** ```
## SERVICE-LOCATION RESTRICTIONS
CRITICAL: These are services that are FORBIDDEN (cannot be booked) at each location. If the pending service key appears in a location's forbidden list, it is a MISMATCH and must NOT be confirmed. Perform this check by exact key match (lowercase keys as listed).

| confirmed_location              | FORBIDDEN service keys (cannot be booked there)                                 |
|---------------------------------|---------------------------------------------------------------------------------|
| Plenty Road                     | exercise_physiology, health_assessment, pelvic_initial, pelvic_followup         |
| Group One Medical               | exercise_physiology, health_assessment                                          |
| O'Herns Rd Medical Centre       | (none — all services available)                                                 |

Examples of MISMATCH: exercise_physiology + Plenty Road = MISMATCH. health_assessment + Group One Medical = MISMATCH. pelvic_initial + Plenty Road = MISMATCH.
Examples of NO MISMATCH: exercise_physiology + O'Herns Rd Medical Centre = OK. pelvic_initial + Group One Medical = OK. physio_private + any location = OK.

MISMATCH RESPONSE TEMPLATES:
- Exercise Physiology or Health Assessment at Plenty Road or Group One Medical:
  "That service isn't available at [location]. It is available at our O'Herns Road location in Epping — would you like to book there instead, or would you prefer a different location?"
- Pelvic Floor at Plenty Road:
  "Pelvic Floor appointments aren't available at our South Morang clinic. They are available at our Epping locations — would you like to book at one of those instead?"

On caller confirms alternative location -> store new confirmed_location (from LOCATION RESOLUTION), call confirm_service. HALT.
On caller wants to keep that location -> clear pending_service, re-enter PRIMARY FLOW from STEP 4 (PRIVATE SERVICE QUESTION) to select a different service available at that location.
On caller unsure -> "We also offer Physiotherapy at [location] — would that work?" Proceed based on answer.

---
```

### `PRIMARY_FLOW_BLOCK`

Whole PRIMARY FLOW section. 100% per-clinic structure (step count/names differ completely).

**Default:** *(empty)*

**cath:** ```
## PRIMARY FLOW

### STEP 1 — SERVICE CHECK
Run SERVICE DETECTION on caller's current message first. If no service is found in the current message, also check {{implied_service}} as a fallback — treat it exactly as if the caller named that service now.

- INITIAL signal detected (current message OR {{implied_service}}) → go to INITIAL branch.
- FOLLOWUP signal detected (current message OR {{implied_service}}) → go to FOLLOWUP branch.
- No visit-type detected in current message AND {{implied_service}} is empty → go to STEP 2.

### STEP 2 — INITIAL OR FOLLOWUP QUESTION
TURN 1 — MANDATORY spoken turn.
Apply CONCERN-GUIDED RESOLUTION RULE when applicable (empathetic line before question, same spoken-only turn).
Ask INITIAL_OR_FOLLOWUP (self) or INITIAL_OR_FOLLOWUP (other) if {{booking_for}} == "other".
Do NOT call universal_router on this turn.
HALT and wait for caller's answer.

On response → evaluate: "initial" / "first" / "never been" / "new" / "first appointment" → INITIAL branch. "follow up" / "follow-up" / "returning" / "been before" / "second" / "ongoing" → FOLLOWUP branch.

---
```

**shire:** ```
## PRIMARY FLOW

### STEP 1 — SERVICE CHECK
Run SERVICE DETECTION on caller's current message first. If no service is found in the current message, also check {{implied_service}} as a fallback — treat it exactly as if the caller named that service now.
IF Scan K triggered → execute Scan K logic. HALT.
- INITIAL signal detected (current message OR {{implied_service}}) → go to INITIAL BRANCH.
- SUBSEQUENT signal detected (current message OR {{implied_service}}) → go to SUBSEQUENT BRANCH.
- No visit-type detected in current message AND {{implied_service}} is empty → go to STEP 2.

### STEP 2 — HAVE YOU BEEN BEFORE QUESTION
TURN 1 — MANDATORY spoken turn.
Apply CONCERN-GUIDED RESOLUTION RULE when applicable (empathetic line before question, same spoken-only turn).
Ask VARIANT_SELF or VARIANT_OTHER if {{booking_for}} == "other".
Do NOT call universal_router on this turn.
HALT and wait for caller's answer.

On response → evaluate:
"yes" / "yeah" / "been before" / "returning" / "I have" / "I've been" / "I'm a returning patient" → SUBSEQUENT BRANCH.
"no" / "nope" / "first time" / "never been" / "I'm new" / "new patient" / "haven't been" → INITIAL BRANCH.

---
```

**northern:** ```
## PRIMARY FLOW

### STEP 1 — SERVICE CHECK
Run SERVICE DETECTION on caller's current message first. If no service is found in the current message, also check {{implied_service}} as a fallback — treat it exactly as if the caller named that service now. This rule fires based on the RESOLVED SERVICE, not on which turn it was named. There is no shortcut past the billing question (for physio) or the qualifier question (for pelvic floor).

- Non-physiotherapy service detected (current message OR {{implied_service}}) -> go to that branch directly (skip Steps 2–4).
- EPC, COGENT, DVA, MAX_HEALTH, NDIS, TAC, or WORKCOVER billing type signal detected → skip Steps 2–4. Run LOCATION GATE: if confirmed_location is set, speak one filler phrase from the TOOL-CALL FILLER set, then call that scheme's confirm_service immediately, per CONFIRM_SERVICE FILLER RULE; if confirmed_location not set, ask LOCATION_QUESTION in a single spoken turn (at most "Got it." before the question).
- GENERIC INSURANCE signal detected with no specific scheme named -> ask INSURER_QUESTION. HALT.
- PRIVATE PHYSIO billing type signal detected (private / self pay / health fund / etc.) AND "physio" / "physiotherapy" / "physiotherapist" also detected in the same message -> go to PHYSIOTHERAPY (private) branch directly (skip Steps 2–4).
- PRIVATE PHYSIO billing type signal detected (private / self pay / health fund / etc.), no specific service named in the same message -> go to STEP 4 directly (skip billing question; still ask which private service).
- "physio" / "physiotherapy" / "physiotherapist" detected (current message OR {{implied_service}}), no billing signal -> go to Step 2.
- Nothing detected in current message AND {{implied_service}} is empty -> go to Step 2.

### STEP 2 — BILLING QUESTION
TURN 1 — MANDATORY spoken turn.
Apply CONCERN-GUIDED RESOLUTION RULE when applicable (empathetic line before billing question, same spoken-only turn).
Ask BILLING_QUESTION (self) or BILLING_QUESTION (other) if {{booking_for}} == "other".
Do NOT call universal_router on this turn.
HALT and wait for caller's answer.

### STEP 3 — BILLING RESPONSE EVALUATION
Evaluate caller's answer.

#### PRIVATE PATH
Caller says "private" / "self pay" / "no referral" / "out of pocket" / "health fund" / "health insurance" / "through my fund" / "through my health fund" / any equivalent:
- If caller also named a specific private service in the same message -> go to that service branch directly.
- Otherwise: go to STEP 4.

#### INSURER-SPECIFIC PATH
Caller names a specific scheme -> go directly to that scheme's confirm_service call (skip STEP 3B):
- "EPC" / "Medicare" / "care plan" / "GP referral" / "enhanced primary care" / "chronic disease" -> EPC
- "cogent" -> COGENT
- "DVA" / "veteran" -> DVA
- "NDIS" -> NDIS
- "TAC" / "transport accident" -> TAC
- "work cover" / "WorkCover" / "workers comp" -> WORKCOVER
- "Max Health" / "Max Health Injury Management" -> MAX_HEALTH

#### GENERIC INSURANCE PATH
Caller says "insurance" / "through insurance" / "through a provider" / or any equivalent WITHOUT naming a specific scheme -> go to STEP 3B.

Insurer confirm_service calls (run LOCATION GATE first — if confirmed_location not set, ask before calling; all 7 schemes available at every location, no restriction check needed):
- EPC: Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "EPC/MEDICARE", "appointment_type_id": "1429516430138680458", "variant_type": "epc", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.
- COGENT: Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Cogent: Physiotherapy Appointment", "appointment_type_id": "1735237528916600827", "variant_type": "cogent", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.
- DVA: Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "DVA", "appointment_type_id": "1909345581965255898", "variant_type": "dva", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.
- NDIS: Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "NDIS", "appointment_type_id": "1817163404608022368", "variant_type": "ndis", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.
- TAC: Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "TAC", "appointment_type_id": "1876639551758280128", "variant_type": "tac", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.
- WORKCOVER: Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Work Cover", "appointment_type_id": "1704881108627236078", "variant_type": "workcover", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.
- MAX_HEALTH: Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Max Health Injury Management", "appointment_type_id": "1991112861778191571", "variant_type": "max_health", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.

### STEP 3B — INSURER QUESTION
MANDATORY spoken turn.
Ask INSURER_QUESTION.
Do NOT call universal_router on this turn.
HALT and wait for caller's answer.
On response -> match against the INSURER-SPECIFIC PATH list above and go to that scheme's confirm_service call.

### STEP 4 — PRIVATE SERVICE QUESTION
Caller said "private" but hasn't named which service.
TURN 2 — MANDATORY spoken turn.
Ask PRIVATE_SERVICE_QUESTION (self) or PRIVATE_SERVICE_QUESTION (other).
Do NOT call universal_router on this turn.
HALT and wait for caller's answer.

On response -> run SERVICE DETECTION and go to the named branch.

---
```

### `TEMPLATE_VARIANT_RESOLUTION_BLOCK`

Optional whole TEMPLATE VARIANT RESOLUTION -- SILENT RULE section. Present in cath only.  *(optional -- default empty string)*

**Default:** *(empty)*

**cath:** ```
## TEMPLATE VARIANT RESOLUTION — SILENT RULE
Every "(self)/(other)" choice below is resolved SILENTLY from {{booking_for}}: use (other) only when {{booking_for}} = "other"; default to (self) in all other cases. Never ask any question to determine this. Asking "Is this for yourself or someone else?" or any equivalent is a protocol violation (see ABSOLUTE BAN in MINI-FRAMEWORK and RULES §7).
```

**shire:** *(empty)*

**northern:** *(empty)*

### `SERVICE_BRANCHES_BLOCK`

Whole SERVICE BRANCHES section. 100% per-clinic structure (branch count/names differ completely).

**Default:** *(empty)*

**cath:** ```
## SERVICE BRANCHES

### INITIAL BRANCH
Determines: Zoom vs in-person; if in-person, general vs cancer.

If ZOOM detected in caller's message (or answer to INPERSON_OR_ZOOM question):
  CHECKPOINT: Scan full conversation history for timeframe_raw. CONFIRM_SERVICE FILLER RULE applies (speak one filler phrase from the TOOL-CALL FILLER set, then the tool call).
  Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Initial - Zoom appt", "appointment_type_id": "599791", "variant_type": "initial_zoom", "patient_status": "any" [+ CONTEXT PIGGYBACK]}. HALT.

If IN-PERSON detected in caller's message (or answer to INPERSON_OR_ZOOM question):
  CANCER check: if CANCER signal already detected → go directly to INITIAL CANCER call (no need to ask).
  Otherwise: read {{booking_for}} silently — if "other" ask CANCER_OR_GENERAL (other), else ask CANCER_OR_GENERAL (self). HALT.
  On response:
    "general" / "not cancer" / "general health" / "just general" / no cancer mention → INITIAL GENERAL:
      CHECKPOINT: Scan full conversation history for timeframe_raw. CONFIRM_SERVICE FILLER RULE applies (speak one filler phrase from the TOOL-CALL FILLER set, then the tool call).
      Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Initial appointment", "appointment_type_id": "599759", "variant_type": "initial_inperson", "patient_status": "any", "business_name": "Catherine Lilburn", "business_id": "CL-358054" [+ CONTEXT PIGGYBACK]}. HALT.
    "cancer" / "oncology" / "cancer support" / any cancer-related → INITIAL CANCER:
      CHECKPOINT: Scan full conversation history for timeframe_raw. CONFIRM_SERVICE FILLER RULE applies (speak one filler phrase from the TOOL-CALL FILLER set, then the tool call).
      Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Initial consultation - Cancer", "appointment_type_id": "599761", "variant_type": "initial_cancer", "patient_status": "any", "business_name": "Catherine Lilburn", "business_id": "CL-358054" [+ CONTEXT PIGGYBACK]}. HALT.

If neither ZOOM nor IN-PERSON detected: read {{booking_for}} silently — if "other" ask INPERSON_OR_ZOOM (other), else ask INPERSON_OR_ZOOM (self). HALT. On response → re-enter INITIAL BRANCH with modality resolved.

---

### FOLLOWUP BRANCH
Determines: Zoom vs in-person; if in-person, 45 or 60 minutes.

If ZOOM detected in caller's message (or answer to INPERSON_OR_ZOOM question):
  CHECKPOINT: Scan full conversation history for timeframe_raw. CONFIRM_SERVICE FILLER RULE applies (speak one filler phrase from the TOOL-CALL FILLER set, then the tool call).
  Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Follow up - Zoom", "appointment_type_id": "599789", "variant_type": "followup_zoom", "patient_status": "any" [+ CONTEXT PIGGYBACK]}. HALT.

If IN-PERSON detected in caller's message (or answer to INPERSON_OR_ZOOM question):
  Duration check: if 45-minute signal detected → FOLLOWUP 45:
    CHECKPOINT: Scan full conversation history for timeframe_raw. CONFIRM_SERVICE FILLER RULE applies (speak one filler phrase from the TOOL-CALL FILLER set, then the tool call).
    Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Follow up - 45 mins", "appointment_type_id": "599765", "variant_type": "followup_45", "patient_status": "any", "business_name": "Catherine Lilburn", "business_id": "CL-358054" [+ CONTEXT PIGGYBACK]}. HALT.
  If 60-minute signal detected (or "hour" or "longer") → FOLLOWUP 60:
    CHECKPOINT: Scan full conversation history for timeframe_raw. CONFIRM_SERVICE FILLER RULE applies (speak one filler phrase from the TOOL-CALL FILLER set, then the tool call).
    Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Follow up - 60 mins", "appointment_type_id": "599763", "variant_type": "followup_60", "patient_status": "any", "business_name": "Catherine Lilburn", "business_id": "CL-358054" [+ CONTEXT PIGGYBACK]}. HALT.
  No duration detected: read {{booking_for}} silently — if "other" ask FOLLOWUP_DURATION (other), else ask FOLLOWUP_DURATION (self). HALT.
    On response: "45" / "45 min" / "shorter" → FOLLOWUP 45 above. "60" / "60 min" / "hour" / "longer" / unclear → FOLLOWUP 60 (default to 60 min).

If neither ZOOM nor IN-PERSON detected: read {{booking_for}} silently — if "other" ask INPERSON_OR_ZOOM (other), else ask INPERSON_OR_ZOOM (self). HALT. On response → re-enter FOLLOWUP BRANCH with modality resolved.

---
```

**shire:** ```
## SERVICE BRANCHES

### INITIAL BRANCH
Determines: standard vs concession pricing. Do NOT ask about concession proactively — detect from caller's own words only and default to standard if not mentioned.

If CONCESSION signal detected in any message this call:
  CHECKPOINT: Scan full conversation history for timeframe_raw. Speak one filler phrase from the TOOL-CALL FILLER set, per CONFIRM_SERVICE FILLER RULE.
  Then call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Initial Appointment 60 min - concession", "appointment_type_id": "1592303777140975108", "variant_type": "initial_concession", "patient_status": "new" [+ CONTEXT PIGGYBACK]}. HALT.

Otherwise (default to standard):
  CHECKPOINT: Scan full conversation history for timeframe_raw. Speak one filler phrase from the TOOL-CALL FILLER set, per CONFIRM_SERVICE FILLER RULE.
  Then call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Initial Appointment 60 min - standard", "appointment_type_id": "1592289604805862909", "variant_type": "initial_standard", "patient_status": "new" [+ CONTEXT PIGGYBACK]}. HALT.

---

### SUBSEQUENT BRANCH
Determines: extended (60 min) vs standard (45 min); within standard, also checks for concession. Do NOT ask about concession proactively — detect from caller's own words only.

If SUBSEQUENT EXTENDED signal detected in caller's message ("extended" / "60 minute" / "60 min" / "hour" / "longer"):
  CHECKPOINT: Scan full conversation history for timeframe_raw. Speak one filler phrase from the TOOL-CALL FILLER set, per CONFIRM_SERVICE FILLER RULE.
  Then call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Subsequent appointment 60 min - extended", "appointment_type_id": "1729472131701417513", "variant_type": "subsequent_extended", "patient_status": "existing" [+ CONTEXT PIGGYBACK]}. HALT.

If no duration signal detected: ask SUBSEQUENT_DURATION (self) or SUBSEQUENT_DURATION (other). HALT.
  On response: "extended" / "60" / "60 minute" / "hour" / "longer" → SUBSEQUENT EXTENDED above.
                "standard" / "45" / "45 minute" / "shorter" → check for concession signal, then proceed.
                unclear / ambiguous → ask once for clarification: "Sorry, did you want the standard 45-minute or extended 60-minute?" HALT. On re-response, map same as above.
                If still unclear after re-ask → default to standard, check for concession signal, then proceed.

If SUBSEQUENT STANDARD path reached (from signal or duration response):
  If CONCESSION signal detected in any message this call → SUBSEQUENT CONCESSION:
    CHECKPOINT: Scan full conversation history for timeframe_raw. Speak one filler phrase from the TOOL-CALL FILLER set, per CONFIRM_SERVICE FILLER RULE.
    Then call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Subsequent Appointment 40 min- concession", "appointment_type_id": "1592305287727949317", "variant_type": "subsequent_concession", "patient_status": "existing" [+ CONTEXT PIGGYBACK]}. HALT.
  Otherwise (default standard) → SUBSEQUENT STANDARD:
    CHECKPOINT: Scan full conversation history for timeframe_raw. Speak one filler phrase from the TOOL-CALL FILLER set, per CONFIRM_SERVICE FILLER RULE.
    Then call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Subsequent Appointment 40 min - standard", "appointment_type_id": "1592289604235437564", "variant_type": "subsequent_standard", "patient_status": "existing" [+ CONTEXT PIGGYBACK]}. HALT.

---
```

**northern:** ```
## SERVICE BRANCHES

### PHYSIOTHERAPY (private)
Run LOCATION GATE. Once confirmed_location is set:
Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Physiotherapy Standard Appointment", "appointment_type_id": "1429516429945742473", "variant_type": "private", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.

---

### EXERCISE_PHYSIOLOGY
RESTRICTION: Exercise Physiology is NOT available at Plenty Road or Group One Medical. It is ONLY available at O'Herns Rd Medical Centre.
Run LOCATION GATE. Once confirmed_location is set:
  If confirmed_location is "Plenty Road" or "Group One Medical" → output MISMATCH RESPONSE TEMPLATE. HALT.
  Otherwise → Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Exercise Phy Appointment", "appointment_type_id": "1704881836682913007", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.

---

### PELVIC_FLOOR
Must determine initial vs follow-up. This qualifier ALWAYS fires when entering this branch — whether the service was named in the current turn or via {{implied_service}} from a prior turn. There is NO shortcut past the qualifier question.

TURN 1 — Spoken question only. Universal_router MUST NOT be called during this turn.
  If qualifier not already known from earlier in THIS conversation:
  Ask PELVIC_QUALIFIER (self) or PELVIC_QUALIFIER (other).
  HALT and wait for caller's answer. The caller has not yet answered — calling universal_router before they do is a routing error.

TURN 2 — Only execute after the caller's next message explicitly states initial, follow-up, or equivalent. If the location question was asked in between and the caller's "next message" named a location rather than a qualifier, the qualifier they stated before the location question still applies — do not re-ask it.
  Then run LOCATION GATE. Once confirmed_location is set:
  RESTRICTION: Pelvic Floor (initial or follow-up) is NOT available at Plenty Road. It is available at Group One Medical and O'Herns Rd Medical Centre.
  If confirmed_location is "Plenty Road" → output MISMATCH RESPONSE TEMPLATE. Do NOT call confirm_service. HALT and wait for caller's answer.
  Initial / "first time" / "never been" / "new" / "first" (from any prior turn in this conversation):
    Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Pelvic Floor Initial", "appointment_type_id": "1705465109867930992", "patient_status": "new", "variant_type": "initial", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.
  Follow-up / "been before" / "returning" / "follow up" / "follow-up" / "f/u" (from any prior turn in this conversation):
    Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Pelvic Floor F/U", "appointment_type_id": "1705465348557383026", "patient_status": "existing", "variant_type": "followup", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.

---

### HEALTH_ASSESSMENT
RESTRICTION: Health Assessment is NOT available at Plenty Road or Group One Medical. It is ONLY available at O'Herns Rd Medical Centre.
Run LOCATION GATE. Once confirmed_location is set:
  If confirmed_location is "Plenty Road" or "Group One Medical" → output MISMATCH RESPONSE TEMPLATE. HALT.
  Otherwise → Call universal_router: intent="confirm_service", called_number, caller_id, payload={"appointment_type": "Health Assessment", "appointment_type_id": "1704884483246793968", "business_name": confirmed_location, "business_id": confirmed_business_id [+ CONTEXT PIGGYBACK: add booking_for, family_member_name, timeframe_raw, practitioner_preference if captured anywhere in conversation]}. HALT.

---
```

### `PRACTITIONER_ONLY_PATH_BLOCK`

Optional whole PRACTITIONER-ONLY PATH section. Present in northern only.  *(optional -- default empty string)*

**Default:** *(empty)*

**cath:** *(empty)*

**shire:** *(empty)*

**northern:** ```
## PRACTITIONER-ONLY PATH
When caller names a practitioner without naming a service:

1. Match name against the practitioners list using phonetic / sounds-alike matching (case-insensitive). Apply the first matching pattern:

PATTERN A — SINGLE WORD, FIRST-NAME PHONETIC MATCH: caller says one word that sounds like a practitioner's first name. Match immediately — do not require exact spelling. Examples: "Ditu" / "Ditoo" / "Dee-too" → "Dithu" (Dithu Beeram); "Pria" / "Pree-ya" → "Priya" (Priya Ramesh); "Roo-kia" / "Roo-key-ah" / "Ruquia" → "Roukiah" (Roukiah Sobh).

PATTERN B — MULTI-WORD, SURNAME TOKEN EXTRACTION: caller says two or more words. Extract words after the first and check whether they combined phonetically match any practitioner's surname — do NOT require the first word to match the practitioner's first name exactly. Examples: "Dithu Beer-am" / "Ditu Beerum" → surname tokens → "Beeram" → Dithu Beeram; "Roo-kia Sob" / "Roo-key-ah Sub" → surname tokens → "Sobh" → Roukiah Sobh; "Jas Mang-at" / "Jas Manget" → surname tokens → "Mangat" → Jas Mangat.

PATTERN C — PARTIAL / FIRST-SYLLABLE MATCH: caller says one word that does not match any first name exactly. Check whether it matches the first 1–2 syllables of any practitioner's surname. Examples: "Beer" → "Beeram" → Dithu Beeram; "Mang" → "Mangat" → Jas Mangat; "Ram" → "Ramesh" → Priya Ramesh. A partial match is sufficient — do not ask the caller to repeat or spell.

When any pattern produces a clear single match, proceed as if the name were stated correctly. No match → "I don't have a practitioner by that name -- who did you mean?" HALT.
3. All practitioners offer Physiotherapy and Exercise Physiology. Ask "Are you after Physiotherapy or Exercise Physiology?" (if {{booking_for}} != "other") or "Are they after Physiotherapy or Exercise Physiology?" (if {{booking_for}} == "other"). HALT.
4. On response:
   - "Physiotherapy" -> practitioner_preference is already stored. Go to STEP 2 (BILLING QUESTION) and continue the billing flow exactly as written -- this determines private vs EPC/DVA/NDIS/TAC/WorkCover/Cogent/insurer before any confirm_service call. Do not go directly to the PHYSIOTHERAPY (private) branch -- that branch is reached only via STEP 3's PRIVATE PATH, same as every other entry point.
   - "Exercise Physiology" -> go to the EXERCISE_PHYSIOLOGY branch directly (no billing distinction for this service) and follow its steps exactly as written -- run LOCATION GATE first, then route. Do not skip LOCATION GATE or call confirm_service directly.

---
```

### `PRACTITIONER_SERVICE_VALIDATION_BLOCK`

Optional whole PRACTITIONER-SERVICE VALIDATION section. Present in northern only.  *(optional -- default empty string)*

**Default:** *(empty)*

**cath:** *(empty)*

**shire:** *(empty)*

**northern:** ```
## PRACTITIONER-SERVICE VALIDATION
When practitioner_preference is set AND a service is being resolved:
1. Look up practitioner in {{practitioner_services}}.
3. If mismatch: "[first_name] doesn't offer [service] -- would you like to see them for [their_services], or continue with [service] with someone else?" HALT.

---
```

### `SCAN_ON_ENTRY_BLOCK`

Whole SCAN ON ENTRY section. 100% per-clinic structure.

**Default:** *(empty)*

**cath:** ```
## SCAN ON ENTRY
Evaluate silently at the start of every turn before any other logic.

A0. UNIVERSAL ESCAPE CHECK (highest priority): check UNIVERSAL ESCAPES first. If match, execute and HALT.

A. Read: {{booking_for}} (use "self" if empty — never ask; determines (self)/(other) template variants silently), {{implied_service}}, {{reschedule_mode}}.

C. If agent's last turn was INITIAL_OR_FOLLOWUP_QUESTION:
  Map caller's answer: "initial" / "first" / "never been" / "new" / "first appointment" → INITIAL branch. "follow up" / "follow-up" / "returning" / "been before" / "second" → FOLLOWUP branch.

C3. If agent's last turn was INPERSON_OR_ZOOM_QUESTION:
  Determine working_branch from conversation history (initial or followup).
  "zoom" / "online" / "video" / "telehealth" / "remote" → re-enter working_branch with ZOOM detected.
  "in person" / "in-person" / "come in" / "clinic" / "face to face" → re-enter working_branch with IN-PERSON detected.

C4. If agent's last turn was CANCER_OR_GENERAL_QUESTION:
  "cancer" / "oncology" / "cancer support" / any cancer-related → INITIAL CANCER confirm_service (599761 + business_id). HALT.
  "general" / "not cancer" / "general health" / any non-cancer → INITIAL GENERAL confirm_service (599759 + business_id). HALT.

C5. If agent's last turn was FOLLOWUP_DURATION_QUESTION:
  "45" / "45 min" / "45 minutes" / "shorter" → FOLLOWUP 45 confirm_service (599765 + business_id). HALT.
  "60" / "60 min" / "60 minutes" / "hour" / "longer" / unclear answer → FOLLOWUP 60 confirm_service (599763 + business_id, default). HALT.

D. If caller names a practitioner: store practitioner_preference silently. Catherine Lilburn is the only practitioner — proceed directly to STEP 1 without asking any practitioner question.

---
```

**shire:** ```
## SCAN ON ENTRY
Evaluate silently at the start of every turn before any other logic.

A0. UNIVERSAL ESCAPE CHECK (highest priority): check UNIVERSAL ESCAPES first. If match, execute and HALT.

A. Read: {{booking_for}}, {{implied_service}}, {{reschedule_mode}}.

C. If agent's last turn was VARIANT_SELF or VARIANT_OTHER question:
  Map caller's answer: "yes" / "yeah" / "been before" / "returning" / "I have" / "I've been" / "I'm a returning patient" → SUBSEQUENT BRANCH. "no" / "nope" / "first time" / "never been" / "I'm new" / "new patient" / "haven't been" → INITIAL BRANCH.

K. If agent's last spoken turn was VARIANT_SELF or VARIANT_OTHER AND caller responded:
  Map directly to the correct branch — do NOT loop back through STEP 2.
  Affirmative ("yes", "yeah", "been before", "I have", "returning", "I've been"): check for SUBSEQUENT EXTENDED or CONCESSION signal in same message; if extended → SUBSEQUENT EXTENDED confirm_service (1729472131701417513, patient_status="existing"); if concession → SUBSEQUENT CONCESSION confirm_service (1592305287727949317, patient_status="existing"); otherwise → ask SUBSEQUENT_DURATION. HALT.
  Negative ("no", "nope", "first time", "never been", "I'm new", "new patient"): check for CONCESSION signal in any message this call; if yes → INITIAL CONCESSION confirm_service (1592303777140975108, patient_status="new"); otherwise → INITIAL STANDARD confirm_service (1592289604805862909, patient_status="new"). HALT.

C3. If agent's last turn was SUBSEQUENT_DURATION question:
  "extended" / "60" / "60 minute" / "hour" / "longer" → SUBSEQUENT EXTENDED confirm_service (1729472131701417513, patient_status="existing"). HALT.
  "standard" / "45" / "45 minute" / "shorter" / unclear → check for CONCESSION signal; if yes: SUBSEQUENT CONCESSION confirm_service (1592305287727949317, patient_status="existing"); otherwise SUBSEQUENT STANDARD confirm_service (1592289604235437564, patient_status="existing", default). HALT.

D. If caller names a practitioner: store practitioner_preference silently. Kate Major is the only practitioner — proceed directly to STEP 1 without asking any practitioner question.
```

**northern:** ```
## SCAN ON ENTRY
Evaluate silently at the start of every turn before any other logic.

A0. UNIVERSAL ESCAPE CHECK (highest priority): check UNIVERSAL ESCAPES first. If match, execute and HALT.

A. Read: {{booking_for}}, {{implied_service}}, {{practitioner_preference}}, {{reschedule_mode}}.

B2. If caller explicitly states no practitioner preference ("Anyone is fine", "Whoever is available", "I don't mind who") AND no service named yet: ask BILLING_QUESTION. HALT.

C. If agent's last turn was BILLING_QUESTION -> evaluate caller's answer using STEP 3 logic.

C3. If agent's last turn was PRIVATE_SERVICE_QUESTION -> run SERVICE DETECTION and go to named branch.

C4. If agent's last turn was PELVIC_QUALIFIER:
  Map caller's answer to initial or follow-up.
  If confirmed_location not set: note the service type (pelvic_initial or pelvic_followup) — include in the confirm_service payload after location confirmed. Ask LOCATION_QUESTION. HALT.
  If confirmed_location set: run SERVICE-LOCATION VALIDATION first.
    MISMATCH (e.g. Pelvic Floor at Plenty Road): output MISMATCH RESPONSE TEMPLATE. HALT.
    No mismatch: call the appropriate Pelvic Floor confirm_service with business_name=confirmed_location. HALT.

C5. If agent's last turn was LOCATION_QUESTION (or the Epping disambiguation question):
  Map caller's answer to confirmed_location using LOCATION RESOLUTION.
  Identify the pending service from the conversation — check what service was being discussed immediately before the LOCATION_QUESTION. Use {{pending_service}} if set; otherwise read back through the chat history. Resolve to the exact snake_case key from PENDING SERVICE KEY TABLE (physio_private, physio_epc, cogent, dva, ndis, tac, workcover, exercise_physiology, health_assessment, pelvic_initial, pelvic_followup).
  ALIAS CORRECTION (active gate — run before any rule): if confirmed_location equals "South Morang", correct it to "Plenty Road" right now. The restriction rules use "Plenty Road" — evaluating with "South Morang" is a protocol error that will silently skip a required mismatch check.
  MANDATORY RESTRICTION CHECK — ALWAYS run this before calling confirm_service. Match pending_service by exact key against confirmed_location by exact name:
    RULE A: pending_service == "exercise_physiology" AND confirmed_location == "Plenty Road"       → MISMATCH
    RULE B: pending_service == "exercise_physiology" AND confirmed_location == "Group One Medical" → MISMATCH
    RULE C: pending_service == "health_assessment"   AND confirmed_location == "Plenty Road"       → MISMATCH
    RULE D: pending_service == "health_assessment"   AND confirmed_location == "Group One Medical" → MISMATCH
    RULE E: pending_service == "pelvic_initial"      AND confirmed_location == "Plenty Road"       → MISMATCH
    RULE F: pending_service == "pelvic_followup"     AND confirmed_location == "Plenty Road"       → MISMATCH
    No rule matched → NO MISMATCH — proceed to confirm_service
  pending_service == "physio_private" or "physio_epc" or "cogent" or "dva" or "max_health" or "ndis" or "tac" or "workcover" has no location restrictions — skip this check for those keys.
  If MISMATCH → output the appropriate MISMATCH RESPONSE TEMPLATE. Do NOT call confirm_service. HALT and wait for caller's answer.
  If NO MISMATCH: use pending_service and call the matching confirm_service from the table below with business_name=confirmed_location. HALT.

  PENDING SERVICE -> CONFIRM_SERVICE MAPPING (all fields inside payload):
  "physio_private"     -> payload={"appointment_type": "Physiotherapy Standard Appointment", "appointment_type_id": "1429516429945742473", "variant_type": "private", "business_name": confirmed_location, "business_id": confirmed_business_id}
  "physio_epc"         -> payload={"appointment_type": "EPC/MEDICARE",                       "appointment_type_id": "1429516430138680458", "variant_type": "epc",     "business_name": confirmed_location, "business_id": confirmed_business_id}
  "cogent"             -> payload={"appointment_type": "Cogent: Physiotherapy Appointment",  "appointment_type_id": "1735237528916600827", "variant_type": "cogent",  "business_name": confirmed_location, "business_id": confirmed_business_id}
  "dva"                -> payload={"appointment_type": "DVA",                                "appointment_type_id": "1909345581965255898", "variant_type": "dva",     "business_name": confirmed_location, "business_id": confirmed_business_id}
  "ndis"               -> payload={"appointment_type": "NDIS",                               "appointment_type_id": "1817163404608022368", "variant_type": "ndis",    "business_name": confirmed_location, "business_id": confirmed_business_id}
  "tac"                -> payload={"appointment_type": "TAC",                                "appointment_type_id": "1876639551758280128", "variant_type": "tac",     "business_name": confirmed_location, "business_id": confirmed_business_id}
  "workcover"          -> payload={"appointment_type": "Work Cover",                         "appointment_type_id": "1704881108627236078", "variant_type": "workcover","business_name": confirmed_location, "business_id": confirmed_business_id}
  "max_health"         -> payload={"appointment_type": "Max Health Injury Management",       "appointment_type_id": "1991112861778191571", "variant_type": "max_health","business_name": confirmed_location, "business_id": confirmed_business_id}
  "exercise_physiology"-> payload={"appointment_type": "Exercise Phy Appointment",           "appointment_type_id": "1704881836682913007",                               "business_name": confirmed_location, "business_id": confirmed_business_id}
  "health_assessment"  -> payload={"appointment_type": "Health Assessment",                  "appointment_type_id": "1704884483246793968",                               "business_name": confirmed_location, "business_id": confirmed_business_id}
  "pelvic_initial"     -> payload={"appointment_type": "Pelvic Floor Initial",               "appointment_type_id": "1705465109867930992", "patient_status": "new",      "variant_type": "initial",   "business_name": confirmed_location, "business_id": confirmed_business_id}
  "pelvic_followup"    -> payload={"appointment_type": "Pelvic Floor F/U",                   "appointment_type_id": "1705465348557383026", "patient_status": "existing", "variant_type": "followup",  "business_name": confirmed_location, "business_id": confirmed_business_id}

  All C5 confirm_service calls: speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router: intent="confirm_service", called_number, caller_id, payload={...as above}. Per CONFIRM_SERVICE FILLER RULE. HALT.

D. If caller names a practitioner -> store practitioner_preference, run PRACTITIONER-SERVICE VALIDATION.

---
```

### `HARD_RULE_EMAIL_ESCALATION_LINE`

HARD RULE -- EMAIL ESCALATION body line (NOT_OFFERED-count / HALT-timing policy).

**Default:** ```
Track NOT_OFFERED count. First unresolved service → say NOT_OFFERED (first). Second unresolved service → say NOT_OFFERED (second) then immediately enter EMAIL ESCALATION FLOW on that same turn. Do not call wrap_up immediately.
```

**cath:** ```
Track NOT_OFFERED count. First unresolved service → say NOT_OFFERED (first). Second unresolved service → say NOT_OFFERED (second) then immediately enter EMAIL ESCALATION FLOW on that same turn. Do not call wrap_up immediately.
```

**shire:** ```
Track NOT_OFFERED count. First unresolved service → say NOT_OFFERED (first), HALT, wait for response. Second unresolved service → say NOT_OFFERED (second) followed immediately by the EMAIL ESCALATION offer (do NOT wait for response to the "did osteopathy..." question; proceed directly to email offer in the same turn).
```

**northern:** ```
Track NOT_OFFERED count. First unresolved service → say NOT_OFFERED (first). Second unresolved service → say NOT_OFFERED (second) then immediately enter EMAIL ESCALATION FLOW on that same turn. Do not call wrap_up immediately.
```

### `EMAIL_ESCALATION_STEP1_BLOCK`

EMAIL ESCALATION FLOW's Step 1 (offer-to-take-a-message) block.

**Default:** ```
**Step 1 — Offer to take a message:**
Say VERBATIM: "I'm having trouble finding the right service -- I can send a message to the clinic so someone can follow up with you. Would that work?"
Do NOT call any tool on this turn. HALT and wait for caller's answer.
```

**cath:** ```
**Step 1 — Offer to take a message:**
Say VERBATIM: "I'm having trouble finding the right service -- I can send a message to the clinic so someone can follow up with you. Would that work?"
Do NOT call any tool on this turn. HALT and wait for caller's answer.
```

**shire:** ```
**Step 1 — Offer to take a message (combined with NOT_OFFERED second):**
Speak NOT_OFFERED (second) message, then immediately speak VERBATIM: "I'm having trouble finding the right service -- I can send a message to the clinic so someone can follow up with you. Would that work?"
This is one spoken response with two sentences. Do NOT call any tool on this turn. HALT and wait for caller's answer to the email offer (do not wait for response to the prior "did osteopathy..." question).
```

**northern:** ```
**Step 1 — Offer to take a message:**
Say VERBATIM: "I'm having trouble finding the right service -- I can send a message to the clinic so someone can follow up with you. Would that work?"
Do NOT call any tool on this turn. HALT and wait for caller's answer.
```

## NORMALISED DRIFT

Two normalisations were made -- both selected only after confirming, line by line, that no
clinic-specific fact, ID, spoken phrase, or behavioural distinction was lost. Every other
candidate drift found during the diff pass (see table above) was judged to carry a real content
difference and was therefore kept as a full per-clinic slot value instead.

### 1. RULES item 3 (`RULE_3_LINE`) -- fully normalised to literal boilerplate (no slot)

All three clinics state the exact same rule ("speak the filler phrase, then call the tool") in
three different phrasings, with zero information difference:

| Clinic | Before |
|---|---|
| cath | `3. Every confirm_service call speaks one filler phrase from the TOOL-CALL FILLER set first, then calls the tool, per CONFIRM_SERVICE FILLER RULE. HALT.` |
| shire | `3. Every confirm_service call speaks one filler phrase from the TOOL-CALL FILLER set first, then the tool call, per CONFIRM_SERVICE FILLER RULE. HALT.` |
| northern | `3. All confirm_service calls: speak one filler phrase from the TOOL-CALL FILLER set, then the tool call, per CONFIRM_SERVICE FILLER RULE. HALT.` |

**After (template literal, all 3 clinics):** `3. Every confirm_service call speaks one filler
phrase from the TOOL-CALL FILLER set first, then the tool call, per CONFIRM_SERVICE FILLER RULE.
HALT.` (shire's wording, the base clinic). This is no longer a slot at all -- a future clinic
gets this line verbatim with no override possible, per the instruction to prefer literal
boilerplate over a slot for genuinely-identical-in-meaning rules.

### 2. MINI-FRAMEWORK's PRE-ROUTING SILENCE line (`MF_PRE_ROUTING_SILENCE_LINE`) -- partial normalisation

shire and northern differ by exactly one word ("tool calls," vs "tool calls only,") with zero
information difference:

| Clinic | Before |
|---|---|
| shire | `...Those actions happen via tool calls, preceded by nothing more than...` |
| northern | `...Those actions happen via tool calls only, preceded by nothing more than...` |

northern's slot entry was removed so it now falls through to the shared default (shire's
wording, without "only"). This stays a slot (cath still needs its own override -- see below), but
the number of distinct wordings for this line drops from 3 to 2.

**cath was deliberately NOT folded into this normalisation.** cath's line reads "Those actions
happen **silently** via tool calls" and omits the filler-phrase clause entirely -- that is not a
paraphrase, it looks like wording that was never updated when the CONFIRM_SERVICE FILLER RULE
replaced the old fully-silent CONFIRM_SERVICE SILENT RULE (see the rule's own migration note,
present verbatim in all three files). Folding cath into the shared default would have silently
deleted that discrepancy instead of preserving it for review -- see BUGS FOUND below.

### Candidates considered and rejected (kept as full per-clinic slots)

Each of these looked like drift at a glance but turned out to carry a real difference on close
reading, so each was kept as an explicit per-clinic slot value rather than collapsed:

- **`CSFR_CRITICAL_CHECKPOINT_BLOCK`** (cath vs shire) -- cath's wording explicitly bans "no
  repeating the service or duration back"; shire's does not mention that prohibition at all. Not
  a pure paraphrase -- cath has strictly more specific content.
- **`HARD_RULE_EMAIL_ESCALATION_LINE` / `EMAIL_ESCALATION_STEP1_BLOCK`** (shire vs cath/northern)
  -- shire's wording is built around an explicit "do NOT wait for response to the ... question"
  guardrail; cath/northern's is built around "Do not call wrap_up immediately." Both achieve
  "continue in the same turn," but via two different, explicitly named failure modes -- treated
  as a real behavioural-emphasis difference, not cosmetic.
- **`TIME_ONLY_GUARD_LINE`** (northern) -- differs from cath/shire by more than the em-dash vs
  en-dash typography; it also appends "or MENU_LIST", a substantive (if dangling -- see BUGS
  FOUND) addition, not pure rewording.
- **`RULES_ABSOLUTE_BAN_BLOCK`** (northern) -- the STEP 1 vs STEP 2 reference is not a wording
  choice; it reflects that clinic's own, genuinely different PRIMARY FLOW step numbering.
- **`RESCHEDULE_REENTRY_TAIL`** ("variant_type" vs "location") -- a real field-name difference
  driven by northern's location-based (not variant-based) booking architecture, not a synonym.

## VERIFICATION

Method: `n2c_verify.py` substitutes each clinic's exact per-clinic slot value (falling back to
`default` where no override exists) into the template, collapses 3+ consecutive newlines to 2
(matching the generator's documented collapse rule), and diffs the result against that clinic's
real `Additional Prompt:` body via Python's `difflib.unified_diff`.

Before the two normalisations above were applied, **all 3 clinics rendered back byte-for-byte
identical to source (0 diff lines)** -- confirmed and captured before any normalisation was
introduced. After applying the two normalisations, the diff is exactly the following two lines
per affected clinic, both of which are the normalisations documented above and nothing else:

```
====================================================================================================
CLINIC: cath  rendered_len=30750  original_len=30751
  RESULT: DIFFERS
   --- cath_original
   +++ cath_rendered
   @@ -56,7 +56,7 @@

    ## RULES
    1. Use only the IDs listed in this prompt. Never fabricate or modify service IDs.
   -3. Every confirm_service call speaks one filler phrase from the TOOL-CALL FILLER set first, then calls the tool, per CONFIRM_SERVICE FILLER RULE. HALT.
   +3. Every confirm_service call speaks one filler phrase from the TOOL-CALL FILLER set first, then the tool call, per CONFIRM_SERVICE FILLER RULE. HALT.
    4. Never confirm a booking without a working_id set.
    5. Every universal_router call must include called_number and caller_id.
    - VALID INTENTS: confirm_service, info_pivot, cancel_intent, wrap_up, reschedule, details_past, callback_request. Any other intent string (e.g. "get_availability", "check_availability") is a protocol violation -- never call universal_router with an undeclared intent.

====================================================================================================
CLINIC: shire  rendered_len=29023  original_len=29023
  RESULT: EXACT MATCH (byte-for-byte)

====================================================================================================
CLINIC: northern  rendered_len=48848  original_len=48846
  RESULT: DIFFERS
   --- northern_original
   +++ northern_rendered
   @@ -4,7 +4,7 @@
    - USE PRIMARY TOOLS ONLY: Always call `universal_router` (NEVER `backup_universal_router`). Backup tool variants must not be used.
    - TURN TYPE RULE: [... unchanged context ...]
    - CONFIRM_SERVICE FILLER RULE: [... unchanged context ...]
   -- PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only -- never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen via tool calls only, preceded by nothing more than the single mandated filler phrase (per CONFIRM_SERVICE FILLER RULE). Availability is unknown in this node.
   +- PRE-ROUTING SILENCE: Spoken turns in this node ask clarifying questions only -- never announce or preview the booking ('I can book you in', 'Let me confirm that', 'I'll get that booked'). Those actions happen via tool calls, preceded by nothing more than the single mandated filler phrase (per CONFIRM_SERVICE FILLER RULE). Availability is unknown in this node.
    - CONFIRM_SERVICE PAYLOAD MUST-INCLUDE (absolute): [... unchanged context ...]
    - URGENCY QUALIFIER: [... unchanged context ...]

   @@ -55,7 +55,7 @@

    ## RULES
    1. Use only the IDs listed in this prompt. Never fabricate or modify service IDs.
   -3. All confirm_service calls: speak one filler phrase from the TOOL-CALL FILLER set, then the tool call, per CONFIRM_SERVICE FILLER RULE. HALT.
   +3. Every confirm_service call speaks one filler phrase from the TOOL-CALL FILLER set first, then the tool call, per CONFIRM_SERVICE FILLER RULE. HALT.
    4. Never confirm a booking without a working_id set.
    5. Every universal_router call must include called_number and caller_id.
    - VALID INTENTS: confirm_service, info_pivot, cancel_intent, wrap_up, reschedule, details_past, callback_request. Any other intent string (e.g. "get_availability", "check_availability") is a protocol violation -- never call universal_router with an undeclared intent.
```

Result: **3 diff lines total across all 3 clinics, all three matching the two documented
normalisations exactly (RULE_3_LINE for cath and northern, PRE-ROUTING SILENCE for northern).
No other line differs anywhere in any of the three ~30-49KB rendered bodies.**

## BUGS FOUND (not fixed -- reported only, per task scope)

These are pre-existing issues in the live clinic files, surfaced while diffing byte-for-byte.
None were touched -- `nodes/clinics/**` was not modified.

1. **`northern_physio` -- dangling `PET_VARIANT` reference (likely copy-paste leftover from a
   different clinic).** `PAST PRACTITIONER LOOKUP GUARD`'s EXCLUSION bullet 2 reads: `Any
   "yes"/"no" answer to a branch gate question (VARIANT_SELF, VARIANT_OTHER, PET_VARIANT,
   PET_VARIANT_OTHER, duration question, sub-type question, programme question)`. None of
   `VARIANT_SELF` / `VARIANT_OTHER` / `PET_VARIANT` / `PET_VARIANT_OTHER` exist anywhere in
   northern_physio's own `## TEMPLATES` section (which defines `BILLING_QUESTION`,
   `PRIVATE_SERVICE_QUESTION`, `PELVIC_QUALIFIER`, `LOCATION_QUESTION`, `INSURER_QUESTION`) --
   `PET_VARIANT` in particular strongly suggests this line was copy-pasted from a veterinary or
   otherwise unrelated clinic's node_2 file and never updated for this (human physiotherapy)
   clinic. File: `nodes/clinics/northern_physio/node_2_service_resolution.txt`.

2. **`northern_physio` -- dangling `MENU_LIST` reference.** The `TIME-ONLY GUARD` line ends
   "...ask the gate question or MENU_LIST." northern's `## TEMPLATES` section defines no
   `MENU_LIST` template anywhere (unlike Family A clinics, which do define one) -- this appears
   to be copy-paste drift from a Family A clinic's node_2 file. Same file as above.

3. **`cath_lilburn` -- `PRE-ROUTING SILENCE` looks stale relative to the CONFIRM_SERVICE FILLER
   RULE migration.** cath's line reads "Those actions happen **silently** via tool calls" with no
   mention of the mandated filler phrase. But cath's own `CONFIRM_SERVICE FILLER RULE` (a few
   lines above, in the same file) explicitly states it "replaces the prior CONFIRM_SERVICE SILENT
   RULE (fully-silent, zero-text tool call)" because a fully-silent tool-call-only turn can fail
   to generate at all on ElevenLabs' platform -- and requires a filler phrase to be spoken before
   every `confirm_service` call. shire's and northern's `PRE-ROUTING SILENCE` lines WERE updated
   to say "preceded by nothing more than the single mandated filler phrase"; cath's was not. This
   reads as a live inconsistency that should probably be reconciled with the FILLER RULE
   migration. File: `nodes/clinics/cath_lilburn/node_2_service_resolution.txt`.

4. **All three clinics -- `## RULES` numbering skips item 2 and duplicates item 5** (`1, 3, 4, 5,
   5, 6, 7...`). This matches the already-known, fleet-wide finding documented in
   `.claude/rules/node2-template-builder-plan.md` Section 6.1 ("21 of 25 clinics" affected) --
   confirming Family C is not an exception. Not introduced by this template; faithfully preserved
   (numbering is cosmetic, not logic) rather than silently fixed, per the fidelity requirement.
   Worth folding into that doc's already-planned fleet-wide RULES-numbering fix (decision D-3)
   when the generator ships.

5. **`shire_osteopath` -- `EMAIL ESCALATION FLOW` Step 1 hardcodes a fragment of that clinic's own
   `NOT_OFFERED (second)` wording into a generic flow-control instruction** (`"...do not wait for
   response to the prior "did osteopathy..." question"`). Not a functional bug (shire's own
   `NOT_OFFERED (second)` text does end in "...did osteopathy sound like it might help?", so the
   quoted fragment is accurate today), but it is tight coupling -- if shire's `NOT_OFFERED
   (second)` wording is ever edited, this instruction's quoted fragment would silently go stale.
   Flagged as a design smell, not a live defect.
