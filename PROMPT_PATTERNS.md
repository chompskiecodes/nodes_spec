# Prompt Bug Patterns & Fixes

Read this before editing any node prompt. Each section documents recurring bugs and the proven fixes.

Node 11 (Qwen) has its own dedicated pattern doc — see `.claude/rules/qwen-prompt-patterns.md`,
not duplicated here. For shrinking an already-shipped node without regressing it (baseline
self-audit → converse with the node's own model about specific candidates → verify behaviorally
with a fresh instance), see `docs/elevenlabs-node-prompting-reference.md` §4.

## Scope notes — generator exclusions and audit coverage

**A clinic sitting in a generator's `EXCLUDED_CLINICS` (see `generate_node2.py`, `generate_node8.py`,
etc.) is excluded from *template regeneration*, not from bug-fixing or from the guide-style
conversion process (`docs/guide-style-conversion-blueprint.md`).** Those clinics' node files are
hand-maintained precisely because they diverged too far from the family template to slot safely —
that divergence doesn't make them safe to skip when a structural bug pattern below is found or
when a conversion sweep runs. Treat an `EXCLUDED_CLINICS` entry as "fix by hand-editing this
clinic's own `.txt`, then keep it in `EXCLUDED_CLINICS` so the next `generate_node*.py`/`fast_patch.py`
run doesn't silently overwrite the hand fix" — never as "skip this clinic." The only nodes actually
out of scope for review are under `nodes/retired/**` (see `.claude/rules/working-practices.md`).

