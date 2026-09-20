# Node 7 back on claude-sonnet-5 — what changed, what was ported, how it was verified (2026-09-20)

Decision (owner): gpt-4.1 did not call the tool live, so it is ruled out (gpt-5.4-mini, 09-15, stalled on entry). Node 7 returns to
`claude-sonnet-5` fleet-wide. Tracker: `docs/in-progress/node7_entry_stall_gpt54mini_2026_09_20.md`.

## Base = the last proven Sonnet prompt, not the slim/gpt text

`nodes@04a70554` `shared/node_7_cancellation_handler.txt` (398 lines) ran on claude-sonnet-5 09-08 → 09-15: 0 of 14 entries stalled
(ElevenLabs conversations API, see the tracker). Commit `ff01036b` (09-15) replaced it with a ~200-line prompt written for gpt-5.4-mini.

A plain `git restore` + cherry-pick is not possible: `2a60536b`, `a79b9888`, `41e55d24`, `ca18516b` and `70500d40` all fail
`git apply --check` against the old text (they were written against the slim's line structure), so the fixes were ported by hand,
in the old prompt's own idiom.

## What the slim rewrite had silently dropped (compared 04a70554 vs the slim)

| Dropped | Why it matters |
|---|---|
| SIGNAL A.5 — arrival from Node 7b's `reschedule_cancelled` hand-off | Node 7b calls that intent in 11 places and expects Node 7 to run a real cancel; the trailing caller message (waitlist, "leave it cancelled") is leftover context |
| SIGNAL A.75 — caller describes a missed (past) appointment (`bd7f9166`, 09-11) | without it Node 7 starts cancelling an upcoming appointment |
| SIGNAL 6 + SUCCESS deferred waitlist `book_intent` | waitlist requests |
| name+DOB fallback collection (`86f7401b`) — DOB offer, DOB PARSING, DOB tool call | the slim mentions a DOB lookup but no path collects a DOB |
| the fixed `message_body` on LEAVE_MESSAGE FALLBACK | |

The shared 58-scenario battery has scenarios for A.5 (ARR ×3), A.75 (MAC ×4) and DOB (NAMEDOB ×7) that the slim text cannot satisfy.
Nothing else covers these (checked by grep: the shared system prompt and Node 7b).

## Ported since the slim (real-call driven) — all in the old prompt's idiom

* real cancellation-policy result shape (`error == "cancellation_policy_confirmation_required"`, id from `appointment_id`; was `policy_warning:true`) — the held 09-20 wording change; the ERRORS header now names it so it is not caught by the generic ERRORS block
* a genuine question bundled with "yes" is not a confirmation (`a79b9888`, SIGNAL 0 / CONFIRMATION REQUIRED / POLICY WARNING)
* THIRD-PARTY TAKEOVER with a WHO-CHECK before RESISTANCE / ORIENTATION (`2a60536b`); its cancel call sends the already-identified `appointment_id`
* NAME MATCH beats ordinal in multi-appointment cancel selection (`41e55d24`)
* MISSING APPOINTMENT recovery (other number, then date **and** time) (`a79b9888`)
* DETAILS RETURN = speak + `details_ack`, then the system prompt's PHASE C silent `wrap_up` (the old text said `wrap_up`, contradicting the system prompt)
* N8 RETURN (`info_answered`)

Not carried over (model-specific to gpt-5.4-mini / gpt-4.1): NODE ENTRY TURN, SILENCE MARKER ON ENTRY, BACKGROUND-RESULT TURN,
OUTPUT DISCIPLINE and the OUTPUT CONTRACT idiom.

## Plantar Fascia fork (`clinics/plantar_fascia_clinic/node_7_cancellation_handler.txt`)

A documented per-clinic fork (its "move it to a different Friday" offer). Its header says shared structural changes must be re-applied;
none had been since 09-11. Re-synced with a 3-way merge (base `bd7f9166`, ours = live fork, theirs = the shared candidate), 9 conflicts
resolved by hand, plus three things a merge cannot carry because the fork already lacked them: SIGNAL A.5, the fixed leave-message
`message_body`, the DOB-aware `no_appointments_found` line. It also gains the ATTENDEE SUBSTITUTION phrasing, the bare-day TIMEFRAME FILTER
fix and the 09-08 RESCHEDULE-MODE AVAILABILITY CHECK (`book_intent`, not `wrap_up`). The bundled-question re-asks carry the Friday offer.

## Verification (local only — no OpenRouter, no ElevenLabs runs)

`node7_agent_pack.py` builds the runtime prompt (system prompt + Additional Prompt, every `{{dv}}` substituted), renders each scenario as plain
CALLER/AGENT/TOOL RESULT text with **no expected answer**, and writes agent prompts. Blind `Agent(model="sonnet")` runs produce SPOKEN/TOOL;
a separate judge agent compares them to `expected_behavior`.

| Round | Target | Scenarios | Result | Found |
|---|---|---|---|---|
| 1 | shared candidate | 38 (every ported-fix tag + the restored A.5/A.75/DOB behaviours) | 37 pass | S8T: the takeover cancel sent `appointment_date`, not the already-known `appointment_id` → fixed; ERRORS header made explicit |
| 2 | shared candidate, touched regions | 14 (S8 family, policy-result-shape, missing-appointment) | 14 pass | |
| 1 | Plantar fork | 20 | 19 pass | ARR-1: the fork never had A.5 → added, with the two other omissions |
| 2 | Plantar fork | 10 (A.5, A.75, leave-message, DOB) | 9 pass | LMF-1, see below |
| 3 | shared candidate | LMF-1/2 | same behaviour as the fork | |

LMF-1 note: on "yes, please send a message" Sonnet calls `leave_message` immediately with the correct fixed `message_body` and the caller's
known name (shared 2/2, fork 2/2). The prompt (unchanged base text) says to stay silent for that one turn and let the system prompt's LEAVE MESSAGE
rule act on the next; the scenario's "zero tool calls this turn" expects that. The outcome (fixed body, no caller-words extraction) is what the
scenario protects, so the prompt was left alone.

## Known limits

* A local agent at default temperature with a text history is optimistic (see `docs/postmortems` / the Node 2 lessons). Absolute pass rates
  prove less than the differential; one run per scenario.
* The platform-side entry hand-off (history ending in a `notify_condition_*` tool result) cannot be reproduced locally. It is evidenced only by the
  old text's 0/14 live entries on Sonnet-5. After go-live check the first live Node 7 entries: the first agent turn in Node 7 must not follow a `"..."` user turn.
* An ElevenLabs test campaign was not run (owner rule: ask first).
