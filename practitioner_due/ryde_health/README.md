# Ryde Health — Practitioner Due / Complaint Intake Integration

## Status (2026-09-09)

Ryde unretired 2026-09-09. Audited Node 2C against the live agent before it took real calls
again: it was live and reachable (Node 1's edge into it was fine) but had **zero outbound
edges** — a dead end for any caller routed there. Root cause, best guess from the dates: the 6
outbound edges were applied 2026-04-10 via `patch_node2c_edges_ryde.py`, then wiped 5 days later
by the documented 2026-04-15 incident (a `batch_patch.py` run missing `--no-strict-edges` wiped
edges fleet-wide for nodes outside the patched folder) — and the original script was itself
deleted in the 2026-07-15 retirement cleanup.

Re-applied via a successor `patch_node2c_edges_ryde.py` (this folder) on 2026-09-09: restored
all 7 outbound edges + the Node 2→8 backward-condition tightening. Verified live and deployed.

**`due_router` (tool_6401k18fpvbrfcsv7d63p967n3vz) was deliberately NOT wired to Node 2C.**
Checked its live config: it's a test/demo variant of the voice-agent webhook with
`called_number` and `conversation_id` hardcoded to fake constants (see
`smart_voice_agent_config.py` `DUE_ROUTER_*_CONSTANT`) — wiring it into a node that takes real
calls would send fake caller data to the backend for every call. Node 2C's `smart_voice_agent`
wiring is correct as-is.

Still outstanding, not done in this pass: Node 3's "DUE-PRACTITIONER JUSTIFICATION" block was
lost to a later `generate_node3.py` regeneration (no `patches` entry preserves it for
`ryde_health`) — needs re-adding via that generator's `CLINIC_CONFIGS` + a normal Node 3 patch.


## Status (2026-09-11) — async_capture_context doc drift investigated, resolved as harmless

Investigated a discrepancy: the live Ryde agent has `details_ack` (`tool_9301kw12gm3jfecbzq20bpf6kzgw`)
as Node 2C's third tool, but this README and `node_2c_create_node_payload.json` documented
`async_capture_context` (`tool_3101km7k126qezfsqcxdxfdesdd8`).

**Verdict: doc drift only, live wiring was already correct — no live-agent patch needed.**

- `async_capture_context` was retired conceptually 2026-05-04 (commit e54922a2 — context capture
  became silent CONTEXT PIGGYBACK, no dedicated tool call) and the tool itself was deleted from
  ElevenLabs 2026-06-11 (commit ed500d17). Confirmed via live API GET 2026-09-11: the tool ID
  now returns `404 document_not_found`.
- `details_ack` (GET confirmed live, webhook `POST /api/v1/webhook/details-ack`) is the
  fleet-standard tool every node carries — it acks the shared system prompt's PATIENT
  APPOINTMENT LOOKUP delivery (`nodes/shared/system_prompt.txt`). Node 2C's own ESCAPE ROUTE 1
  explicitly delegates to that flow ("use the system prompt's PATIENT APPOINTMENT LOOKUP
  (universal_router intent="details") instead"), so Node 2C needs `details_ack` independently
  of anything async_capture_context ever did.
- Fetched the full live Ryde agent (`agent_4001knngjghcfwna069y6jjd6f2v`) and a second clinic
  (Intuitive Health and Wellness) via the ElevenLabs API 2026-09-11: every node on both agents
  carries `[universal_router, details_ack]` (+`smart_voice_agent` where relevant) — Node 2C
  matches this exactly. Zero nodes fleet-wide reference the dead async_capture_context tool ID.
- `node_2c_complaint_intake.txt`'s own TOOL ROLES section never mentioned async_capture_context
  or details_ack by name (correctly — details_ack is a shared-system-prompt-level tool, not
  restated per-node per `.claude/rules/node-prompt-style.md` "Don't repeat system-level rules").
  So there was nothing to fix in the prompt body itself.
- Fixed in this pass (doc-only, no live patch): this README, `node_2c_create_node_payload.json`'s
  `additional_tool_ids` + comment, and `integrate_node2c_ryde.py`'s `TOOL_ASYNC_CAPTURE` constant
  (renamed `TOOL_DETAILS_ACK`, dead ID→`tool_9301kw12gm3jfecbzq20bpf6kzgw`) — the script still had
  the dead ID hardcoded and would have wired the wrong (nonexistent) tool if ever re-run via
  `--from-step`.
- Separately found (not fixed here, out of scope of Node 2C): `nodes/README.md`'s "Tool
  assignment per node" table and `nodes/REVISED_master_workflow_updated.txt` also had stale
  async_capture_context references — `nodes/README.md` fixed same session; the master workflow
  doc's stale claim that the tool is "still attached to Nodes 1, 6a, 6b, 9" is disproven by the
  same live fetches above but was left for a separate pass.

Adapts the agent_7101kkp2ajcjf21tj7mrv59rhkj5 single-prompt scaffold (complaint
classification + due-rank practitioner selection) into the multi-node Ryde
Health agent (`agent_4001knngjghcfwna069y6jjd6f2v`) as a new node:
**Node 2C — Complaint Intake**.

## Files in this folder

| File | Purpose |
|---|---|
| `node_2c_complaint_intake.txt` | Full prompt body for Node 2C. Lift verbatim into the patch payload. Includes DOC 1, DOC 2, SERVICE ID LOOKUP, PRACTITIONER LOOKUP inline. |
| `node_2c_create_node_payload.json` | Empty-prompt creation stub for the new node. Tools wired: smart_voice_agent, universal_router, details_ack (due_router was the original plan but was swapped for smart_voice_agent — see Status section above; async_capture_context was the original third tool but was decommissioned 2026-06-11 — see Status (2026-09-11) below). Use this to create the node first, then patch the prompt body in a follow-up. |
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
| details_ack | `tool_9301kw12gm3jfecbzq20bpf6kzgw` |

`async_capture_context` (`tool_3101km7k126qezfsqcxdxfdesdd8`) is decommissioned — see Status
(2026-09-11) below. Do not use it in any future patch.

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

### C. async_capture_context vs `async_router` — RESOLVED 2026-09-11, superseded

This section originally deferred a decision between `async_capture_context` (then wired
fleet-wide) and a future `async_router` tool. Overtaken by events: `async_capture_context`
was retired fleet-wide 2026-05-04 (commit e54922a2 — context capture became silent CONTEXT
PIGGYBACK onto whichever routing call fires next, no dedicated tool call) and the tool itself
was deleted from ElevenLabs 2026-06-11 (commit ed500d17 — `tool_3101km7k126qezfsqcxdxfdesdd8`
now 404s). `async_router` was never built. Node 2C does not need either — it does not do
standalone async context capture at all; its own dynamic variables arrive pre-populated by
Node 1 (see ENTRY: CONTEXT SCAN) and its own captures ride along on universal_router/
smart_voice_agent payloads per the inherited CONTEXT PIGGYBACK rule.

Node 2C's actual third tool, confirmed live 2026-09-11, is `details_ack`
(`tool_9301kw12gm3jfecbzq20bpf6kzgw`) — required because this node's ESCAPE ROUTE 1 delegates
to the shared system prompt's PATIENT APPOINTMENT LOOKUP flow, which needs it. This matches
the tool set on every other node in this agent (and fleet-wide) exactly. See "Status
(2026-09-11)" above for the investigation that confirmed this.

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