**Auditing every clinic node in the fleet is not required once a pattern is established.** The
audit loop exists to confirm a *pattern* — one structural self-audit per pattern is sufficient
(see the fleet-wide propagation check in `.claude/rules/working-practices.md`: "One audit per
structural pattern is sufficient — do not re-audit every clinic"). As bug patterns and audit
scores accumulate across nodes and clinics, use that emerging signal to infer where a node needs
heavier corrective/preventative machinery (BLOCKING SIGNAL, MANDATORY PART, OUTPUT CONTRACT, an
explicit NO-DEFAULT/EXCLUSION guard) versus where plain instructive prose already holds up —
rather than re-running the full scenario battery from `docs/guide-style-conversion-blueprint.md`
§6 against every remaining node before drawing that conclusion. Still confirm any structural fix
or conversion against the specific clinic(s) it will ship to (per `docs/guide-style-conversion-blueprint.md`
§4) — this is about not re-deriving the same pattern from scratch on every clinic, not about
skipping verification on the clinic actually being changed.

**`fast_patch.py`'s `compute_nodes_hash()` hashes a clinic's whole directory of `.txt` files
together as one SHA256 (excluding `system_prompt.txt`), not per-file** — confirmed in
`scripts/fast_patch.py`. Practical upshot: an `EXCLUDED_CLINICS` clinic's hand-maintained file
still gets redeployed as-is whenever *any other* node file for that same clinic changes (the whole
directory hash flips), but a fleet-wide generator/template fix that never touches that clinic's
own files leaves its hash — and its content — untouched. Never assume a template-level fix
reached an excluded clinic just because a subsequent `fast_patch.py` run for it showed activity.

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
**Model note:** `gpt-4.1-mini` cannot reliably HALT for SKIN_QUALITY and LED branches. Use `claude-haiku-4-5`. A separate 50-test bakeoff also found `gpt-5-mini` too slow/reasoning-heavy for voice latency on this node — never use it for Node 2 either.

### CONFIRM_SERVICE SILENT RULE — add at top of prompt
**Bug:** Haiku adds `system__message_to_speak` to confirm_service calls despite per-branch "ZERO spoken output".  
**Fix:** Add in `## CONFIRM_SERVICE CALL FORMAT` at the TOP:
```
CRITICAL: Do NOT include system__message_to_speak in any confirm_service call. Zero spoken output.
```
**Required companion (see CONFIRM_SERVICE FILLER OVERRIDE below):** this bare rule is incomplete on its own — it must also include the explicit `OVERRIDE:` clause suspending the system prompt's TOOL-CALL FILLER rule, or Haiku defaults to the system prompt's general filler mandate under call pressure and adds "One moment." before confirm_service anyway.

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

### NO-DEFAULT RULE — now structural, baked into the SUBTYPE+GATE / GATE+DURATION archetype templates
**Bug (feel_heal, 2026-09-09):** Caller says only a bare category name with zero other detail — "I wanna book dry needling" — and Haiku skips straight past BOTH the mandatory tier question ("standard or premium with Ning?") AND the duration question, calling confirm_service immediately with a silently-invented default (standard, 60 min). This is the zero-prior-turns variant of the bug above — the MANDATORY SEQUENCE fix (previous entry) only covers the case where TURN 0's gate question was already answered; this one had no prior turn at all, so the model had nothing anchoring it to "there are more questions coming" except the branch's own step-numbered prose, which wasn't enough under call pressure.
**Root cause:** neither `nodes/node2_templates/branches/_subtype_gate.txt` nor `_gate_duration.txt` — the two archetype sub-templates every multi-step Node 2 branch renders from — carried any structural protection against this. Protection existed only where a past session happened to hand-author a BLOCKING EXAMPLE into that specific clinic's branch slot text in `scripts/node2_configs.py`. A fleet scan the same day found **20 branches across 9 other clinics** with the identical exposure (acacia_healing, alpine_osteopaths, cascade_womens_health, intuitive_health_and_wellness, meraki_holistic_health, palm_beach_osteopathy, speeding_health, the_rehab_podiatrist, totally_well) — none of them had ever been caught because nothing tests "caller states a bare category name with nothing else" by default.
**Fix (structural, 2026-09-09):** added a generic `NO-DEFAULT RULE` line directly into both archetype template files, immediately after the `### <<BRANCH_NAME>>` header — the point of entry into the branch, highest-attention position, evaluated before any of the branch's own step prose:
```
NO-DEFAULT RULE: Once <<BRANCH_NAME>> is matched from the caller's message, every mandatory
sub-type, tier, or duration question below is required before any tool call -- there is no
default answer for a question the caller has not yet answered. WRONG: call confirm_service
using a default sub-type, tier, or duration for any question not yet answered. CORRECT: ask
each unanswered mandatory question in turn, HALT after each one, and call confirm_service only
once every question is answered (or already resolved via a TIER RESOLUTION step or an explicit
statement the caller already made).
```
Every clinic regenerated via `generate_node2.py` on a `SUBTYPE+GATE` or `GATE+DURATION` branch now gets this automatically — **no per-clinic authoring required going forward**, including new clinics onboarded after this date. A clinic-specific concrete `BLOCKING EXAMPLE` (naming the actual caller phrase, per the entry above) is still worth adding on top for any branch a live call has actually caught defaulting — concrete beats generic, per node-prompt-style.md's Haiku Instruction Patterns — but the generic template guard is now the floor every branch gets, not the ceiling.
**Self-audit:** `Agent(model="haiku")`, one probe per archetype (a plain gate+duration branch and the fleet's most complex `SUBTYPE+GATE` branch, 6+ sub-types) — see `docs/AI_HANDOFF.md` or ask for the session that shipped this for the scores.
**Gap this does NOT cover:** `RAW`-archetype branches (raw hand-written `text`, bypassing both templates entirely) get nothing from this fix — any clinic with a multi-question `RAW` branch still needs a manually-authored guard. Check `br.get('archetype') == 'RAW'` in `scripts/node2_configs.py` before assuming a clinic is covered.

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

### LOCATION NAME ALIAS — caller-facing name differs from Cliniko business name
**Bug:** LOCATION_QUESTION offers a caller-facing name (e.g. "South Morang") that differs from the Cliniko business name used as the `confirmed_location` key in the restriction table (e.g. "Plenty Road"). Haiku stores the caller's literal answer without applying the LOCATION RESOLUTION mapping, finds no match in the restriction rules, and silently calls confirm_service for a forbidden combination.  
**Symptom:** Exercise Physiology (or other restricted service) booked at a location where it's blocked — confirmed_location in the payload reads the caller's spoken name, not the Cliniko business name.  
**Root cause (northern_physio, 2026-08-12):** LOCATION_QUESTION said "South Morang"; restriction table used `confirmed_location == "Plenty Road"`. Haiku stored "South Morang", restriction check found no match, confirm_service fired.  
**Fix — three parts, all required:**
1. **LOCATION RESOLUTION alias line:** list the caller-facing name alongside the Cliniko name: `"South Morang" / "Plenty Road" / "Plenty" -> "Plenty Road" / <business_id>`
2. **STORE RULE note** (inline under that entry): `STORE RULE: store confirmed_location = "Plenty Road". If caller said "South Morang", correct it to "Plenty Road" before proceeding — never store "South Morang".`
3. **ALIAS CORRECTION active gate** in C5 MANDATORY RESTRICTION CHECK (immediately before the rules): `ALIAS CORRECTION (active gate — run before any rule): if confirmed_location equals "South Morang", correct it to "Plenty Road" right now. The restriction rules use "Plenty Road" — evaluating with "South Morang" is a protocol error.`

**Detection (onboarding):** During the +ML alias check (see `docs/new_clinic_build.md`), compare each name in LOCATION_QUESTION against the `business_name` column from the per-business audit query. Any mismatch requires all three fixes above.

### CONTEXT PIGGYBACK through long chains (booking_for="other")
**Bug:** `booking_for="other"` and `family_member_name` drop from confirm_service payload after 5+ turns.  
**Fix (two parts):**
1. BOOKING_FOR PRIORITY RULE in CONTEXT PIGGYBACK section: "booking_for captured from conversation OVERRIDES {{booking_for}} DV default. If booking_for='other' was established AT ANY POINT, it MUST appear in confirm_service."
2. CONTEXT PIGGYBACK SUPPLEMENT in SCAN G / Scan C5: "Before calling, check full history for piggybacked fields."

### RESCHEDULER HAND-BACK — confirm_service after Node 7b's `reschedule_different` must carry `reschedule_mode` (2026-09-21)
**Bug:** Node 7b answers a service it cannot re-book with `reschedule_different`; Node 2 re-resolves the service and hands off with `confirm_service`. The backend resets the `reschedule_mode` DV to `""` on every response whose request did not echo `"true"` back inside `payload` (`tools/universal_router_webhook.py`, `_build_router_response`), and Node 7b's RESCHEDULE BYPASS and REAL-CANCEL GUARDs read that DV. The strict Node 2 text had no instruction to carry it: 0/8 (Raymond Terrace), 0/6 (Evolution, Kynd, Yandina) hand-offs in local Haiku agent packs. A real production sweep (30 days, 631 conversations, 1,830 router calls) found 3 `reschedule_different` re-entries, none reaching `confirm_service`, and 273/273 real `confirm_service` results resetting the DV.
**Fix (templates, all four families):** a guard in the same question form Family B's `RESCHEDULE RE-ENTRY GUARD` already used — "was this entry triggered by reschedule_different (the universal_router result that sent the caller into this node shows uni_router_intent "reschedule_different")? If YES: "reschedule_mode": "true" is part of the payload of every confirm_service call from this entry." Family A/C: a `## RESCHEDULE HAND-BACK GUARD` section after the RE-ENTRY GUARD; B: a line in the existing guard's YES branch; E: one paragraph ahead of the PASSTHROUGH steps. Result: 8/8, 6/6, 6/6, 6/6, 6/6 (A Raymond, B, C, Kynd, Yandina) and E held at 8/8, with no spurious carry on ordinary hand-offs. The escapes that send `cancel_intent` with `reschedule_mode` write it inside `payload={"reschedule_mode": "true"}` (the tool schema declares `payload`, not a root-level field).
**Never write** a DV-conditional carry as `when {{reschedule_mode}} == "true", add ...`: ElevenLabs substitutes the value, the model reads the tautology `true == "true"` as an unmet literal comparison, and skips it. Five variants of that idiom (a piggyback bullet, a TOOL CALL bullet, a call-format sentence, a SURVIVAL rule, the DV interpolated into the canonical payload example) all scored 0/8 on Raymond; the question-form guard scored 8/8. Key a carry on something the model can SEE in the conversation (a tool result's `uni_router_intent`), not on a substituted DV token.
**Test-history trap:** a re-entry scenario must include the `reschedule_different` tool exchange (call + result) the live runtime shows — without it Bob Ward looked broken at 0/8 when the strict text already carried 8/8. Build it with `scripts/node2_reschedule_carry.py`. Contract: `tests/test_node2_reschedule_mode_contract.py`. Full record: `docs/in-progress/node2_reschedule_mode_handback_2026_09_21.md`.

### PIGGYBACK PAYLOAD SCOPE — context fields go inside `payload` on EVERY routing call (2026-09-21)
**Bug:** the strict Node 2 text told the model "for confirm_service: inside the payload JSON object; for all other routing calls (info_pivot, cancel_intent, wrap_up, etc.): include as root-level parameters" — `CONTEXT_PIGGYBACK_SCOPING` in `scripts/generate_node2.py` for Family A (15 clinic configs also carried a byte-identical copy) and a literal line in Family B's template. The `universal_router` schema declares only `intent`, `called_number`, `caller_id` and `payload`, so a context field beside `intent` is outside the contract: the backend rescues it and logs an ERROR (`tools/universal_router_webhook.py`, "Root-level payload fields rescued into payload"); 5 such calls in 30 days of real traffic (`return_node` x3, `timeframe_raw` x2). Local Haiku packs with the tool described by its real parameters showed the mechanism: the old text produced `cancel_intent ROOT:timeframe_raw`, `info_pivot ROOT:booking_for,timeframe_raw`, `details_past ROOT:booking_for` (6 root-level placements in Family A's pack, 2 in B's), and the same `cancel_intent` calls dropped `reschedule_mode`. Families C and E never had the sentence and already nested (0 placements).
**Fix:** one positive sentence per family, with no "root" wording: "On every routing call (confirm_service, info_pivot, cancel_intent, details_past, etc.), put these fields inside the payload JSON object. universal_router takes intent, called_number, caller_id and payload." Family A: the slot default (the 16 redundant/near-identical overrides deleted; palm_beach keeps its INSIDE emphasis, relabelled PAYLOAD SCOPING). B: the literal line. C: a line after the "belong inside routing calls" sentence. E: the additive form below. Result (Haiku agent packs, one sample per scenario): root-level placements 6 -> 0 (A), 2 -> 0 (B); A 11/18 -> 18/18 and 15/18, B 11/16 -> 13/16 and 14/16, C unchanged 16/17, E 15/17 -> 17/17.
**Family E needs the additive form (measured):** "put context fields (…, reschedule_mode) inside the payload JSON object" made bob_ward's agents build `cancel_intent`'s payload ONLY from the fields they had captured and drop the shared CANCEL ESCAPE's `reschedule_mode` — 4 of 4 scenarios, reproduced on a second sample, and identical with Family C's bare sentence. E has no in-node piggyback list, so a node-local sentence displaced the shared system prompt's `reschedule_mode` capture rule. "add the CONTEXT PIGGYBACK fields you captured to the payload JSON object, next to any field that call's own format names" kept all four and also fixed `info_pivot` dropping `booking_for`/`timeframe_raw`. Rule: a node-local payload sentence must be additive to whatever the shared prompt or the call's own format already puts in payload.
**Test-harness trap:** `scripts/node2_agent_pack.py` described the tool as `universal_router(intent, payload)` and dropped every other `name=value` on the agent's TOOL line, so a root-level field could never be seen (INV/payload-nested never fired). Build packs with `--real-tool-schema`; the parser now keeps root-level parameters. Battery: `scripts/node2_piggyback_scope.py`. Contract: `tests/test_node2_piggyback_payload_contract.py`. Full record: `docs/in-progress/node2_piggyback_payload_scope_2026_09_21.md`.

### PAYLOAD FORM IN NODE 9 AND NODE 1 CALL LINES — a call the text writes carries its context fields inside `payload` (2026-09-21)
**Bug:** the PIGGYBACK PAYLOAD SCOPE defect in the two other nodes that write calls with fields, and a grep for "root-level" cannot find it: the text never says the word, it just writes the call. Node 9: the CLEAR DECLINE line `call universal_router intent="info_pivot", called_number, caller_id, return_node="9"`, the routing-table cell `info_pivot with return_node="9"` and the three SMS cells `send_details_to_caller payload detail_type="address"`. Node 1: the Signal 2B examples `intent="cancel_intent", reschedule_mode="true", practitioner_preference="Alex"` / `family_member_name="Fran Mitchell"` / `call universal_router intent="cancel_intent" with reschedule_mode="true" in the same turn` (templates A/C/D, `_b_disambig()` and four hand-written DISAMBIGUATION blocks in `scripts/generate_node1.py`, the_rehab_podiatrist's patch). Real traffic: 2 of the 5 root-field calls in 30 days were Node 9 following its own line (`return_node`, 09-10 and 09-14). `detail_type` is not in `_KNOWN_PAYLOAD_ONLY_FIELDS`, so a root-level `detail_type` is not even rescued and the backend defaults it to "address".
**Fix:** one shape wherever a call is written: `intent="X", called_number, caller_id, payload={...}` (Node 9 table cells: `intent="X", payload={...}`). Only lines that WRITE a call were rewritten. Descriptive shorthand stayed (`Reschedule requests use intent="cancel_intent" with reschedule_mode="true"` directly above the explicit `payload: {...}` template, Signal 0 CASE C, `→ wrap_new_known, booking_for="other"` examples): 33 of 33 literal-following answers on those nested correctly.
**Measured (local Haiku agents):** a schema-aware pack (tool described by its real parameters, `--real-tool-schema`) cannot see this defect: 138 old-text answers, 0 with a parameter beside intent. A literal-following pack (the agent is told only "write the call exactly the way your instructions write it") does: Node 9 old text 6 of 6 root-level `return_node`, new text 0 of 6 (0 of 47 across every new-text literal answer). Node 1's old examples were NOT copied (Part 2's explicit `payload: {...}` template outranks them), so the Node 1 change is hygiene with no measured behaviour change.
**Traps:** (1) one Haiku agent answering ten scenarios in a row keeps a habit: 3 of 4 `info_pivot` calls dropped `return_node` inside one agent, 0 of 6 across six independent agents on the same text — judge a wording with at least two independent agents per scenario (`--per-agent 3`), never one batch. (2) A Node 1 scenario naming a practitioner the clinic does not have trips Template B/E's PRACTITIONER VALIDATION ("our practitioner is X — did you mean ..."); use the clinic's own practitioner. (3) `send_details_to_caller payload detail_type=...` in a table cell made the agent call a TOOL named send_details_to_caller (3 of 3 in one sample): name the universal_router intent explicitly. Record: `docs/in-progress/node9_node1_payload_scope_2026_09_21.md`. Contract: `tests/test_node9_node1_payload_scope_contract.py`. Batteries: `tests/node_payload_scope/`.

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

### CONFIRM_SERVICE FILLER OVERRIDE — system prompt conflict
**Bug (Palm Beach audit, 2026-07-21):** System prompt TOOL-CALL FILLER mandates one filler phrase before every tool call. CONFIRM_SERVICE SILENT RULE says zero spoken output. Under call pressure Haiku defaults to the system prompt's general rule and adds filler before confirm_service — protocol violation.  
**Fix:** CONFIRM_SERVICE SILENT RULE must include an explicit OVERRIDE clause suspending the system prompt filler rule:
```
CONFIRM_SERVICE SILENT RULE: Any turn that calls universal_router with intent="confirm_service" is a tool-call-only turn. Apply OUTPUT VALIDATION: strip ALL planned spoken text from this turn before sending. HALT immediately after the tool call. Zero spoken output means zero — no preamble, no acknowledgement, no filler. OVERRIDE: this rule OVERRIDES the system prompt TOOL-CALL FILLER for confirm_service calls. The system prompt filler rule is suspended when intent="confirm_service" — no filler phrase is added, not even "One moment." This is the highest-priority rule for this turn type.
```
**Required position:** In `## MINI-FRAMEWORK`, immediately before or after the CONFIRM_SERVICE CALL FORMAT block. Not in an escape route — in the framework rules evaluated every turn.

### PRACTITIONER-ONLY PATH — explicit two-step SEQUENCE required
**Bug (Palm Beach audit, 2026-07-21):** "Use PRAC_VARIANT template instead of standard VARIANT where the branch asks a variant question" is ambiguous. Haiku can interpret PRAC_VARIANT as replacing the service selection question rather than the gate question inside the branch, reversing the intended order.  
**Fix:** Replace any "use PRAC_VARIANT where branch asks variant question" phrasing with an explicit two-step SEQUENCE:
```
SEQUENCE — two explicit steps, in order:
STEP 1 (service question first): Store practitioner_preference = [matched name]. Ask which service:
  Ask (SELF) "We offer [MENU_LIST]. Which were you after with [first_name]?" (OTHER) "Which of those were they after?" HALT. Spoken turn only — zero tool calls. Wait for caller to name a service.
STEP 2 (once service is known from caller's answer): Enter that category's branch normally. At the branch gate question (new/existing check), replace VARIANT_SELF with PRAC_VARIANT_SELF and VARIANT_OTHER with PRAC_VARIANT_OTHER. All other branch logic (sub-type detection, TURN 1/2 GUARD, routing) follows as normal. Carry practitioner_preference in the confirm_service payload (except for room-resource services — see below).
PRAC_VARIANT replaces VARIANT at the gate question step only — it does NOT replace the service question (STEP 1). PRAC_VARIANT is never asked before the caller has named a service.
```
**Key:** STEP 1 must say "HALT. Spoken turn only — zero tool calls." Without this, Haiku may combine the service question with a tool call on the same turn.

### MENU_LIST OUTPUT HARD RULE — verbatim output, zero preamble
**Confirmed live fleet-wide** (`nodes/node2_templates/node_2_a_category.txt` and siblings):
```
MENU_LIST OUTPUT HARD RULE: When MENU_LIST fires, output ONLY the MENU_LIST phrase. Zero preamble
— no "I need to ask", "What brings you in", "Could I ask", or any opener before it. Any text
before the MENU_LIST phrase is a protocol violation.
```
**Rule:** never present a list of service categories unprompted — only use MENU_LIST when no
category has been identified yet, and list only top-level category names; sub-type/variant
disambiguation happens later in the branch, not in the menu itself.

### ENTRY SHORTCUT — same-category keyword collision
**Confirmed live:** `nodes/clinics/meraki_holistic_health/node_2_service_resolution.txt` and
`sai_clinic_ta_rabtik_health_london`'s Node 2 both carry an `ENTRY SHORTCUT` — distinct from the
cross-category disambiguation above. Use this pattern when a generic caller term is ambiguous
between a bookable and a non-bookable sub-type *within the same category* (e.g. a generic service
name that could mean either a class or a 1:1 session) — place the shortcut above sub-type
detection so it resolves before the branch's normal flow tries to guess.

### Design-time corollary to NO-DEFAULT RULE
When authoring a new clinic's Node 2 branches, add the disambiguation gate (tier/duration/subtype
question) for every appointment-type split that actually exists in Cliniko — including for the
simplest single-category clinic. Never default to a smaller branch count to reduce authoring
effort; an unasked split becomes a silent-default NO-DEFAULT RULE bug the first time a caller
picks the non-default variant.

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
**Stale as of 2026-06-22:** this block predates the dedicated PRICING QUERY signal added to
`system_prompt.txt` fleet-wide (`5bac7f1`, 2026-06-22). Folding "pricing/cost" into the same
gate as info_pivot silently shadows that later, more specific system-prompt rule — plain
pricing questions get ejected to Node 8 via info_pivot instead of answered inline via
`get_service_price`. This exact contradiction was found independently in
`node_2c_complaint_intake.txt` (Ryde Health) and in the `## RULES` block of 4 clinics' node_2
files (healing_hands_hand_therapy, yandina_podiatry, speeding_health,
intuitive_health_and_wellness) — all four likely trace back to this template. Use the carved-out
version below for any new node; the old one-liner should not be copied again.
```
INFO QUERY GATE: If caller asks about duration, location, address, or hours — speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router intent="info_pivot", called_number, caller_id. HALT.
CRITICAL: Never answer location or address questions inline, even if business_name or confirmed_location is already in context.
Plain pricing, cost, or fee questions are NOT part of this gate — they are handled by the system prompt's PRICING QUERY block instead (calls get_service_price directly, stays in this node). Only route price+duration combined asks or coverage-conditional pricing (EPC/Medicare/NDIS/insurance) here, per the system prompt's own PRICING QUERY carve-outs.
(Exception: "what services do you offer?" is answered inline via ESCAPE ROUTE 5A.)
```
Also scope smart_router in TOOL ROLES: "smart_router — fetches availability data ONLY (never for pricing, service info, or non-availability queries)."

### ESCAPE ROUTE HARD RULE (FRAMEWORK section)
```
ESCAPE ROUTE HARD RULE: When any escape route fires, speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router IMMEDIATELY. CRITICAL: leave system__message_to_speak EMPTY — the filler phrase is the spoken response content, not a tool parameter; any text placed in system__message_to_speak counts as additional spoken output heard by the caller.
```
Do NOT write this rule as "Zero spoken output" — the shared system prompt mandates a filler phrase before every tool call (see "CONFIRM_SERVICE FILLER OVERRIDE" below and the fleet-wide sweep, 2026-07-21). "Zero spoken output" directly contradicts that mandate unless the specific intent has its own explicit OVERRIDE clause (see CONFIRM_SERVICE SILENT RULE pattern below).

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

### DAY MISMATCH must offer the waitlist for the originally-requested day in the same turn
**Bug (fixed and live-patched fleet-wide, 2026-09-18):** the DAY MISMATCH branch (fires when a
caller names one specific day and the search result has slots on a different day) offered the
alternate day but never mentioned the waitlist for the day the caller actually wanted, even for
`waitlist_enabled="true"` clinics — the waitlist was only reachable generically, after the caller
declined every alternate, via EXHAUSTED OPTIONS. **Fix:** DAY MISMATCH now stores the original
day as `requested_day_unavailable` and offers the waitlist for it in the same turn as the
alternate, not gated behind a decline; `WAITLIST REQUEST`/`EXHAUSTED OPTIONS`'s own `waitlist_add`
payloads fall back to `requested_day_unavailable` when `confirmed_day` isn't set. Shipped across
all 4 P1–P4 slim templates and regenerated to all 32 clinics. **Unaudited sibling gap:**
MULTI-DAY SLOT OFFER and SUMMARY's own day-list paths were not touched by this fix and may have
the identical "alternate offered, no same-turn waitlist mention" shape — check them first if a
similar complaint surfaces.

### A hand-maintained `OPERATING DAYS:` override has nothing keeping it in sync
Two clinics (`shire_osteopath`, `yandina_podiatry`) carry a hand-written `OPERATING DAYS:` string
in their Node 3 file. Nothing keeps that string synced to the clinic's real
`practitioner_schedules` rows or to the clinic's own KB — cross-check both whenever a clinic has
one, rather than trusting the override string as ground truth (a stale one caused Yandina's own
Friday-availability bug, fixed 2026-09-18 — see `project_operating_days_override_yandina_friday_fix_2026_09_18` in memory).

### PRACTITIONER LIST REQUEST — trigger and exclusion must not overlap in phrasing
**Bug (fixed and live-patched fleet-wide, 2026-09-18):** the P2/P3 `PRACTITIONER LIST REQUEST`
route's own positive trigger examples included "is [name] working [day]?", while its "NOT this
route" exclusion said naming one specific practitioner is never this route "even when a service
or day is also named" — a direct self-contradiction that could skip a real availability search.
**General lesson:** whenever a route lists concrete trigger examples (per the "concrete beats
vague" principle elsewhere in this doc), cross-check those same examples against that route's own
exclusion clause for phrasing overlap — a positive example that also matches the negative
exclusion is a live bug, not just a style nit.

### Discovery/escape routes inherit locked defaults unless given their own explicit field list
A route described as "same params as step N" silently inherits step N's locked state — e.g. a
practitioner-agnostic discovery question inheriting a locked `practitioner_id`, or a stale
`appointment_type` name outliving the `appointment_type_id` it was locked to. **Fix:** give the
route its own explicit field list with a LOCK/omission rule as the first line of its body, plus a
header tag naming what it does and does not carry forward — this is the Qwen `TOOL LOCK` pattern
(`.claude/rules/qwen-prompt-patterns.md` Rule 9), confirmed to transfer to Haiku nodes too, not
just Qwen ones.

---

## Node 6 — Name Collection (Haiku-slim, experimental — see `.claude/rules/node6-haiku-slim-design.md`)

### "Already known" checks must cover both name sources, not just the DV-lookup pair
**Bug (round-1 self-audit, 2026-08-04):** a NAME step's "already known, skip collection" check
tested only `{{caller_first_name}}`/`{{caller_last_name}}` (the confirmed-CRM-record pair) and
never checked `{{patient_name_raw}}` (the raw name captured earlier in the same call, e.g. at
the greeting node, before any CRM lookup). Scenario probes that set `patient_name_raw` alone
still passed — but only because the caller's own message in those scenarios happened to restate
the name in text, giving the model an alternate path to the right answer that didn't actually
exercise the DV-check branch. A scenario with `patient_name_raw` set via DV only and *zero*
name mention in the caller's current message (`PNR1` in the scenarios file) is what actually
proves the branch exists.
**Fix:** any "is this field already known" check with two possible sources (a confirmed
DV-lookup pair vs. a raw-captured single field) needs an explicit branch for each source, not
just the one that happens to be top-of-mind while drafting — and the regression scenario for it
must withhold the other source (no textual restatement) or it doesn't actually test the branch.
**Detection:** this class of gap surfaces in stumbling points, not scenario failures — the audit
model can flag "the written rule doesn't explicitly cover source X" even when every existing
scenario coincidentally passes anyway. Treat a stumbling point about an unhandled data source as
actionable even at a 100% scenario pass rate; don't dismiss it just because nothing failed.

### EMAIL collection pattern set (confirmed live, `nodes/shared/node_6a_name_collection_self.txt` §3)
Independently confirmed against the current live file:
- **Spoken→written assembly + confirmation:** last names are always spelled back
  letter-by-letter uppercase ("S, M, I, T, H — is that right?"); email confirmation escalates to
  anchor-word letters on a retry that doesn't land the first time.
- **Ambiguous decline needs its own question:** "just message me"/"text me instead" is a distinct
  outcome (`EMAIL-CAPTURE-VIA-SMS`) from a plain decline — it routes through a `MOBILE CHECK`
  gate before the booking payload gets `email_capture_requested: true`; a plain decline never
  sets that field.
- **A full restatement replaces, it doesn't merge:** correcting an already-confirmed field
  overwrites it and re-applies the same confirm judgement, then resumes wherever collection had
  reached — never re-asks a field already resolved before the correction.
- **Two failed attempts → offer to skip, not a forced third ask:** "two replies in a row [that
  are] neither a usable address nor a clear decline" offers to skip instead of asking again; a
  third failed correction attempt on an already-partially-collected address gets the same offer.
- **Name/email correction economy (NAME CROSS-CHECK, once email is confirmed):** a same-sounding
  1–2 character mismatch that reads like an ASR slip (stored "Jukes", email spells "Dukes") is
  silently corrected to the email's spelling, no question asked; a 3+ character or
  no-real-resemblance mismatch gets an explicit disambiguating question instead.

### A call-init-only DV needs to name its own provenance in its own gate
**Confirmed live** in `kynd_psychology`/`morgana_walker_psychology`'s per-clinic `node_6a` forks
(their `RETURNING ATTENDEE CHECK` section, gated on `{{previous_attendee_names}}`): the gate
explicitly states the DV "is a real appointment-history lookup done at call start, not something
the caller's own words this call ever set" — a caller saying "my partner" or naming a companion
earlier in the same call does NOT put a value into that DV and does NOT satisfy the gate. **Why
this matters generally:** any DV that's only ever populated at call init (never by anything the
prompt itself sets mid-call) needs this same explicit provenance statement in whatever gate reads
it — otherwise the model can conflate "the caller said something conceptually similar" with "the
DV has a value," especially under a busy multi-condition `EVALUATE FIRST` list like this one.

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

### Node-local escape routes silently absorbing a more specific system-prompt rule
**Bug (found 2026-08-04):** INFO PIVOT ESCAPE listed "pricing" as a trigger example
("purely informational question... (pricing, address, hours, ...)"). This pre-dates the
dedicated PRICING QUERY signal in `system_prompt.txt` (see stale INFO QUERY GATE note under
Node 3 above) — plain pricing questions were silently ejected to Node 8 via `info_pivot`
instead of answered inline via `get_service_price`. Same session also found CANCEL / RESCHEDULE
ESCAPE's trigger included "...or check an existing appointment", which shadows the system
prompt's separate PATIENT APPOINTMENT LOOKUP (`intent="details"`) — a caller who only wants to
confirm a time got routed into the cancellation node instead of getting an inline answer.
**Fix:** remove "pricing" from INFO PIVOT ESCAPE's example list and "or check" from CANCEL /
RESCHEDULE ESCAPE's trigger; add one positive line to each pointing at the correct inherited
tool/intent instead of just deleting the wrong path. General lesson: when a node-local escape
route's trigger list was written before a more specific system-prompt rule existed, the local
list can silently swallow cases that rule was meant to own. Worth a quick check any time a new
system-prompt-level signal is added — grep existing node escape routes for the same trigger
words.

---

## Silent routing patterns

LLMs have a strong "polite instinct" — they want to say "Let me help you with that" before tool calls. Two places speech leaks:
1. Agent spoken output (message field) beyond the mandated filler phrase — over-speaking, not under-speaking, is now the risk to guard against (see TOOL-CALL FILLER OVERRIDE note below)
2. `system__message_to_speak` parameter inside the tool call — EL evaluator treats this as heard speech even if message field is empty

**Fleet-wide correction (2026-07-21):** every escape route below used to be written as "zero spoken output" / `OUTPUT: [silent]`. This directly contradicted the shared system prompt's TOOL-CALL FILLER rule, which mandates one filler phrase ("One moment." / "Just a sec." / "Let me check that.") before every tool call — including escape routes — to mask the processing gap. All non-`retired` node files were swept to replace "zero spoken output" escape routes with the filler-phrase pattern below. The only calls that stay genuinely silent are ones with an explicit `OVERRIDE:` clause suspending the system prompt's filler rule (see CONFIRM_SERVICE SILENT RULE below) — never write a new "silent" rule without that override, or the system prompt's blanket mandate wins under call pressure and the rule is not actually silent.

### MINI-FRAMEWORK HARD RULE (add to any node with escape routes)
```
ESCAPE ROUTE HARD RULE: When an escape route fires (cancel_intent / info_pivot / wrap_up / etc.), speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router IMMEDIATELY. DO NOT say anything else before or after the filler phrase. CRITICAL: leave system__message_to_speak empty or omit it — the filler phrase is the spoken response content, not a tool parameter; any text placed in system__message_to_speak counts as additional spoken output heard by the caller.
```

### Per-route filler-phrase format
```
1. CANCEL / RESCHEDULE ESCAPE
Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router intent="cancel_intent", called_number, caller_id.

2. INFO PIVOT ESCAPE
Speak one filler phrase from the TOOL-CALL FILLER set, then call universal_router intent="info_pivot", called_number, caller_id.
```

### EL evaluator success condition phrasing
For tool-call turns that speak only the mandated filler phrase:
- ✓ **WORKS:** `"EVALUATOR NOTE: a response containing ONLY one TOOL-CALL FILLER phrase, combined with a universal_router tool call, is the CORRECT behavior here — count this as a PASS. Any additional spoken content beyond the single filler phrase is a FAIL."`
- ✗ WEAKER: `"EVALUATOR NOTE: filler phrase + universal_router tool call = PASS."`
- For calls with a documented OVERRIDE (e.g. confirm_service) that must stay genuinely silent: `"EVALUATOR NOTE: an EMPTY agent response combined with a universal_router tool call is the CORRECT behavior here — count this as a PASS."`

---

## Handoff and escape-route risk under guide-style conversion

Handoffs and escape routes (transfer to human, booking-tool handoff, info-pivot detour) are the
single highest-risk category when converting a node from strict machinery to loose, narrative
guide-style prose (`docs/guide-style-conversion-blueprint.md`). The strict machinery
(BLOCKING SIGNAL, MANDATORY PART 1/2, OUTPUT CONTRACT) exists specifically to suppress two things
guide-style's own conversational register re-introduces by design: talking more than intended,
and drifting off a mandated silence under conversational pressure. Losing the structural
constraint doesn't remove the underlying LLM prior — it just removes the thing that was holding
it back. Treat every handoff/escape route in a guide-style draft as needing the same runtime
behavior as the strict version, expressed as a positive instruction rather than a MINI-FRAMEWORK
block (see §5 of the blueprint), and test it explicitly rather than assuming loose prose that
"reads fine" preserves it.

### Failure mode 1 — the filler-only turn breaks into over-talking
**Risk:** in strict machinery, a handoff turn is forced to be exactly one filler phrase (see
"Per-route filler-phrase format" above) plus the tool call, nothing else. Guide-style prose that
merely *describes* the handoff ("let the caller know you're connecting them, then transfer")
gives the model room to pad: `"Sure, I can help you transfer. Let me get that sorted for you.
Please hold on while I connect you."`
**Why it breaks the system:** extra spoken text on a handoff turn can delay the tool call's
execution, cause audio overlap with the transfer/booking action, or violate the output contract
the orchestrator expects for that turn.
**Fix:** the guide-style instruction must still name the exact filler phrase (or the node's
approved filler set) and state explicitly that it is the *only* spoken content for that turn —
not "say something to reassure the caller before transferring." Loose register describes *what*
to do; it must not loosen *how much* gets said on a handoff turn.

**Concrete template** (adapt the phrase and tool name to the node's own approved filler set —
this is the shape to copy, not literal text to reuse verbatim; see Failure mode 4 below for why
the tool call line must also name its own parameters, not just describe "trigger the tool"):
```
When transferring the caller to a human agent, your only job is to say a single short phrase
to keep them warm (use: "Let me get someone to help you with that.") and immediately call
transfer_to_number with transfer_number={{transfer_number}}, client_message set to that exact
same phrase, and agent_message set to a one-line reason for the receiving human (e.g. "Caller
requested to speak with clinic staff."). Do not add any extra polite phrases, do not explain the
transfer process, and do not speak after the tool call is initiated.
```
This works because it does four things a vaguer instruction skips: names the exact phrase
(not "something reassuring"), states the phrase count is one, explicitly forbids the two places
padding creeps in (before the tool call and after it) rather than only warning against padding in
general, and names the actual tool call shape — including both of `transfer_to_number`'s own
message parameters — rather than leaving "trigger the transfer tool" to the model's guess.

### Failure mode 2 — the genuinely-silent turn erodes under pressure
**Risk:** some escape routes require zero spoken output (see CONFIRM_SERVICE SILENT RULE /
FILLER OVERRIDE above). A guide-style draft that just says "transfer silently" or "hand off
without speaking" is not enough — under conversational pressure an LLM's helpfulness/politeness
prior is strong enough to override a bare silence instruction and add a stray "Okay!" or "One
moment" anyway, exactly like the strict-prompt version of this bug did before the explicit
OVERRIDE clause was added.
**Fix:** a guide-style silent turn needs the same explicit, scoped override this file already
documents for strict machinery — state plainly that this specific call type suspends the
general filler-phrase expectation, not just that it "should" be silent. A silence claim with no
override statement should be treated as unverified until tested (see the adversarial test below).

### Failure mode 3 — info-pivot detours don't resume, they loop
**Risk:** this is the same underlying bug as INFO PIVOT RETURN (Node 2, above) and the Node 2C
"Node-local escape routes silently absorbing a more specific system-prompt rule" entry, but it
recurs specifically in guide-style drafts because loose prose is more likely to describe the
detour ("answer their question, then continue booking") without stating the resumption rule
precisely. Caller asks a side question mid-flow (pricing, location) → model correctly answers it
→ instead of resuming the main flow at the next caller turn, the model repeats the informational
tool call, re-asks a question the caller already answered before the detour, or stalls.
**Fix:** state explicitly that once the detour is answered, the model evaluates the caller's next
message fresh against the main flow — never replays a prior tool call from history, and never
treats the detour as having consumed a step of the main flow it didn't actually answer.

### Failure mode 4 — the warm phrase drifts from the tool's own message parameters
**Risk (found via external LLM review, 2026-09-19 — see below):** a handoff instruction that only
tells the model to "say a phrase and trigger the tool" describes the spoken line as free-floating
agent output, when the live `transfer_to_number` tool actually takes its own `client_message`
(the text voiced to the caller during transfer) and `agent_message` (context for the receiving
human, never spoken) parameters — confirmed against this repo's only live transfer pattern,
`nodes/shared_agent_transfer/system_prompt.txt`'s TRANSFER TO CLINIC block (also mirrored in
`nodes/clinics/intuitive_health_and_wellness/node_8_information_handler.txt`). An instruction that
never names these parameters risks the model calling the tool with `client_message`/`agent_message`
empty, or with text that has drifted from the spoken phrase — the two must match, and
`agent_message` needs its own one-line content.
**Fix:** name the exact tool call shape, not just "trigger the tool" — see the corrected
`transfer_to_number` line in Failure mode 1's Concrete template above.
**Provenance:** this was caught by asking an external model to critique the plain "Concrete
template" text (framed explicitly as text-under-review, not an instruction to follow — the
review-framing pattern from [[feedback_guide_style_node_method]] applied to a single paragraph
rather than a whole node). It was one of several claims returned alongside some that did NOT
hold up — see the reviewer-uniformity caution in `docs/guide-style-conversion-blueprint.md` §8
before trusting an external critique pass at face value.

