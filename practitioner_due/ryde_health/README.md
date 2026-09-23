# Ryde Health — Practitioner Due / Complaint Intake Integration

## Status (2026-09-23, night) — STEP 1 design proposal + safety escalation IMPLEMENTED and patched live

The STEP 1 design proposal below (concrete SKIP CONDITION / PRIMARY QUESTION / FALLBACK QUESTION)
and the new safety escalation ESCAPE ROUTE (item D below) are both now built into
`node_2c_complaint_intake.txt` and live on the Ryde Health agent
(`agent_4001knngjghcfwna069y6jjd6f2v`, node `node_2c_complaint_intake_tmp`).

- **Item E (remaining two categories) resolved without needing to ask** — the live node's own
  STEP 1 intro already names all six: Physiotherapy, Chiropractic, Osteopathy, Chinese Medicine &
  Acupuncture, Remedial Massage, Clinical Pilates. The FALLBACK QUESTION wording now explicitly
  says any of the six can be a live candidate, not only the four used in its example sentences.
- **Item D (safety escalation) scope decided as "Node 2C only"** — per the instruction that
  requested this work ("implement the README into ryde n2c"), the escalation is scoped to this
  node, not the shared system prompt. It is now ESCAPE ROUTE 1 (checked first, ahead of every
  other escape route and all STEP logic, every turn), using the trigger list proposed below as-is:
  numbness/weakness, chest pain, loss of bladder/bowel control, unexplained weight loss, fever, or
  major trauma. Per the doc's own caveat, this list is a starting point, not clinically
  exhaustive — worth a clinician review pass later, not blocking today.
- **SKIP CONDITION vs SERVICE PIVOT ESCAPE overlap, addressed:** a caller naming their own category
  preference while still describing their complaint ("my back hurts, can I see a chiro") now
  explicitly stays in this node (SKIP CONDITION) rather than risking a false exit to Node 2 via
  SERVICE PIVOT ESCAPE (which fires only when the caller abandons the complaint framing entirely,
  e.g. "forget that, just book me a massage") — a disambiguating NOTE was added at the point of use.
- **Stale `core`-tagged scenario fixed per this doc's own process (rule 3/5 below):** "Straightforward
  back pain gets a modality explanation, never a soon/timeframe question" was silently certifying
  STEP 1's clarifying question being skipped for a bare "my back hurts", which is no longer the
  intended behaviour. Its test input was changed to a complaint with a stated mechanism (a SKIP
  CONDITION trigger) so it still tests STEP 4's own behaviour without asserting a verdict on STEP
  1's now-different decision. 6 new scenarios were added covering the PRIMARY/FALLBACK split and
  the new safety escalation (positive trigger, false-positive regression guard, mid-conversation
  trigger) — `node_2c_complaint_intake_scenarios.json`, 20 scenarios total.
- **Verification:** mandatory Haiku self-audit loop (`.claude/rules/node-edit-verification.md`), 2
  rounds. Round 1: 72/100, all 15 scoped scenario probes PASSED, but 3 concrete stumbling points
  flagged (SAFETY ESCALATION filler/tool-call muscle-memory bleed from the other 4 escape routes;
  SKIP CONDITION vs PRIMARY QUESTION precedence when a caller states both a duration and a
  mechanism in the same breath; FALLBACK QUESTION wording only exemplified for 4 of the 6
  categories). All 3 fixed in the node text. Round 2: 92/100, all 3 fixes independently confirmed
  resolved, 3 new targeted probes PASSED, no new stumbling points. Accepted per the verification
  rule's known-tradeoff clause — the residual gap is inherent real-time wording generation for the
  FALLBACK question's open-ended category-naming, not a fixable ambiguity.
