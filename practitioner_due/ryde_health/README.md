# Ryde Health — Practitioner Due / Complaint Intake Integration

Adapts the agent_7101kkp2ajcjf21tj7mrv59rhkj5 single-prompt scaffold (complaint
classification + due-rank practitioner selection) into the multi-node Ryde
Health agent (`agent_4001knngjghcfwna069y6jjd6f2v`) as a new node:
**Node 2C — Complaint Intake**.

## Files in this folder

| File | Purpose |
|---|---|
| `node_2c_complaint_intake.txt` | Full prompt body for Node 2C. Lift verbatim into the patch payload. Includes DOC 1, DOC 2, SERVICE ID LOOKUP, PRACTITIONER LOOKUP inline. |
| `node_2c_create_node_payload.json` | Empty-prompt creation stub for the new node. Tools wired: due_router, universal_router, async_capture_context. Use this to create the node first, then patch the prompt body in a follow-up. |
| `research_prompt_kb_injection.md` | Hand to another AI to research whether ElevenLabs KB documents are injected verbatim for small KBs vs RAG-chunked. Decides whether DOC 1/2 stay inline or move to KB. |
| `research_prompt_universal_router.md` | Hand to another AI to add the `complaint_intake` pass-through intent to `tools/universal_router_webhook.py`, plus add `caller_complaint` to `CONTEXT_FIELD_SPEC`. |
| `README.md` | This file. Integration order, open questions, deferred work. |

## Files modified outside this folder

| File | Change |
|---|---|
| `nodes/shared/node_1_entry_greeting_router.txt` | Added IMMEDIATE CAPTURE blocking signal #4 (COMPLAINT INTAKE) and new edge `edge_new_node1_complaint_intake` (target = Node 2C, expression edge `uni_router_intent == "complaint_intake"`). Target node ID is placeholder `<NODE_2C_ID_TBD>` — update after the create-node call returns the assigned ID. |
| `nodes/clinics/ryde_health/node_3_availability_handler.txt` | Added DUE-PRACTITIONER JUSTIFICATION block to the NEXT AVAILABLE OFFER section (STEP 5 → STEP 9 path). Generates a one-sentence clinical justification when `caller_complaint` is set, `new_patient_allocation_enabled == "true"`, `patient_status == "new"`, and justification has not yet been spoken for this practitioner. |

## Tool IDs (Ryde agent)

| Tool | ID |
|---|---|
| smart_router | `tool_4501k96qzckzemabz9rwppjms6zj` |
| smart_voice_agent | `tool_4501k96qzckzemabz9rwppjms6zj` |
| universal_router | `tool_9401k7e4bc90fw7avkmysavqhj91` |
| async_capture_context | `tool_3101km7k126qezfsqcxdxfdesdd8` |

## Integration patch order

1. **Add `complaint_intake` to universal_router** — apply
   `research_prompt_universal_router.md`. Run its tests. Deploy the webhook.
   *Without this, Node 1's IMMEDIATE CAPTURE call will fail validation.*

2. **Patch Node 3 single-category logic** — already applied to local file
   `nodes/clinics/ryde_health/node_3_availability_handler.txt`. Run the
   normal Node 3 patch flow (`patch_staging.py` or equivalent) to push to
   ElevenLabs.

3. **Create Node 2C (empty)** — apply `node_2c_create_node_payload.json`
   to the Ryde agent. Capture the assigned `node_id` from the response.

4. **Update Node 1 edge target** — replace `<NODE_2C_ID_TBD>` in
   `nodes/shared/node_1_entry_greeting_router.txt` with the assigned Node 2C
   ID. Patch Node 1.

5. **Add Node 2C outbound edges** — Node 2C needs the same edge fan-out as
   Node 3 minus the booking-flow internals. Edges to add (using Node 3's
   target IDs as reference):
   - to Node 6a (`booking_self`)
   - to Node 6b (`booking_other`)
   - to Node 7 (`cancel_intent`)
   - to Node 8 (`info_pivot` / `info_answered`)
   - to Node 9 (`wrap_up`)
   - to Node 11 (`error_recovery`, llm condition)