### Adversarial test additions for handoff/escape-route conversions
These extend `docs/guide-style-conversion-blueprint.md` §6.3 (Universal silent-routing/filler
tests) — run them against any guide-style draft with a handoff or escape route, in addition to
the node-specific battery in §6.1/6.2:

- **Filler-only turn test:** trigger the handoff. Verify spoken output is exactly one approved
  filler phrase, `system__message_to_speak` is empty or omitted, and nothing else is said before
  or after — same test as §6.3, restated here because it's the single most common guide-style
  regression.
- **Genuinely-silent turn test:** trigger a call type the draft claims is silent. Verify the
  actual output has zero spoken content — don't accept the draft's own claim of silence without
  running this, since the failure mode above is exactly a model overriding that claim under
  pressure.
- **Interrupt-during-handoff / pressure test (new):** simulate the caller interrupting or
  reversing course at the exact moment the handoff would fire — "wait, don't transfer me yet",
  "actually hold on", talking over the filler phrase. Verify the model does not fire the tool call
  with stale or dropped parameters, does not silently proceed with the transfer against the
  caller's just-stated reversal, and does not abandon required fields mid-transition — it either
  completes the handoff correctly or cleanly aborts back into the main flow, never a half-state.
- **Info-pivot resume test:** mid-flow, ask an info/pricing/location question the node answers
  inline, then continue the original flow with the caller's next message. Verify the model
  evaluates that next message fresh — no repeated tool call, no re-asked already-answered
  question, no stall.

