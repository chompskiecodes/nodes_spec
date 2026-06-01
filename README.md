# Node Architecture Reference

## Node map & universal IDs

Every clinic agent uses these same node IDs:

| Node | Universal ID | Label |
|------|-------------|-------|
| 1    | `node_01kbej4q4sf6dbt7vd9f1e03t1` | Entry Greeting Router |
| 2    | `node_01kbej6wqpf6dbt7vs563vxh94` | Service Resolution |
| 3    | `node_01kbemw1axf6dbt7xryxe7gpd7` | Availability Handler |
| 6a   | `node_01kbenaznwf6dbt7ztc7xphbzq` | Name Collection (self) |
| 6b   | `node_01kbenbrd5f6dbt80awydptcbe` | Name Collection (other) |
| 7    | `node_01kbemhx6xf6dbt7wa2hnywer8` | Cancellation |
| 8    | `node_01kbemmcz6f6dbt7ws7b6zk74p` | Information Handler |
| 9    | `node_01kbf348egf6dbt86h6b6ej77d` | Wrap Up |
| 11   | `node_01kbgm46v9fvgv43n0m989n3f0` | Error Recovery |

---

## Canonical LLM map

| Node | LLM | Rationale |
|------|-----|-----------|
| 1 (entry router) | `claude-haiku-4-5` | Consistent HALT/instruction-following with other nodes |
| 2 (service resolution) | `claude-haiku-4-5` | HALT-critical; gpt-4.1-mini fails |
| 3 (availability) | `claude-sonnet-4-5` | All clinics; P1/P2/P3 templates in `node3_templates/`; Haiku hallucinated slot times |
| 6a/6b/6c (name collect) | `claude-haiku-4-5` | |
| 7 (cancellation) | `claude-haiku-4-5` | |
| 7b (rescheduler) | `gpt-5.4-nano` | Migrated 2026-05-29; 10/10 scaffold tests |
| 8 (information) | `claude-haiku-4-5` | |
| 9 (wrap up) | `gpt-5.4-nano` | Migrated 2026-05-29; 12/13 scaffold tests (D1 scaffold artifact) |
| 11 (error recovery) | `gemini-3.1-flash-lite-preview` | Cheapest/fastest |
| 2C (complaint intake) | `claude-haiku-4-5` | |

**LLM path:** `conversation_config.agent.prompt.llm` is authoritative. Writing to `cc.agent.llm` is silently ignored for `override_agent` nodes.

**Temperature:** always set `cc.agent.prompt.temperature = 0.0` alongside the LLM on every node. `audit_node_llms.py` checks this.

---

## Tool assignment per node

Tools are attached **at the node level** via `workflow.nodes.<node_id>.additional_tool_ids`, NOT agent-level.

```
Node 11 (Error Recovery):       [universal_router]
Node 1  (Entry Router):         [async_capture, universal_router]
Node 2  (Service Resolution):   [universal_router]
Node 3  (Availability):         [smart_voice, universal_router]
Node 6a/6b/6c (Name Collect):   [universal_router, smart_voice, async_capture]
Node 7  (Cancellation):         [universal_router, smart_voice]
Node 7b (Rescheduler):          [universal_router, smart_voice]
Node 8  (Information):          [universal_router, smart_voice]
Node 9  (Wrap Up):              [async_capture, universal_router]
```

**Primary tool IDs (use these — never the backup/ghost variants):**
- `universal_router` → `tool_9401k7e4bc90fw7avkmysavqhj91`
- `async_capture_context` → `tool_3101km7k126qezfsqcxdxfdesdd8`
- `smart_voice_agent` → `tool_4501k96qzckzemabz9rwppjms6zj`

`create_new_agent.py` does NOT set `additional_tool_ids` — patch separately after creation.

---

## Node 1 — per-clinic architecture

Node 1 uses a **shared base + optional practitioner-due override** pattern.

### Shared Node 1 (`nodes/shared/node_1_entry_greeting_router.txt`)
- 4 blocking signals: `book_intent`, `cancel_intent`, `info_pivot`, `wrap_up`
- Signal 5: SYMPTOM/CONDITION ONLY → fires `book_intent` (caller_complaint merged into payload); Node 2 handles from there
- No greeting — greeting is handled before Node 1 starts
- Outgoing edges: 1A (book_intent→Node 2), 1C (info_pivot→Node 8), 1E (wrap_up→Node 9), 1F (cancel_intent→Node 7)

### Practitioner-due Node 1 (`nodes/practitioner_due/<slug>/node_1_entry_greeting_router.txt`)
- Signal 5 replaced: COMPLAINT INTAKE — fires `complaint_intake` → edge 1G → Node 2C
- "Who's best for X" / "who do you recommend for X" → also fires `complaint_intake`
- Activated by `"practitioner_due": "<slug>"` in `clinic_agent_ids.json`
- `batch_patch --shared` auto-applies the override — no separate patching step

### Node 1 OUTPUT template rule
OUTPUT templates are authoritative. The LLM only includes variables explicitly listed per signal — "etc." in the ROUTING HARD RULE is insufficient.