- **Deploy mechanism note (bug found and fixed in the same pass):** Node 2C is NOT part of the
  standard `fast_patch.py`/`batch_patch.py` per-clinic file set (it isn't under
  `nodes/clinics/ryde_health/`) — it's patched directly via this folder's own
  `integrate_node2c_ryde.py --from-step 8 --node2c-id node_2c_complaint_intake_tmp` (step 8 =
  `step_patch_node2c_prompt`, a direct ElevenLabs API PATCH). `parse_node_prompt()` was reading
  node `.txt` files as `encoding="utf-8"`, which does not strip a UTF-8 BOM — this file (and
  presumably others written by Windows tooling) has one, so `line.startswith("Node ID:")` never
  matched and every prompt-patch call hit `ERROR: Could not parse Node ID from ...` immediately.
  Fixed by switching to `encoding="utf-8-sig"` in `parse_node_prompt()` (the other two `read_text`
  call sites in this script, `upload_kb_doc` and `step_update_node1_local`, don't crash on a BOM —
  left as-is, out of scope of this pass). Patched live and verified via a full-text fetch-and-diff
  against the live agent (not just the script's own first-200-char check): exact byte match,
  39711 chars.
- **Not done in this pass, deliberately out of scope:** the safety-escalation trigger list itself
  was implemented as proposed, not clinically re-derived — see item D's note above. No ElevenLabs
  test-call credits were spent (per the standing rule) — verification was the local Haiku
  self-audit loop only.

## Status (2026-09-23, evening) — live call showed zero triage differentiation; root cause found; design proposal open

Real call, same day as the two rewrites below: caller says "i hurt my back". Node 2C responds
"back pain is really common, and physio, chiro, or osteo are all great at working out what's
driving it... let me have a look at what's available" and goes straight into `recommend_availability`
— no clarifying question at all, no attempt to differentiate between the three candidate
categories. User flagged this as wrong: for a complaint where the clinic genuinely offers several
meaningfully different approaches (hands-on/manual vs rehab/exercise, plus acupuncture as a
further option), the caller should be asked something to help land on the right one — not
necessarily a rigid question per complaint-modality permutation, but *some* triage signal beyond
"they're all great."

**Root cause, confirmed via `nodes` git history (`git log` on this file):** this is not a testing
gap — the self-audit scenario suite was faithfully checking the behaviour the prompt was written
to produce a few hours earlier, and that behaviour is what's now considered wrong.

1. Commit `920775af` (the loose/LLM-driven STEP 1 rewrite, earlier the same day) replaced the old
   DOC-1-table-driven mandatory question with a subjective bar: "Reserve a clarifying question for
   when you're genuinely torn between two meaningfully different approaches... Ask at most ONE such
   question." This bar has no concrete trigger — it relies on the model *feeling* torn, and Haiku
   evidently does not feel torn about "back pain" even though physio/chiro/osteo are three
   meaningfully different approaches to it.
2. Commit `a12a2d28` (later the same day) fixed a *different*, real problem found in a call review:
   STEP 4 was asking a low-value standalone timeframe question ("are you looking to get in soon...")
   on nearly every call and skipping the modality explanation for "obvious" complaints like back
   pain. That fix was scoped correctly to STEP 4 (timeframe question + modality_reason generation).
   But the scenario added to verify it — **"Straightforward back pain gets a modality explanation,
   never a soon/timeframe question"**, tagged `core` + `asap-default`, input `"my back hurts"` —
   wrote its PASS criteria around the *combination* of both steps: "speaks a short, complaint-specific
   reason... then moves straight toward checking availability... with no question in between." That
   criteria is correct for STEP 4 (no timeframe question) but, because the test input is a bare
   4-word complaint with zero differentiating detail, it *also* certifies STEP 1 skipping the
   clarifying question entirely as correct — which was never the thing this scenario was written to
   test, but is exactly what the real call did.
3. Because that scenario is tagged `core`, it now runs on every future self-audit and will FAIL any
   change that tries to make STEP 1 ask a differentiation question for a bare "my back hurts" —
   i.e. the current scenario suite actively blocks the fix the user is asking for. It must be
   rewritten (not just STEP 1) before any STEP 1 change can be verified honestly.

**Lesson for future scenario-writing on this node, formalized below:** when a scenario is added to
verify a fix to one STEP, scope its PASS/FAIL wording to that STEP's behaviour only. Don't let an
input chosen for convenience (a bare, information-free complaint) silently also assert a verdict on
a *different* STEP's decision (whether to ask a clarifying question at all) that the commit never
intended to test.

**Design proposal for STEP 1 (revised same session, folding in chat suggestions — still pending
user sign-off, not yet implemented):** replace the subjective "genuinely torn" bar with a concrete
signal check, prioritising the axes the user asked for. Two additions below are new since the
original writeup: an extended skip signal, and a safety escalation branch.

- **Skip condition (extended):** the existing rule ("skip the question entirely whenever the
  caller's own words already resolve it") now explicitly covers two signal types instead of one:
  - explicit category preference ("book me a chiro") — existing, kept
  - a clear mechanism or trauma in the caller's own words (fell, lifted something, twisted it
    playing sport, car accident) — new; treated as resolving toward physio the same way a stated
    preference resolves toward the named category, on the reasoning that recent trauma is a
    stronger fit for an assessment-and-rehab pathway than for a manual adjustment
  Either signal skips the primary question below entirely.
- **Primary default question (new):** when the caller has given no duration/history signal at all
  ("since when", "on and off", "tried X before" — none present) and the landed category set has
  2+ real candidates, ask ONE combined question surfacing both acuity and treatment history in one
  breath — e.g. "How long has this been going on, and have you tried anything like physio, chiro,
  or osteo for it before?" A chronic-with-prior-treatment answer often resolves the category choice
  directly (whatever helped before) without needing a second question.
- **Fallback question (existing, kept, retriggered, wording generalised):** only if the primary
  didn't resolve it (acute, or chronic with nothing tried before) AND the categories still
  meaningfully differ in approach, ask a plain-language approach question naming whichever
  categories are actually live for this complaint, rather than a fixed hands-on-vs-rehab-plus-
  acupuncture template. The current phrasing (hands-on-vs-rehab, optionally folding in acupuncture:
  "...or would you be open to trying acupuncture for this?") is the right pattern when the landed
  set is physio/chiro/osteo/acupuncture; it needs to be written so it can name a different pair or
  triple if the landed set differs (e.g. osteo/chiro/acupuncture with no physio candidate).
- Still never more than ONE question per turn (existing STEP 1 rule, kept).
- Still skip entirely whenever the caller's own words already resolve it (existing rule, kept,
  now covering the wider trigger list above) — this is what keeps it from reintroducing the old
  DOC-1 "scripted mandatory question on nearly every call" problem: the question is skipped
  whenever the caller already volunteered the relevant signal, not whenever the model subjectively
  decides it isn't needed.