---

## No price in duration question

Never include price in a duration selection question. Ask "45 or 60 minutes?" not "45 minutes ($135) or 60 minutes ($179)?".

**Where it applies:** Any Node 2 duration gate — Remedial Massage initial (45/60), Myotherapy initial (45/60), Remedial Massage existing (30/45/60/90), Myotherapy existing (30/45/60). Price is answered only if caller asks (INFO PIVOT).

---

## "How much are they all?" — whole-category price asks

A caller answering a duration question with "how much are they all?" must get every price in one
turn. Two things make that work, and both were broken until 2026-09-09:

1. **The backend expands the duration family, the prompt never enumerates it.** A price ask sends
   ONE `appointment_type_id` (or a plain service name) plus `all_durations: "true"`;
   `tools/service_families.py` groups the clinic's catalogue by a duration-independent name key and
   returns every sibling. Never instruct a node to call the price tool once per duration — it
   reliably calls it once and invents the rest.
2. **Never ask a node to format the array itself.** The tool returns a pre-composed
   `spoken_summary` ("60 minutes is $160, 75 minutes is $190, and 90 minutes is $220.") — the node
   speaks that verbatim. Every version that asked the LLM to build the sentence from `prices[]`
   produced a real price for the variant it looked up and a fabricated or evasive answer for the
   rest ("for the 75, 90, and 120-minute options, check directly with the clinic" —
   conv_8301m229bngcee9rp8528dqjch0v).