| Signal | Must include in OUTPUT |
|--------|----------------------|
| BOOKING INTENT | `patient_name_raw`, `booking_for`, `family_member_name`, `practitioner_preference`, `timeframe_raw`, `preferred_gender`, `location`, `patient_status`, `implied_service`, `caller_complaint`, `group_or_private` |
| CANCEL/RESCHEDULE | `patient_name_raw`, `reschedule_mode`, `booking_for`, `family_member_name`, `timeframe_raw`, `location` |
| SYMPTOM/CONDITION | `caller_complaint`, `patient_name_raw`, `booking_for`, `family_member_name`, `timeframe_raw`, `preferred_gender`, `location`, `patient_status` |

**`{{double_braces}}` required:** every node that needs a variable must reference it with `{{double_braces}}` in the prompt or ElevenLabs won't inject it.

---

## Practitioner-due folder structure

```
nodes/
  shared/                          # Standard shared nodes (all clinics)
  clinics/{clinic_name}/           # Standard per-clinic booking nodes
  practitioner_due/{clinic_name}/  # Complaint-intake class (2C clinics)
    node_1_entry_greeting_router.txt
    node_2c_complaint_intake.txt
    doc1_complaint_mapping.txt
    doc2_practitioner_constraints.txt
```

**Never mix** practitioner-due files with booking nodes in `clinics/{clinic_name}/`. Integration scripts in `practitioner_due/` need `REPO_ROOT = SCRIPT_DIR.parent.parent.parent`.

---

## Phase 2 CONTEXT PIGGYBACK architecture (deployed 2026-05-04)

`universal_router intent="capture_context"` is **GONE from all active node prompts**. Do NOT add it back.

**Migration pattern — when writing or fixing any node:**
- `## IMMEDIATE CAPTURE` → `## BLOCKING SIGNALS`
- `### Non-blocking signals` → `### CONTEXT PIGGYBACK` with: "When a routing call fires, include any of the following that have been mentioned in the conversation into the universal_router payload."
- PRANK GUARD: transcript-based ("no prior redirect in this conversation") — no `caller_flag` DV
- `capture_context` calls mid-node → "Note the current service details — they will be included in the confirm_service payload after..."

**Exception (intentionally deferred):** `universal_router intent="capture_context"` still exists in 8 files (Node 6b + 6c variants). These are **functional DV-writes for expression edges**, not context sniffing. They require a backend redesign before removal. The `capture_context` handler in `tools/universal_router_webhook.py` must stay alive until then.

---

## Context variable wiring checklist

When a new variable needs to flow from Node 1 → router → downstream nodes, add it to ALL FOUR locations:

1. `UNIVERSAL_ROUTER_DYNAMIC_VARIABLE_NAMES` in `universal_router_webhook.py`
2. `CONTEXT_FIELD_SPEC` in `universal_router_webhook.py`
3. `RESPONSE_TO_DYNAMIC_VARIABLE` in `patch_tools_universal_router.py`
4. `twilio_init_webhook.py` seed (if knowable from patient lookup)

Missing any one of these means the variable is not persisted, not returned, or not injected.

**Context preservation:** The router merges missing fields from `session.resolved_context` for all `CONTEXT_FIELD_SPEC` fields, so async_capture variables are never wiped by a subsequent router call. `caller_complaint`, `preferred_gender`, `location`, `timeframe_raw`, `reschedule_mode` are all safe across node transitions.

**Router payload field rescue:** Both router endpoints use `extra="allow"` + a rescue block that self-corrects root-level payload-only fields. If the rescue fires, an alert email is sent — it means a node prompt has a syntax bug. `_KNOWN_PAYLOAD_ONLY_FIELDS` in `universal_router_webhook.py` is the canonical list.

---

## Voice style & personality

Set `ignore_default_personality: True` on ALL agents (API PATCH to `conversation_config.agent.prompt`). Without this, EL's helpful assistant persona adds filler ("Thanks for confirming", "Of course") on top of our prompts.

### VOICE STYLE rule — add to every node MINI-FRAMEWORK

**Node 2 version:**
```
- VOICE STYLE: Warm, calm, professional — brief like a receptionist on a phone call. Short sentences. Contractions fine. No verbal mirroring: when a caller answers a gate question, move directly to the next step — no echo, no acknowledgement, no filler.
```

**Node 3 version (inside FRAMEWORK, after OUTPUT STYLE):**
```
OPENER RULE: Begin every spoken response with the direct answer or question. No verbal mirroring: when a caller confirms a detail, move immediately to the next question — no echo, no acknowledgement, no filler. Banned openers: "I'd be happy to help", "Of course", "Certainly", "Absolutely", "Sure thing", "Right...", "Duly noted", "Great question", "No problem", "Got it", "Thanks for that", "Let me check on that".
```

**Node 8 version:**
```
## VOICE STYLE
No verbal mirroring before answers. When a caller asks a question, answer it directly — no preamble. Move straight to the answer, then the closing line.
```