**New: safety escalation, ESCAPE ROUTE 2 (not yet drafted into `node_2c_complaint_intake.txt`):**
none of STEP 1 through STEP 8 currently screens for anything. Proposed addition, same "only fires
on signal, never scripted" philosophy as the rest of this node, not a dedicated question and not
gated to STEP 1 specifically: if the caller volunteers any of numbness or weakness, chest pain,
loss of bladder or bowel control, unexplained weight loss, fever, or a major trauma (car accident,
fall from height, suspected fracture) anywhere in Node 2C, stop the normal triage/booking flow and
direct them to urgent GP or emergency care instead of a routine booking. Sits alongside ESCAPE
ROUTE 1 (appointment lookup delegation), doesn't replace it. Trigger list is a starting point, not
a clinically exhaustive one; see Open / deferred decision D below.

This changes the *default direction* of STEP 1 (ask unless signalled, vs. today's skip unless
torn), adds a new signal type to the skip list, generalises the fallback's category wording, and
adds a net-new escalation path — four genuine design choices, not bug fixes with one right answer,
so all of it needs the user's sign-off on the shape above before any of it is written into the
node and re-audited. Per the review process below (rules 3 and 5), the `core`-tagged scenario
blocking the STEP 1 fix needs to be rewritten in the same pass as whichever of the above gets
built, not as a follow-up.