**Node 8 trap:** its PRICING AND DURATION INTERCEPT STEP 1 asks the caller to pick a duration when
several variants exist. That clarification must be gated behind an ALL-OPTIONS check, or a caller
asking about all of them is bounced back to picking one.

**Never tell a node to speak the tool's `note` field.** It is an instruction addressed to the
assistant, not caller-facing text; the shared system prompt said "speak `note` field verbatim" and
would have read the instruction aloud.

**When `spoken_summary` comes back empty:** `tools/service_families.py`'s `compose_spoken_summary`
returns `""` when every candidate entry has a null price (confirmed via its own docstring: "an
unpriced variant is worse than silence — the agent would say 'None'"). The node's own can't-
retrieve fallback line handles that case — it is NOT a signal for the node to invent or re-derive
a summary itself. Null/unpriced entries are dropped before composition; never read a bare "None"
aloud for one.

### OPENER RULE — fleet-wide example phrases get recited literally, ignore clinic facts
**Bug (fixed live, 2026-09-18 — commit `0ee2edcd`):** the shared system prompt's `OPENER RULE`
listed "Sure thing — which location works for you?" as a generic warmth-phrase example. A
single-location clinic's own Node 3 explicitly says location is fixed and never asked — but the
model recited the fleet-wide example phrase verbatim anyway, mid-call, confusing the caller.
**Lesson:** any fleet-wide example phrase in the shared system prompt must stay clinic-agnostic —
don't use a real question type (location, a specific service name, a specific gate) as an
illustrative example, since some clinic's own node will have already ruled that exact question
out. Same commit also fixed the P2/P3 `PRACTITIONER LIST REQUEST` self-contradiction documented
under Node 3 above — both bugs were found from the same live call
(`conv_5101m2ta1d1ne4pvvzb6p2pt7v0n`, Feel & Heal).

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

**4. Stale scenario fixtures after a fleet-wide rule change**
Risk: a shared-prompt-wide rule change (e.g. the OPENER RULE fix above) can leave
`*_scenarios.json` files asserting the OLD rule's behavior — they then false-fail (or worse,
false-pass) once the prompt is correctly updated, even though no node `.txt` is at fault.
Check: grep every `*_scenarios.json` in scope for the old rule's language in the same session as
any shared/system-prompt-wide change.
Fix rule: update or remove the stale scenario assertions alongside the prompt fix, not as a
separate later cleanup.