6. **Patch Node 2C prompt body** — apply the body of
   `node_2c_complaint_intake.txt` (everything below the `Additional Prompt:`
   header) into the `additional_prompt` field of a follow-up update patch.

7. **(deferred) Test scaffold** — build `test_node2c_scaffold.py` mirroring
   `test_node2_scaffold.py` and `test_node3_scaffold.py`. Cover: clean
   complaint, named-practitioner, who's-best, needle check, full fallback to
   `find_next_available`, debug command, mixed-signal handling once the
   focus-match override (below) ships.

## Open / deferred decisions

### A. DOC 1 / DOC 2 storage — pending KB research

Current state: DOC 1 and DOC 2 are **inlined** in `node_2c_complaint_intake.txt`
so the prompt is self-contained and runnable as-is. Hand
`research_prompt_kb_injection.md` to another AI. If the answer confirms small
KB documents are injected verbatim, migrate DOC 1/2 to the agent's Knowledge
Base for cleaner editing, and remove the inline copies.

### B. Mixed-signal handling — service AND complaint named (Option 1)

Caller says *"I'd like to book a physio for my back pain"* — service AND
complaint. Decision: this still routes to Node 2 (booking path), NOT Node 2C.
Node 2 resolves to a single category, then Node 3 should:

1. Check DOC 2 for a focus match within that single category (e.g. is there a
   physio whose focus list mentions "back pain"?).
2. If yes → surface that practitioner ahead of due rank.
3. If no → fall through to backend due-rank (current behavior).

**Current state:** only step 3 works. Steps 1–2 require Node 3 to have access
to DOC 2. Defer until KB-injection research is complete — if KB docs inject
verbatim, attach DOC 2 to Node 3's KB instead of duplicating it inline. Then
add a Node 3 prompt section that scans the focus lists and surfaces a
matching practitioner from `stored_recommendations[]` even if not first-ranked.

### C. async_capture_context vs `async_router`

User mentioned `async_router` as a future tool. Currently using
`async_capture_context` (already wired across the rest of the workflow).
When `async_router` ships as a separate tool/webhook, add it to Node 2C's
`additional_tool_ids` and update the prompt's "TOOL ROLES" line.

## Verification before patching

Per CLAUDE.md "Before recommending from memory" — confirmed the following
against current code (April 2026):

- **`get_due_practitioners` in `tools/new_patient_practitioner_selector.py`**:
  runs at the appointment_type level, returns a single due practitioner when
  `new_patient: true` and a single category is sent. **No backend changes
  needed for the Node 3 single-category path.**
- **Node 1 edge IDs**: `node_01kbej4q4sf6dbt7vd9f1e03t1` is the current Node 1
  ID per the local file. Existing IMMEDIATE CAPTURE list and edge structure
  preserved.
- **Tool IDs**: confirmed via `patch_staging.py:43-46`. due_router is real and
  available, points to the same voice-agent webhook as smart_router with
  fixed system params.
- **Ryde agent ID**: `agent_4001knngjghcfwna069y6jjd6f2v` per
  `clinic_agent_ids.json`.

## Risks to watch on first deploy

1. **Inflated false positives on complaint_intake**: callers who say "my back
   hurts, can I book a physio?" should fall through to Node 2, not Node 2C.
   The Node 1 suppression rule depends on Node 1's LLM correctly detecting the
   service mention. If false-routes to 2C are common, tighten the suppression
   wording or add a service-detection regex hook upstream.
2. **DOC 1 / DOC 2 token cost**: ~1500 tokens added to every Node 2C turn.
   Acceptable for a complaint-intake node that runs <10 turns. Move to KB if
   token budget becomes a concern.
3. **Node 6a/6b expects appointment_type_id from confirm_service**: Node 2C's
   STEP 8 payload includes `appointment_type_id`, `appointment_type`,
   `practitioner_preference`, `appointment_date`, `appointment_time`,
   `booking_for`. Verify Node 6a/6b name collection works with this payload
   shape — should be identical to Node 3's confirm_time payload modulo the
   intent name.
4. **`caller_complaint` not in CONTEXT_FIELD_SPEC**: until the universal_router
   patch lands, `caller_complaint` will be silently dropped from the
   complaint_intake payload. Node 2C will then re-extract it from the
   conversation history on entry — should still work but adds a turn.