**Shared nodes 6a/6b/6c/7/7b/9/11:**
```
- VOICE STYLE: No verbal mirroring. When a caller confirms something or answers a question, move directly to the next step — no echo ("Got it", "Perfect", "Great"), no filler. Short responses.
```

**CONFIRM_SERVICE SILENT RULE (mandatory in Node 2):**
```
- CONFIRM_SERVICE SILENT RULE: Any turn that calls universal_router with intent="confirm_service" is a tool-call-only turn. Apply OUTPUT VALIDATION: strip ALL planned spoken text from this turn before sending. HALT immediately after the tool call. Zero spoken output means zero — no preamble, no acknowledgement, no filler.
```

---

## Railguard hardening — all nodes (deployed 2026-05-06)

### ACCOUNT/PROFILE MODIFICATION (blocking signal — Nodes 6a/6b/6c/7/7b/8)
Trigger: caller asks to update email, phone, address, name, or any personal detail.
Response: "I can't update contact details directly, but I can pass a note to the clinic team if you'd like."
→ agreed: collect detail → leave_message → wrap_up
→ declined: wrap_up

### FINANCIAL ENQUIRY (blocking signal — Nodes 6a/6b/6c/7/7b/8)
Trigger: billing, invoices, refunds, payment plans, gap fees, outstanding accounts.
Response: "Our team handles billing directly — would you like me to get someone to call you back?"
→ agreed: callback_request → wrap_up
→ declined: wrap_up

### Node 8 specific additions
- **SERVICE COMPARISON BLOCK:** "should I see a chiro or massage?" → never recommend one service over another. "Both can be really helpful — best fit depends on your situation."
- **FINANCIAL COMMITMENT SUPPRESSION:** never say "I can lock in that price", "that's your rate", or any price-commitment language.
- **MESSAGING SUPPRESSION:** never say "I've noted that", "I'll flag that", "I'll record that", "I'll pass that to [practitioner]", "I'll make a note of that".

### Node 9 change
EMAIL CORRECTION → CONTACT DETAIL UPDATE: broadened to any contact detail (phone, address, name, email). Collects detail and sends via leave_message.

### Node 7 additions
- CANCELLATION SCOPE LIMIT: at most one smart_router cancel call per response turn
- MID-FLOW REBOOKING GATE: if cancel already called and caller now wants to book → wrap_up
- INFO PIVOT SCOPED EXCEPTION: "Is that possible?", "Can you do that?", "Would that work?" never trigger INFO PIVOT

---

## Node 8 handler architecture

Node 8 always routes `info_answered` when the caller is done — no DV-conditional branching.

**CLOSING LINE:** every answer turn ends with "Did you have any other questions?" On second use: vary ("Anything else I can help with?"). Never improvise referencing slots/dates/practitioners.

**BLOCKING SIGNAL #2 — WRAP-UP:** `"bye"` or `"goodbye"` (exact words, anywhere in message). Nothing else. Longer exclusion lists are ignored by Haiku under attention degradation.

**RESPONSE HANDLER evaluation order:**
1. YES HANDLER — bare affirmative, no question → "Go ahead." halt
2. NO HANDLER — closure statement → `universal_router intent="info_answered"` (TOOL-ONLY)
3. QUESTION HANDLER — new question → re-evaluate from FAST CLASSIFY, answer, CLOSING LINE
4. BOOKING SIGNAL HANDLER — explicit booking intent or time → `universal_router intent="info_answered"` (TOOL-ONLY)

NO HANDLER must be evaluated BEFORE QUESTION HANDLER. Haiku misclassifies "I just wanted to know" as a question.

**NO HANDLER phrase list:** "no", "nope", "no thanks", "nothing else", "that's it", "I'm good", "I'm fine", "that's all", "all good", "not right now", "that's fine", "I'm done", "I'm all set", "that's everything", "I just wanted to know", "I just wanted to find out", "just wanted to check", "that answered my question", "that's what I needed"

**Do NOT re-add:** BLOCKING SIGNALS #5 (DV digit check), LOOP PREVENTION scan, "Would you like to book?" offer from Node 8, CLOSING LINE FOLLOW-UP GATE.

---

## Node 8 KB attachment

**Always use the ElevenLabs UI — never the API** to attach KB documents to Node 8.

Steps: Open agent → Node 8 → Knowledge Base → turn OFF "Inherit knowledge base" → add document directly to node. This sets `usage_mode: "auto"` (RAG).

API PATCH sets `usage_mode: "prompt"` (full doc injected every turn — wrong).

The patch script fetches remote state before PATCHing — KB config set via UI is preserved through future prompt patches.

**IHW reference config:**
- Document: `Owaq6kEFAKiOzmeuIrv6` ("intuitive health and wellness modality info")
- Node: `node_01kbemmcz6f6dbt7ws7b6zk74p`

**Local node file header (documentation only — not read by patcher):**
```
Knowledge Base:
  - id: [document_id]
    name: [document name]
    type: text
    usage_mode: auto
    inherit: false
```