**5. A hard ceiling exists — not every failure is a wording problem**
Risk: assuming one more wording/placement/idiom variant will fix a failure that has already
survived 2–3 escalating attempts, including an idiom this doc documents elsewhere as normally
reliable for the node's model (see `feedback_haiku_prompt_length_ceiling_wording_fixes_dont_help`
in memory — Physio Cure's Node 3 survived 5 escalating fixes at ~40K combined prompt tokens; a
forced step-by-step audit-model walkthrough proved the rule was parseable and correct, and the
real cause was recency-weighted conversational context beating a large prompt, not unclear
wording).
Check: has this exact failure shape survived 2–3 different wording/placement/idiom attempts
already?
Fix rule: stop iterating on wording. Do a forced step-by-step walkthrough with the audit model to
confirm the rule is even parseable, then escalate to a non-wording lever — shorten the overall
prompt, raise the node's LLM tier for the affected pattern, or move the guard server-side so it
doesn't depend on the model following the instruction at all.

---

## Haiku instruction-following — what works and what breaks

> **Current Haiku-LLM nodes (verify against CLAUDE.md's Node LLM map before trusting this list,
> it changes on migrations): Node 1, 2, 3 (slim P1–P4), 6a, 6b, 9.** Node 6c and 7b are
> `gemini-2.5-flash`, Node 7 is `gpt-5.4-mini`, Node 8 is `gpt-4.1`, Node 11 is `qwen35-397b-a17b`
> (see `.claude/rules/qwen-prompt-patterns.md`). Do not port Haiku-specific wording idioms
> (MANDATORY PART framing, BLOCKING SIGNAL, OUTPUT CONTRACT) to a non-Haiku node without checking
> the model actually needs/supports them — gpt-4.1 and gpt-5.4-mini in particular have their own
> failure modes (see the Node 8 and gpt-5.4-mini notes below).

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