## Triage question design & review process (formalized 2026-09-23, after the above)

For any future session working on Node 2C's (or a future triage-enabled clinic's) clarifying-question
logic:

1. **Source real failures from call transcripts, not assumption.** A scenario written from
   imagination tends to encode whatever the prompt already does. Pull the actual caller wording.
2. **Separate the two concerns explicitly when reading or editing this node:** STEP 1 decides
   *which category and whether to ask a clarifying question*; STEP 4 decides *what to say once a
   category is chosen* (modality reasoning) *and the timeframe*. A fix to one must not be verified
   only through a test scenario whose input/PASS-criteria silently also asserts a verdict on the
   other's untested behaviour.
3. **Scope every new scenario's `expected_behavior` text to the one behaviour the commit changed.**
   If the chosen test input could also exercise a different, not-yet-decided behaviour (e.g. a bare
   complaint with no signal, which also exercises "should I ask a clarifying question"), either (a)
   write the PASS criteria to cover both axes deliberately, or (b) pick an input that doesn't
   incidentally certify the untested axis.
4. **A change to the clarifying-question trigger threshold is an architecture/design decision, not
   a data-driven bug fix** — confirm the specific framework (which axes, what counts as "enough
   signal to skip") with the user before rewriting STEP 1, the same way the 2026-09-23 loose
   rewrite and the practitioner-specialty removal were both done per explicit user direction.
5. **After any STEP 1 edit, don't just run the existing scenario suite — re-read each scenario's
   PASS criteria and ask whether it still says what you now believe is correct.** A scenario that
   passed yesterday can be passing because it's rewarding the exact behaviour you're trying to
   remove today (this is precisely what happened above). Update or retag stale scenarios in the
   same commit as the prompt change, not as a follow-up.
6. **Keep this section current** — if the framework above changes (a different axis added, a
   question folded differently, the whole approach replaced), update this section so the next
   session doesn't have to re-derive it from git history.

## Status (2026-09-23) — Node 2C triage rewritten as loose/LLM-driven, specialty matching dropped

Requested by the user: Node 2C's classification step (STEP 1/1B/1C/1D/2/3 in the old numbering) was
a rigid, table-driven decision tree -- a hardcoded DOC 1 complaint→category lookup table (80 lines),
a MUSCULOSKELETAL CATCH-ALL body-region table, and GROUP 1/2/3 modality-menu machinery that forced a
scripted structural-vs-rehab-vs-systemic question for nearly every complaint. Rewritten so the model
does the clinical reasoning itself: STEP 1 now just lists the six categories Ryde Health offers and
gives loose guidance to ask at most one plain-language clarifying question, only when genuinely
torn between two meaningfully different approaches -- never a scripted mandatory question, never a
recited modality menu. `git backup: nodes commit dd1e6b94 ("old ryde triage 2c")` holds the exact
pre-rewrite file plus DOC 1/DOC 2/the old scenarios file, in `backup/2026-09-23/practitioner_due/ryde_health/`.

**Practitioner-specialty matching (DOC 2, STEP 6-PRIME's focus-match reorder) removed per explicit
instruction ("let's ignore practitioner specialties for now")** -- `doc2_practitioner_constraints.txt`
is no longer referenced anywhere in the live node. `stored_recommendations[]` is now presented in
whatever due-rank order the backend returns, unmodified. STEP 6a-3's justification generation (warm,
complaint-specific, from clinical world knowledge, not from DOC 2 text) is unchanged and still runs
for every offer, including "who's best" queries -- there is no longer a separate WHO'S-BEST
pre-check flow (old STEP 1B); a caller who defers the choice to the agent just skips the clarifying
question and flows through the same pipeline as everyone else.

**Kept unchanged, verbatim: all "tech" that looks at availability and practitioner due-rank** --
the STEP 5 `smart_voice_agent recommend_availability` tool call, STEP 6/6a/6b response handling and
slot-band grouping/narrowing, the NEXT AVAILABLE OFFER quick path, STEP 7's fallback sequence
(next practitioner in the ranked array → widen to an adjacent category → widen the time window →
`find_next_available`), and STEP 8's confirm-and-handoff. SERVICE ID LOOKUP and the
PRACTITIONER LOOKUP fuzzy-name table are also unchanged (the latter's per-practitioner "primary
modality" column is not specialty data -- it's needed to resolve a named practitioner to a service
ID, and is now also reused as STEP 7's fallback category if that one named person has nothing
available).

**One correctness fix made in the same pass, not requested but necessary:** the old STEP 1C/1D gave
a named-practitioner request ("book me with Angelo") its own bespoke availability pre-check outside
STEP 7's fallback chain. Removing that pre-check (folded into the same generic STEP 1→5→6→7 pipeline
everyone else uses, per the loose-triage redesign) exposed a latent bug in STEP 7 STAGE 1: it
assumed `stored_recommendations[]` always has 3+ entries and would try to read a second entry that
doesn't exist for a single-named-practitioner array. Fixed with a bounds check (STAGE 1 falls
straight through to STAGE 2 when there's no second entry to advance to), and STAGE 2 now switches
`approach` from "A" to "B" using that practitioner's own modality (from PRACTITIONER LOOKUP) as the
fallback category, so a named-practitioner request with nothing available still widens sensibly
instead of stalling. See scenario "Named practitioner with nothing available widens into their own
modality" in `node_2c_complaint_intake_scenarios.json`.