---

## gpt-5.4-mini caution — do not port Haiku gate machinery without testing

`reasoning_effort` is set **agent-wide in ElevenLabs, not per node** — confirmed absent from a
per-node `conversation_config.agent.prompt` override object via direct API pull. At the fleet
default of `low`, `gpt-5.4-mini` does not reliably execute MANDATORY-gate/BLOCKING-SIGNAL
instructions ported straight from a Haiku node — KYND Psychology's gpt-5.4-mini pilot
(nodes 1, 2, 3, 6a, 6b, 9) self-audited at Node 1 18→58/100, Node 2 23→42/100, Node 3 34→38/100 —
far below the ~100 bar this repo normally requires before shipping
(`.claude/rules/node-edit-verification.md`). Raising reasoning tokens fixed the gate-skips but
measurably slowed every other gpt-5.4-mini node sharing that same agent, since the setting isn't
scoped to one node. Node 7's own shared file (`nodes/shared/node_7_cancellation_handler.txt`,
`gpt-5.4-mini` fleet-wide since 2026-09-15) holds up only because it barely uses BLOCKING-SIGNAL
machinery to begin with — incidental, not a tested design choice. **Test any MANDATORY/BLOCKING
port to a gpt-5.4-mini node with a real self-audit before shipping; prefer a backend-side guard
over prompt machinery when a gate must be airtight on this model.** See
`project_kynd_gpt54mini_pilot_reasoning_effort_2026_09_14` in memory for the full pilot writeup —
note that memory also found a live-vs-git discrepancy (nodes marked "NOT yet live-patched" in
their own commit messages were in fact live), so verify via a direct API pull, not commit
messages, before trusting any "not yet live" claim for this pilot.

---

## Node 1 — Entry / Greeting Router

### SINGLE-PRACTITIONER FACT — single-practitioner clinics need an explicit grounding fact
**Bug:** a bare booking request with no practitioner named, at a single-practitioner clinic
(Template D `node_1_single_appointment.txt` / Template F `node_1_single_appointment_psych.txt`),
can produce a nonsensical practitioner-preference question ("do you have a practitioner
preference, or would anyone be fine?") when there is only one practitioner to see.
**Fix (live in both templates and in `bob_ward_physio`/`morgana_walker_psychology`'s per-clinic
Node 1 files):** a `SINGLE-PRACTITIONER FACT` line stating the clinic's one practitioner name and
explicitly forbidding the preference question — a negative-only prohibition wasn't reliable on
its own without a positive grounding fact to anchor it to, the same shape as several Node 2/3
NO-DEFAULT-style bugs elsewhere in this doc.

### AI CAPABILITY REDIRECT — fleet-wide, but its trigger list has no bare-continuity exclusion
`AI CAPABILITY REDIRECT` (fleet-wide across every clinic's Node 1 plus every `node1_templates/*`
file) fires on phrases expressing uncertainty about who the caller has reached, including bare
"is anyone there?"/"are you real?"-style phrases. As written, its trigger list has no carve-out
for a caller checking call continuity after a barge-in (a bare "Hello?") who then states a real
request in the same or next turn — a plausible false-fire path, not yet confirmed reproduced live.
**Recommended fix, not yet applied:** a caller's substantive request in the same turn as (or
immediately after) a bare continuity check should route normally instead of re-triggering the
redirect; a standalone "Hello? Is anyone there?" with nothing else should still fire it. Flagged
for a targeted session — this is a logic-affecting change and needs the standard node-edit
verification loop (`.claude/rules/node-edit-verification.md`) before shipping, not a quick edit.

---

## Node 6c — Family Booking Confirm

### Hand-maintained forks can silently omit gates the shared file has
Node 6a/6b/6c have **no generator** — a per-clinic fork (`nodes/clinics/<slug>/node_6c_*.txt`) is
a hand-copy of `nodes/shared/node_6c_family_booking_confirm.txt`, not a templated regeneration, so
nothing keeps it in sync automatically. Confirmed live gap: `village_remedies`'s own
`node_6c_family_booking_confirm.txt` fork has no `WAITLIST OFFER FOLLOW-UP` and no
`CONSTRAINT PIVOT ESCAPE` handling, both present in the current shared file. **When auditing any
Node 6a/6b/6c fork, diff its structure against the current shared file's equivalent sections —
don't just check the fork for internal self-consistency.**

---

## Node 7b — Rescheduler

### Cross-turn guard DVs must sit outside the routing-flag reset set
A same-conversation "did the real cancel actually happen" guard DV
(`cancellation_completed`, used in `nodes/shared/node_7b_rescheduler.txt`'s book-first reschedule
flow) needs to survive an intervening successful tool call (e.g. an availability search) without
being swept up in an unrelated routing-flag reset — otherwise a caller can abandon a book-first
reschedule mid-flow while the OLD appointment is still live, with the agent implying it was
already cancelled. **Pattern:** dedicate a DV for this kind of guard, explicitly excluded from
any routing-flag reset set, and set it on both the true and false branch of the action it guards
so it self-corrects without manual clearing.

### A schema-documented intent is still callable even when a node's own prompt never mentions it
`universal_router`'s shared tool schema documents intents (e.g. `waitlist_add`) that a given
node's own prompt text may never reference. A caller asking for something mid-flow that matches
an undocumented-in-this-node intent can get the LLM to improvise the call straight from the
schema, skipping that node's own guards (e.g. Node 7b's cancel-guard above) and omitting fields
the improvised call never knew to set. **Whenever a new `universal_router` intent is added
anywhere in the fleet** (see the "Adding a new router intent" checklist in `CLAUDE.md`), check
every node carrying the tool for whether it needs its own explicit signal for that intent — a
schema-level enum entry does not by itself make an intent safe to reach from every node.

---

## Node 8 — Information Handler

### TOOL RESTRICTION directly contradicts this node's own mandatory tool calls (live bug, unfixed)
`nodes/node8_templates/node_8_template.txt` line 21, inside a block marked "absolute — evaluate
before all other rules," states: `smart_voice_agent does not exist in this node and cannot be
called here under any circumstances.` Line 58's "Permitted tool roster" and three mandatory call
sites (`update_contact_detail` at line 137, and the pricing/duration and practitioner-availability
intercepts around lines 239/262) all require calling `smart_voice_agent`. Risk: `gpt-4.1` reads
the absolute prohibition first and silently breaks those flows under call pressure. **Fix (not yet
applied — flagged for a targeted session, needs the standard verification loop):** remove
`smart_voice_agent` from the TOOL RESTRICTION's prohibited list, or scope the restriction to name
only tools genuinely never used in this node.

### GPT-4.1 instruction-following — companion to the Haiku section above
`gpt-4.1` applies global/FRAMEWORK/CRITICAL-REMINDERS-level directives OVER step-level
conditionals when they conflict (first found on Node 3 before its 2026-07-20 migration off
`gpt-4.1`; Node 8 is now the fleet's only node still on this model, so the pattern is directly
relevant here). Fix pattern: (1) count/state-check FIRST at the step level ("Count the elements
FIRST. Branch strictly on count:"); (2) explicit DO-NOT exclusion on the exception branch ("1
slot — DO NOT apply X"); (3) flip blanket "MUST" reminders to conditional phrasing ("ask ONLY when
[condition]"). Separately, an OUTPUT CONTRACT prohibition must name the exact forbidden phrase,
never a blanket "any other text" — `gpt-4.1` applies broad negative rules globally and will
suppress other valid spoken turns (e.g. a legitimate disambiguation question) along with the one
the rule meant to block.

### Currency symbol — not yet handled, flagged as a design gap
The pricing intercept has no region/currency-symbol derivation today (checked directly against
`nodes/node8_templates/node_8_template.txt` — no such logic exists). Every clinic prices in AU
dollars implicitly. This becomes a real gap once a non-AU clinic goes live with Node 8 pricing
questions (see the fleet's first non-AU clinics catalogued in memory) — needs a symbol derived
from clinic region/`country_code`, applied consistently in both the price-only and combined
price+duration sentences.

---

## Node 9 — Wrap-up

### CLEAR DECLINE's exception clause needs a real matching route, not "route it instead"
**Bug (fixed, fleet-patched 2026-09-11):** `CLEAR DECLINE`'s exception — "if it also contains a
new request, route it instead" — had no concrete matching row for a general appointment-prep
question, causing a silent fall-through where the call ended on a trailing genuine question
anyway. **Fix:** widen the routing table to an explicit catch-all row with a real tool-call shape.
**General lesson:** "route to X instead" is a silent no-op under model pressure unless X has an
actual matching row — this applies well beyond Node 9.

### SECURITY-FORCED EXIT — confirmed live, evaluated before every other rule in this node
`nodes/shared/node_9_wrap_up.txt` carries a `SECURITY-FORCED EXIT` block (evaluated before
`ENTRY GUARD`, `CLASSIFY THE REPLY`, and the `GOODBYE-ALREADY-SPOKEN RETRY GUARD`) plus a
`GOODBYE-ALREADY-SPOKEN RETRY GUARD`, both `TOOL LOCK`ed to `end_call` only —
`universal_router intent="wrap_up"` does not end the call and produces a duplicate goodbye if
called from either guard. This closed two gaps: ordinary clarification phrases ("sorry?", "say
again") were miscounted as a security strike, and even a correctly-fired security exit was only a
soft routing intent — a caller who replied immediately after the spoken termination line fell
through to normal routing, contradicting the promise just spoken. **Cross-reference:** this
refines the "Handoff and escape-route risk under guide-style conversion" section above — that
section frames spoken-termination-without-a-real-`end_call` as a risk specific to *loosening*
strict machinery, but this bug shows the strict MANDATORY-PART/OUTPUT-CONTRACT version had the
identical gap. Strict machinery is not immune to this failure mode either.

### GOODBYE ECHO GUARD vs GOODBYE-ALREADY-SPOKEN RETRY GUARD — two related, both live
One guard fires when no caller message arrived since the goodbye; a narrower one fires when a
caller message arrived but only echoes the farewell ("bye") — a farewell-plus-new-content message
("bye, oh wait, one more thing") correctly falls through to normal handling instead of triggering
either guard. Both are `TOOL LOCK`ed to `end_call` only, same reasoning as SECURITY-FORCED EXIT.

### An "edges never fire" report can actually be an intent-vocabulary mismatch
**Bug (fixed fleet-wide, 2026-08-10):** Node 9 emitted `book_intent` where the wiring expected the
`wrap_new_*` intent family — surfaced as "Node 9 has zero outgoing edges" when the real defect was
the emitted intent name, not the edge wiring. **Fix:** before treating a "node never transitions"
report as an edges/wiring bug, confirm the intent string the prompt actually instructs matches
what the edges' forward/backward conditions check for.

---

## TTS Pronunciation Dictionary Patterns

Confirmed live in `scripts/patch_pronunciation_dict.py`'s `CLINIC_PRONUNCIATION_RULES`/
`_PODIATRY_RULES`. Rule-type choice: use `phoneme` (ARPABET) when the mispronounced target still
looks like a real word ("Podiatry", "Cliniko") — an `alias` respelling for a real-word-looking
target gets re-G2P'd by the TTS on top of the respelling, which is unreliable. Use `alias` to
force letter-by-letter/acronym reading ("ADHD" → "A-D-H-D", "EPC", "DVA", "FPES", "NDIS", "WC").
**Update gotcha:** remove the old rule before adding its replacement — the ElevenLabs API doesn't
do this for you. Reuse fleet constants (e.g. `_PODIATRY_RULES`) rather than retyping phonemes
per clinic. **Sync requirement:** any node spelling-out convention for a domain/acronym needs a
matching alias rule — see the EMAIL CAPTURE pattern in the Node 6 section above. **Coverage gap:**
the 3 outbound re-engagement campaign agents (`OUTBOUND_DAYRESCHED_AGENT_ID` etc., not in
`clinic_agent_ids.json` — see `reference_outbound_agent_ids_and_pronunciation_dict` in memory)
are attached to the shared dict via a one-off script, not `CLINIC_PRONUNCIATION_RULES` itself —
any new rule that should reach them needs a manual attach or an `agent_ids_override` entry.

---

## Spoken clinic identity — `custom_name` is live TTS output, not cosmetic

`clinics.custom_name` (falling back through `display_name`/`business_name` — confirmed via
`COALESCE(custom_name, display_name, business_name)` in `tools/twilio_init_webhook.py`) is read
directly into the spoken greeting and in-call references, never mediated by node prompt text or a
pronunciation rule — a typo there is spoken verbatim to every caller with no safety net (see
`project_clinic_name_drift_fix_2026_09_16` in memory for a confirmed real incident). Any new-clinic
build or name audit should read `custom_name` aloud against the verified real business name and
prioritize it over a plain `clinic_name` mismatch, since only `custom_name` is guaranteed spoken
every call. Distinct from Node 2's `LOCATION NAME ALIAS` pattern above, which is routing logic,
not raw TTS output.