Not touched in this pass: `doc1_complaint_mapping.txt` and `doc2_practitioner_constraints.txt` are
left in place (unreferenced by the live node) rather than deleted, in case specialty-aware matching
is reintroduced later -- if a future session revisits practitioner specialties, these are the
starting reference data. Node 1's IMMEDIATE CAPTURE signal into this node, the edges, and the tool
wiring are all unaffected by this change.

**Verification:** mandatory `.claude/rules/node-edit-verification.md` Haiku self-audit loop run
against the rewritten prompt (this node is `LLM: claude-haiku-4-5`, `Override: Disabled`) using the
rewritten scenarios file (12 scenarios, `core`-tagged plus new `loose-triage`/`due-rank-order` tags)
before patching live -- see the audit result recorded below once it lands this session.

## Status (2026-09-22) — edge_node2c_service_pivot dead edge fixed and re-deployed

Found via the corrected fleet-wide `tests/test_nodes_expression_edges_uni_router_values_are_producible`
test (previously a permanent no-op — non-recursive glob + a regex that never matched the plain-text
edge syntax nodes actually use): `edge_node2c_service_pivot` (N2C → N2) was keyed on
`uni_router_intent == "change_service"`, but `tools/universal_router_webhook.py`'s
`INTENT_TO_UNI_ROUTER_INTENT` maps `intent="change_service"` to `uni_router_intent="service_change"`
("change_service" is the tool-call intent name, not the emitted DV value) — the exact same bug class
as the Node 4 "details" fix in commit 12a86835. Every other clinic's Node 2 checks
`{{uni_router_intent}} == "service_change"` for this same hand-off, so this edge could never fire: a
caller in Node 2C who wanted to change the requested service had no way to route back to normal
service resolution. The original 2026-04-10 edge (via the now-deleted original
`patch_node2c_edges_ryde.py`) had this right; the *successor* `patch_node2c_edges_ryde.py` (this
folder, written 2026-09-09 from this file's own then-wrong header comment) reproduced the bug and
pushed it live.

Fixed same session: this file's header comment, `patch_node2c_edges_ryde.py`'s docstring + `_eq(...)`
call, and re-ran the script against the live agent (verified via a fresh GET — the live edge now
reads `uni_router_intent == "service_change"`). The same run also re-applied the `edge_new_node2_info_pivot`
(N2↔N8) backward-condition tightening (`caller_complaint == "none"`), which a dry-run beforehand
showed had drifted back to its untightened 2-clause form since the 2026-09-09 patch — cause not
investigated (`scripts/add_node4_node1_and_book_edges.py`, today's fleet-wide Node1→Node4/Node4→Node2
edge rollout, was checked and only *adds* new edge keys via `dict(edges)`, never touches existing
ones, so it isn't the cause).

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


## Status (2026-09-14) — DUE-PRACTITIONER JUSTIFICATION redesigned and re-added (local only)

Re-added, scoped to `ryde_health` only via a `patches` entry in `scripts/generate_node3.py`
`CLINIC_CONFIGS['ryde_health']` — not a hand-edit of the generated `.txt` file (which would be
silently overwritten on the next regeneration, same as any other Node 3 clinic).

No exact original text survived — searched the `nodes` submodule's full git history and found no
commit containing the old block; it was applied directly to the live/local file circa April 2026
and later overwritten by a `generate_node3.py` regeneration before ever being committed. The old
"NEXT AVAILABLE OFFER" / STEP 5 → STEP 9 section it lived in also no longer exists — that
structure belonged to the pre-2026-07-20 gpt-4.1 "regular" Node 3 template; the clinic has been on
the P2 slim template (`nodes/node3_templates/node_3_p2_slim.txt`) since that migration. This is a
fresh design against the current template, not a restoration.

Verified before designing: `{{new_patient_allocation_enabled}}` is a real, currently-live DV —
set by `tools/twilio_init_webhook.py` from `clinic_settings.new_patient_allocation_mode in
("even", "custom")`, defaulting to `"false"` — not a stale/unused spec. `{{caller_complaint}}` and
`{{patient_status}}` are likewise real, live DVs (context-piggybacked via `universal_router`'s
`CONTEXT_FIELD_SPEC`, pre-declared with empty defaults by `twilio_init_webhook.py`). Also
confirmed `ryde_health` DOES have a live `clinic_agent_ids.json` entry
(`agent_4001knngjghcfwna069y6jjd6f2v`) — the "NOT currently live" note that used to sit on this
clinic's `CLINIC_CONFIGS` entry (accurate 2026-09-02) was stale as of the 2026-09-09 unretirement
above and has been corrected in both `generate_node3.py` and this clinic's
`node_3_availability_handler_scenarios.json`.

Design: the current P2 slim template only ever names the recommended practitioner to the caller
inside `SINGLE-PRACTITIONER`'s two count branches that speak `[first_name]` — "1 time, no next
band" and "2+ times". Both were patched (tag: `DUE-JUSTIFY` on both) to add one clause ("based on
what you've told me, [first_name] is a good match for this") to that same spoken turn, gated on
ALL of: `{{caller_complaint}}` non-empty, `{{new_patient_allocation_enabled}}=="true"`,
`{{patient_status}}=="new"`, the practitioner having been auto-selected via
`PRACTITIONER + LOCATION FALLBACK` (i.e. the caller never named one themselves — this is what
scopes the feature to the due-rank backend recommendation specifically, not a coincidental
single-practitioner-in-category match or a caller-stated preference), and — for the "2+ times"
branch — this being the first offer of the call (piggybacking the template's own existing
LOCATION ANNOUNCEMENT first-offer gate), plus never repeating the sentence for the same
practitioner later in the same call. Every OUTPUT CONTRACT on the touched branches was extended
to name the new clause explicitly rather than left to bleed in unconditionally, per
`.claude/rules/node-prompt-style.md`. `FIRST-APPOINTMENT OVERRIDE` and the "0 times" / "1 time,
next band has times" branches were deliberately left untouched — none of them speak the
practitioner's name in this template, so there is nothing to justify there.

Verification: `py -X utf8 scripts/generate_node3.py --clinics ryde_health --dry-run` reports 0
skipped/warned (both patch anchors matched cleanly); regenerating for real produced a diff
touching only the two intended lines. Two rounds of the mandatory Haiku self-audit
(`.claude/rules/node-edit-verification.md`) both ran clean: all 5 scoped scenarios (2 `core` +
3 new `due-practitioner-justification`-tagged, added to
`node_3_availability_handler_scenarios.json`) PASSED in both rounds, plus one additional ad-hoc
probe (re-offering the same due-selected practitioner later in the same call correctly does NOT
repeat the justification). Confidence scored 74/100 then 70/100 across the two rounds — the drop
is self-reported-uncertainty noise, not a regression (every scenario output was correct in both
rounds); the residual stumbling points are multi-turn "already said this, this call" state
tracking, a difficulty class the base P2 template already carries in several other places
(LOCATION ANNOUNCEMENT's own first-offer gate, WAITLIST-ASKED CHECK, DETAILS_ACK CALL LOCK) and
not something newly introduced by this patch — accepted as a known tradeoff rather than iterated
further.

**Not yet patched to the live agent** — per the standing rule, any `fast_patch.py`/
`batch_patch.py` run against a live ElevenLabs agent needs explicit user approval every time, even
though this clinic's onboarding itself was a pre-authorized live-patch exception. Once approved:
`py -X utf8 scripts/fast_patch.py --clinic "Ryde Health"` (fast_patch regenerates Node 1/2/3/8
from their generators automatically, so no separate `generate_node3.py` run is needed first).


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
(`tool_9301kw12gm3jfecbzq20bpf6kzgw`) — required because this node's CANCEL / RESCHEDULE ESCAPE
(route 2 as of the 2026-09-23 night safety-escalation renumbering; was route 1 when this note was
written) delegates to the shared system prompt's PATIENT APPOINTMENT LOOKUP flow, which needs it.
This matches
the tool set on every other node in this agent (and fleet-wide) exactly. See "Status
(2026-09-11)" above for the investigation that confirmed this.

### D. Safety escalation trigger list — RESOLVED 2026-09-23 (night), implemented and live

Built as ESCAPE ROUTE 1 (renumbered to be checked first, ahead of the other four) in
`node_2c_complaint_intake.txt`, scoped to Node 2C only (not the shared system prompt) per the
instruction that authorized this build. Trigger list shipped exactly as proposed: numbness or
weakness, chest pain, loss of bladder or bowel control, unexplained weight loss, fever, or major
trauma. Not re-derived clinically in this pass — still worth a clinician review of the exact list
later, per the original caveat, but that review isn't blocking since the route's job (stop and
redirect to urgent care) is conservative by construction: a false negative (missed trigger)
behaves exactly as Node 2C did before this change (routine triage), and a false positive just
sends a caller who didn't need it to a GP/ED referral instead of a booking. Verified via the
mandatory Haiku self-audit loop (see the 2026-09-23 night status section above) including a
false-positive regression scenario ("my back's been absolutely killing me").

### E. Ryde Health's remaining two categories — RESOLVED, was already answered in the node itself

Turned out not to need asking: `node_2c_complaint_intake.txt`'s own STEP 1 intro already lists all
six categories Ryde Health offers (Physiotherapy, Chiropractic, Osteopathy, Chinese Medicine &
Acupuncture, Remedial Massage, Clinical Pilates) — this README just hadn't named the last two
(Remedial Massage, Clinical Pilates) anywhere in its own prose. The FALLBACK QUESTION wording was
generalised to say explicitly that any of the six can be a live candidate, not only the four used
in its example sentences.

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
5. **Safety escalation trigger list is new and unvalidated**: once ESCAPE ROUTE 2 is built,
   false negatives (a real red flag that doesn't match the trigger list) are the risk to watch
   first, since they're the costly failure mode. False positives (escalating a routine complaint
   that happens to use one of the trigger words loosely, "my back's been killing me") are lower
   stakes but will affect booking conversion if the wording is too broad. Worth a dedicated
   scenario batch before this goes live, the same way the rest of Node 2C is audited.
