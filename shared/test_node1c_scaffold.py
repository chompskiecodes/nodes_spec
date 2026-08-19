#!/usr/bin/env python3
"""
test_node1c_scaffold.py  (shared — Node 1c, Appointment Lookup Recovery)

First live-EL scaffold test for node_1c (nodes/shared/node_1c_appointment_lookup_recovery.txt),
the node that re-resolves a caller's identity after their phone-based appointment lookup
(intent="details"/"details_past") fails on the first try. Deployed fleet-wide
(commit 77658872) with only a pytest suite (tests/test_appointment_lookup_recovery.py, backend
DV contract only) and a self-audit — no live EL scaffold test has run against it yet, the same
gap every other node's self-audit in this repo carries per node-edit-verification.md.

STATUS UPDATE 2026-08-20: the original T2/T4/T5 hypothesis (system_prompt.txt cross-
contamination causing a hardcoded intent="details") was disproven by a controlled A/B — see
project_node1c_scaffold_test_and_bugs_2026_08_20 (session memory). The model reliably echoes
a value pre-substituted as literal TEXT but not one relied on EL's own
dynamic_variable_placeholders substitution to fill a tool-call parameter — reproduced
regardless of prompt wording or how many times the token appeared. Fix: node_1c's retry calls
now use a FIXED LITERAL intent="appointment_lookup_retry" (never a DV substitution), and the
backend (_handle_appointment_lookup_retry_intent in tools/universal_router_webhook.py)
resolves which underlying lookup to retry from server-side session state. T2/T4/T5 below are
updated to expect this literal value — same shape as T6's intent="wrap_up", which passed
reliably in every prior run specifically because it's already a fixed literal, not a DV.

Covers (6 tests, cost-conscious per this repo's convention — not full coverage):
  T1 ENTRY               — MANDATORY PART 1 exact message, no tool call, stops.
  T2 ALT_NUM_VALID        — valid alt number -> filler + universal_router
                             intent="appointment_lookup_retry" (fixed literal — see STATUS
                             UPDATE above), payload={"patient_phone": "<digits only>"}.
  T3 ALT_NUM_INVALID_ONCE — one clearly-invalid number format -> exactly ONE re-ask, no tool call
                             (must not skip straight to NAME+DOB PATH after only one bad attempt).
  T4 ALT_NUM_INVALID_TWICE — a second invalid format -> do NOT ask a third time, go straight to
                             NAME+DOB PATH's first question (or straight to DOB if name is
                             already known — same DV set as T5, so this exercises NAME KNOWN
                             CHECK too).
  T5 NAME_KNOWN_DOB_PATH  — caller declines the alt-number offer outright; caller_first_name/
                             caller_last_name are pre-set -> NAME KNOWN CHECK must skip asking
                             for a name and go straight to the DOB question; caller then gives a
                             spoken date form ("the fourteenth of March, nineteen ninety") which
                             must be normalized to YYYY-MM-DD before the tool call, with
                             patient_name built from the known first+last name.
  T6 RESULT_DELIVERY      — a universal_router result with a message field has just returned
                             (found=true) -> MANDATORY PART 1 speaks the message field verbatim,
                             MANDATORY PART 2 calls universal_router intent="wrap_up" in the SAME
                             turn (OUTPUT CONTRACT — producing either without the other is a
                             protocol violation, per the node's own text).

NOT covered (out of scope for this pass, flag before expanding):
  - LEAVE MESSAGE FALLBACK's decline branch — the node's own wording ("say X then call Y in
    the same response as any further exit, or intent=wrap_up if the caller has nothing else")
    is ambiguous about same-turn vs next-turn timing; worth a dedicated, carefully-designed
    test rather than folding it in here where the ambiguity would just produce a noisy result.
  - The YES branch of LEAVE MESSAGE FALLBACK (defers to the system prompt's own LEAVE MESSAGE
    procedure — that procedure has its own coverage elsewhere, not node_1c-specific).
  - PRANK GUARD Strike 2 (system-prompt-level mechanism, not node_1c-specific logic).

Node 1c is Override: Disabled -> system_prompt.txt is prepended to its Additional Prompt
before the scaffold agent is created, matching the runtime context the LLM actually sees
(same convention as test_node6a_scaffold.py in this directory).

STATUS UPDATE 2026-08-20 (later, same day) — NAME KNOWN CHECK garbling fixed; T4 is a
SEPARATE, still-open bug; T5/T6 "failed" labels are an EL evaluator artifact, not real
failures. See project_node1c_scaffold_test_and_bugs_2026_08_20 (session memory) for the
full investigation.
  - FIXED: the garbled "a caller" placeholder patient_name (T5's payload construction).
    node_1c no longer builds patient_name from a DV-conditional at all — three new
    dynamic_variable-backed request params (known_caller_first_name/known_caller_last_name/
    known_patient_name_raw) let the backend resolve the known name itself, zero model
    involvement, same mechanism as caller_id/session_id/practitioner_id. The node's
    NAME+DOB PATH now either relays the name the caller JUST gave this turn, or omits
    patient_name from the payload entirely when it was already known. Verified via raw
    tool-call payload inspection (ground truth params_as_json, not the pass/fail label —
    see session_id_dv_sentinel_bug.md for why that distinction matters): payload is now
    cleanly {"date_of_birth": "1990-03-14"} with patient_name correctly absent, across
    multiple re-runs.
  - EL EVALUATOR ARTIFACT (not a real failure): T5 and T6 both show status="failed" with
    rationale "Expected 0 tool calls, received 1" even though their raw tool calls are
    unambiguously correct (T5: intent=appointment_lookup_retry with a clean payload; T6:
    intent=wrap_up, exactly per OUTPUT CONTRACT). T6's node text was not touched by this
    fix and was previously confirmed working — the same generic rationale string appearing
    on both an untouched, previously-good test and a freshly-fixed one, both with genuinely
    correct tool calls, indicates this is a transient EL Agent-Testing API scoring glitch,
    not a signal about node correctness. Ground truth is always the raw tool_calls array on
    the test run, not the status/rationale field, when the two disagree this blatantly.
  - STILL OPEN, confirmed real (NOT the same bug as the garbling above): the model still
    asks "Can I get your full name?" in T4 even when caller_first_name/caller_last_name are
    unambiguously set. Reproduced 4 times across 3 distinct prompt wordings (the original,
    an "if any of these" rewrite, an "1. If X... Otherwise..." plain-sequential rewrite) AND
    a diagnostic where {{caller_first_name}}/{{caller_last_name}} were pre-substituted as
    literal Python-level text (bypassing EL's own dynamic_variable_placeholders mechanism
    entirely, the same technique that proved the intent-substitution bug) — still asked for
    the name even then, which rules out DV-substitution unreliability as the cause. This is
    a genuine Haiku attention/reasoning limitation specific to this conversational context
    (deep into ALTERNATE NUMBER PATH's two-strikes failure before reaching NAME+DOB PATH),
    not a wording problem — do not attempt another wording-only fix without a new hypothesis.

Usage:
    py -X utf8 nodes/shared/test_node1c_scaffold.py --run
    py -X utf8 nodes/shared/test_node1c_scaffold.py --run --filter T2
    py -X utf8 nodes/shared/test_node1c_scaffold.py --cleanup
    py -X utf8 nodes/shared/test_node1c_scaffold.py --show-prompt
"""

import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import json
import time
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = "https://api.elevenlabs.io/v1/convai"

SHARED_DIR   = Path(__file__).parent
REPO_ROOT    = SHARED_DIR.parent.parent
NODE1C_FILE  = SHARED_DIR / "node_1c_appointment_lookup_recovery.txt"
SYS_PROMPT   = SHARED_DIR / "system_prompt.txt"

# Node 1c only calls universal_router (TOOL ROLES line) — same tool set convention as
# every other Override:Disabled scaffold test in this repo (see UNIVERSAL_ROUTER_TOOL_ID
# grep across nodes/clinics/*/test_node*_scaffold.py).
UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"

SCAFFOLD_LLM       = "claude-haiku-4-5"   # must match production LLM for node 1c
POLL_INTERVAL_SECS = 14
POLL_TIMEOUT_SECS  = 300

_SESSION_FILE = SHARED_DIR / "node1c_scaffold_agent.json"
_PASSED_FILE  = SHARED_DIR / "node1c_passed_tests.json"


# ── Prompt loading ────────────────────────────────────────────────────────────

def strip_node_header(content: str) -> str:
    idx = content.find("Additional Prompt:")
    if idx == -1:
        return content.strip()
    after = content[idx + len("Additional Prompt:"):]
    return after.lstrip("\r\n").strip()


CANDIDATE_FILE = SHARED_DIR / "node_1c_appointment_lookup_recovery.candidate.txt"


def load_node1c_prompt(candidate: bool = False) -> Optional[str]:
    """Node 1c is (currently) Override: Disabled -> runs combined with the shared system
    prompt by default. --candidate loads the Override:Enabled rewrite instead — a fully
    self-contained prompt with NO system_prompt.txt prepend, matching what Override:Enabled
    actually means at runtime (see project_node1c_scaffold_test_and_bugs_2026_08_20 memory
    note for why this rewrite exists — the shared system prompt's PATIENT APPOINTMENT LOOKUP
    block was the confirmed root cause of two real bugs)."""
    if candidate:
        if not CANDIDATE_FILE.exists():
            print(f"✗ Candidate file not found: {CANDIDATE_FILE}")
            return None
        node_text = strip_node_header(CANDIDATE_FILE.read_text(encoding="utf-8"))
        print(f"✓ Loaded node_1c CANDIDATE (Override:Enabled, self-contained) — "
              f"{len(node_text):,} chars total, no system_prompt.txt prepended")
        return node_text

    if not NODE1C_FILE.exists():
        print(f"✗ Node 1c file not found: {NODE1C_FILE}")
        return None
    if not SYS_PROMPT.exists():
        print(f"✗ system_prompt.txt not found: {SYS_PROMPT}")
        return None

    node_text = strip_node_header(NODE1C_FILE.read_text(encoding="utf-8"))
    sys_text = SYS_PROMPT.read_text(encoding="utf-8").strip()
    combined = f"{sys_text}\n\n{node_text}"
    print(f"✓ Loaded node_1c — system_prompt ({len(sys_text):,} chars) "
          f"+ additional_prompt ({len(node_text):,} chars) = {len(combined):,} chars total")
    return combined


# ── Dynamic variable placeholders ───────────────────────────────────────────────
#
# One fixed DV set for the whole agent (ElevenLabs sets dynamic_variable_placeholders
# at agent-creation/patch time, not per-test — same constraint every scaffold test in
# this repo works within). appointment_lookup_intent is deliberately "details_past"
# (not the more common "details") specifically so T2/T5 catch a hardcoded intent="details"
# — the node's own RETRY INTENT rule explicitly warns against that mistake.
# caller_first_name/caller_last_name are pre-set so T4/T5 can exercise NAME KNOWN CHECK.

_DVS = {
    # Identity / caller
    "caller_phone":              "+61411111111",
    "caller_id":                 "+61411111111",
    "system__caller_id":         "+61452851341",   # Telnyx SIP proxy — should not be used
    "caller_first_name":         "Karlee",
    "caller_last_name":          "Mercuri",
    "caller_email":              "",
    "patient_name_raw":          "",
    # Call routing
    "called_number":             "+61285318641",
    "system__called_number":     "+61285318641",
    "system__conversation_id":   "test-conv-001",
    "session_id":                "test-session-001",
    # appointment_lookup_intent is still set as a DV by the original failed lookup (kept for
    # observability), but node_1c no longer reads it into a tool call — it always sends the
    # fixed literal intent="appointment_lookup_retry" (see STATUS UPDATE in the file docstring).
    "appointment_lookup_intent": "details_past",
    "appointment_lookup_failed": "true",
    # Flags this node's own text references
    "uni_router_intent":         "",
    "wrap_routing_flag":         "",
    # name_known_instruction: see NAME_KNOWN_INSTRUCTION_SKIP / presubstitute_name_known_
    # instruction below — kept here too (harmless either way) but the test run does NOT rely
    # on this dict alone to land it in the prompt.
    "name_known_instruction":    "",
}

# T4/T5 both need {{name_known_instruction}} to resolve to the "already known" branch
# (caller_first_name/caller_last_name above are pre-set to exercise exactly that case).
# Must be byte-identical to _node1c_name_known_instruction()'s "known" branch in
# tools/universal_router_webhook.py — kept as a literal copy rather than importing across
# the tools/ <-> nodes/ package boundary.
NAME_KNOWN_INSTRUCTION_SKIP = (
    "the caller's name is already known — skip the name question entirely. "
    "Immediately ask: 'And what's your date of birth?' Stop and wait for the "
    "caller's answer."
)


def presubstitute_name_known_instruction(prompt: str) -> str:
    """Bake {{name_known_instruction}} into literal text before agent creation.

    test_node6a_phone_skip_scaffold.py's own investigation (same phone_known-style DV
    pattern) found EL's run-tests simulation does not reliably substitute a
    dynamic_variable_placeholders value into prompt TEXT the way a real live call does —
    presubstitution is the proven-reliable technique in this repo for exactly this shape of
    test (a DV whose value is itself a MANDATORY instruction sentence, not a tool-call
    parameter). _DVS above still carries the same value for realism/defense-in-depth, but
    this presubstitution is what the T4/T5 result should actually be trusted against.
    """
    return prompt.replace("{{name_known_instruction}}", NAME_KNOWN_INSTRUCTION_SKIP)


# ── Test helpers ──────────────────────────────────────────────────────────────

def _m(role: str, text: str, t: int = 0) -> Dict:
    return {"role": role, "message": text, "time_in_call_secs": t}

def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}

def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}


ENTRY_MSG = (
    "Our system finds appointments by the number you're calling from, and I wasn't able to "
    "match it. Is the appointment maybe under a different number?"
)


# ── Test generation ────────────────────────────────────────────────────────────

def generate_tests() -> List[Dict]:
    tests = []

    # ── T1 — ENTRY: MANDATORY PART 1, no tool call ────────────────────────────
    # KNOWN EL HARNESS LIMITATION (not a node bug — do not "fix" node_1c to chase this):
    # EL's test API rejects a genuinely empty chat_history (422 "must have at least 1 item"),
    # but node_1c's entry_behavior is "auto" — in production it speaks with ZERO prior turns
    # in its own context. Every seed tried backfires differently: a live caller question
    # primes a fresh tool call; a single generic filler line ("One moment.") with nothing to
    # react to has produced a hallucinated intent="initialize_call" tool call (not a real
    # universal_router intent anywhere in this codebase) rather than the ENTRY line. This
    # looks like an artifact of the model having no coherent prior narrative to ground itself
    # in, not a real failure mode any live call could reach — node_1c only ever gets entered
    # via a real edge with real preceding call history, never a bare single line.
    # Kept as best-effort coverage; treat a T1 fail as inconclusive unless reproduced with a
    # more realistic seed, and prioritize T2–T6 for real signal.
    tests.append({
        "name": "[node1c] T1 ENTRY — exact opening line, no tool call, stops for caller",
        "chat_history": [
            _m("agent", "One moment.", 1),
        ],
        "success_condition": (
            "This is the very first turn of the node — a phone-based appointment lookup on the "
            "caller's own number has already failed, but the caller has not been told this yet. "
            "PASS: the agent's spoken output is exactly (or a near-verbatim match of) "
            f'"{ENTRY_MSG}" — asking whether the appointment might be under a different number. '
            "There is NO tool call in this turn. "
            "FAIL: the agent calls any tool this turn, asks for name/DOB before offering the "
            "alternate-number option, or says anything materially different from the exact line."
        ),
        "success_examples": [_ok(ENTRY_MSG)],
        "failure_examples": [
            _fail("Can I get your name please?"),
            _fail("[calls universal_router]"),
            _fail("I'm sorry, I couldn't find your appointment. What's your name?"),
        ],
    })

    # ── T2 — ALT_NUM_VALID: correct payload + fixed-literal intent ────────────
    tests.append({
        "name": "[node1c] T2 ALT_NUM_VALID — valid alt number: filler + retry with correct intent",
        "chat_history": [
            _m("agent", ENTRY_MSG, 2),
            _m("user", "Oh sure, try 0412 345 678.", 6),
        ],
        "success_condition": (
            'The caller gave a valid alternate number ("0412 345 678") in response to the ENTRY '
            "question. Agent speaks one filler phrase from the TOOL-CALL FILLER set (\"One "
            "moment.\" / \"Just a sec.\" / \"Let me check that.\" or equivalent), then calls "
            'universal_router with intent="appointment_lookup_retry" (a FIXED LITERAL value — '
            'never "details" or "details_past" directly; the backend resolves which lookup to '
            'retry on its own from session state) and payload={"patient_phone": "0412345678"} '
            '— digits only, no spaces or hyphens. Does NOT ask for another number. Does NOT ask '
            "for name or DOB this turn."
        ),
        "success_examples": [
            _ok('One moment. [calls universal_router intent=appointment_lookup_retry payload={"patient_phone":"0412345678"}]'),
            _ok('Let me check that. [calls universal_router intent=appointment_lookup_retry patient_phone=0412345678]'),
        ],
        "failure_examples": [
            _fail("What's your date of birth?"),
            _fail('[calls universal_router intent=details ...] — must be the literal appointment_lookup_retry, not details'),
            _fail('[calls universal_router intent=details_past ...] — must be the literal appointment_lookup_retry, not details_past'),
            _fail('[calls universal_router payload={"patient_phone": "0412 345 678"}] — not digits-only'),
            _fail("[no tool call]"),
        ],
    })

    # ── T3 — ALT_NUM_INVALID_ONCE: one re-ask only ────────────────────────────
    tests.append({
        "name": "[node1c] T3 ALT_NUM_INVALID_ONCE — one bad format: single re-ask, no tool call",
        "chat_history": [
            _m("agent", ENTRY_MSG, 2),
            _m("user", "Yeah, it's under, um, my dog's name I think?", 6),
        ],
        "success_condition": (
            "The caller's reply contains no extractable phone number (fewer than 8 digits after "
            "stripping non-digit characters) — an invalid format on the FIRST attempt. PASS: the "
            'agent says something equivalent to "That doesn\'t look right — can you give me the '
            'number again?" and does NOT call any tool this turn. Does NOT jump straight to '
            "asking for a name or DOB yet — only ONE invalid attempt has occurred so far, so "
            "NAME+DOB PATH must not fire yet."
        ),
        "success_examples": [
            _ok("That doesn't look right — can you give me the number again?"),
            _ok("Hmm, that doesn't quite look like a number — could you say it again?"),
        ],
        "failure_examples": [
            _fail("Can I get your full name?"),
            _fail("[calls universal_router]"),
            _fail("What's your date of birth?"),
        ],
    })

    # ── T4 — ALT_NUM_INVALID_TWICE: second invalid -> straight to NAME+DOB PATH ──
    tests.append({
        "name": "[node1c] T4 ALT_NUM_INVALID_TWICE — second bad format: no third re-ask, moves to DOB (name known)",
        "chat_history": [
            _m("agent", ENTRY_MSG, 2),
            _m("user", "It's under my dog's name I think?", 6),
            _m("agent", "That doesn't look right — can you give me the number again?", 9),
            _m("user", "Sorry, I really don't remember the number.", 13),
        ],
        "success_condition": (
            "This is the SECOND consecutive invalid/unusable alternate-number attempt. PASS: the "
            "agent does NOT ask for the number a third time — it moves to NAME+DOB PATH. Since "
            "{{caller_first_name}} (\"Karlee\") and {{caller_last_name}} (\"Mercuri\") are already "
            "set, NAME KNOWN CHECK means the agent does NOT ask for a name — it goes straight to "
            'asking "And what\'s your date of birth?" (or a close paraphrase). Does NOT call any '
            "tool this turn (DOB has not been given yet)."
        ),
        "success_examples": [
            _ok("No worries — let's try a different way. And what's your date of birth?"),
            _ok("That's okay. What's your date of birth?"),
        ],
        "failure_examples": [
            _fail("Can you give me the number one more time?"),
            _fail("Can I get your full name?"),
            _fail("[calls universal_router]"),
        ],
    })

    # ── T5 — NAME_KNOWN_DOB_PATH: decline alt-number entirely, name known, DOB normalized ──
    tests.append({
        "name": "[node1c] T5 NAME_KNOWN_DOB_PATH — declines alt number, name skipped, DOB normalized + payload correct",
        "chat_history": [
            _m("agent", ENTRY_MSG, 2),
            _m("user", "No, it's under my own number, I don't have another one.", 6),
            _m("agent", "No worries — let's try a different way. And what's your date of birth?", 10),
            _m("user", "The fourteenth of March, nineteen ninety.", 14),
        ],
        "success_condition": (
            "The caller declined the alternate-number offer and step 1 of NAME+DOB PATH already "
            "skipped asking for a name (caller_first_name=\"Karlee\", caller_last_name=\"Mercuri\" "
            "are set). The caller has now given a spoken date of birth (\"the fourteenth of March, "
            "nineteen ninety\"). PASS: agent speaks one filler phrase, then calls universal_router "
            'with intent="appointment_lookup_retry" (a FIXED LITERAL value — never "details" or '
            '"details_past" directly), and payload={"date_of_birth": "1990-03-14"} — date '
            "normalized to YYYY-MM-DD. patient_name must be OMITTED from the payload entirely "
            "(the backend resolves the known name itself from known_caller_first_name/"
            "known_caller_last_name DVs — the agent must NOT write \"Karlee Mercuri\" or any "
            "other name/placeholder into a patient_name field). Does NOT ask for the date again. "
            "Does NOT ask for a name (already known)."
        ),
        "success_examples": [
            _ok('One moment. [calls universal_router intent=appointment_lookup_retry payload={"date_of_birth":"1990-03-14"}]'),
        ],
        "failure_examples": [
            _fail("Can I get your full name?"),
            _fail('[calls universal_router payload={"date_of_birth": "March 14, 1990"}] — not normalized to YYYY-MM-DD'),
            _fail('[calls universal_router intent=details ...] — must be the literal appointment_lookup_retry, not details'),
            _fail('[calls universal_router intent=details_past ...] — must be the literal appointment_lookup_retry, not details_past'),
            _fail('[calls universal_router payload={"patient_name": "a caller", "date_of_birth": "1990-03-14"}] — must not fabricate/reconstruct a name value itself'),
            _fail("Can you give me your date of birth again?"),
            _fail("[no tool call]"),
        ],
    })

    # ── T6 — RESULT_DELIVERY: speak message verbatim + call wrap_up, same turn ──
    fixture_result = {"success": True, "message": "Great news — I found your appointment. You're booked for Tuesday at 3 PM with Dr. Chen."}
    tests.append({
        "name": "[node1c] T6 RESULT_DELIVERY — speak message verbatim AND call wrap_up, same turn",
        "chat_history": [
            _m("agent", ENTRY_MSG, 2),
            _m("user", "Try 0412 345 678.", 6),
            # Single fixture turn representing the just-returned tool result — matches the
            # proven convention used elsewhere in this repo (see
            # nodes/clinics/northern_physio/test_node3_confirmation_only.py's fixture_msg) —
            # NOT a separate fake "One moment. [calls ...]" turn beforehand, which the model
            # reads as literal prior speech rather than a completed tool interaction (found
            # live in an earlier run of this test).
            _m("agent", f"[universal_router response received]: {json.dumps(fixture_result)}", 9),
        ],
        "success_condition": (
            "The universal_router retry just returned a result with success=true and a message "
            "field (\"Great news — I found your appointment. You're booked for Tuesday at 3 PM "
            "with Dr. Chen.\"). PASS: in the SAME turn, the agent (1) speaks that message field "
            "verbatim — no paraphrase, no added opener, no added closer — AND (2) calls "
            'universal_router with intent="wrap_up". Both must appear in this one turn — '
            "producing only the speech, or only the tool call, is a FAIL (the node's own OUTPUT "
            "CONTRACT: producing either without the other is a protocol violation)."
        ),
        "success_examples": [
            _ok("Great news — I found your appointment. You're booked for Tuesday at 3 PM with Dr. Chen. [calls universal_router intent=wrap_up]"),
        ],
        "failure_examples": [
            _fail("Great news — I found your appointment. You're booked for Tuesday at 3 PM with Dr. Chen."),  # speech only, no tool call
            _fail("[calls universal_router intent=wrap_up]"),  # tool call only, no speech
            _fail("Perfect! I found it — you're all set for Tuesday at 3 PM. Anything else? [calls universal_router intent=wrap_up]"),  # paraphrased/embellished
        ],
    })

    return tests


# ── ElevenLabs API helpers ──────────────────────────────────────────────────────

def _hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def create_scaffold_agent(prompt: str) -> Optional[str]:
    payload = {
        "name": "[Node1c Test] appointment-lookup-recovery",
        "conversation_config": {
            "agent": {
                "first_message": "",
                "prompt": {
                    "prompt": prompt,
                    "llm": SCAFFOLD_LLM,
                    "tool_ids": [UNIVERSAL_ROUTER_TOOL_ID],
                    "temperature": 0.0,
                    "max_tokens": 1024,
                },
                "dynamic_variables": {"dynamic_variable_placeholders": _DVS},
            },
            "conversation": {"text_only": True},
        },
    }
    resp = requests.post(f"{BASE_URL}/agents/create", headers=_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        agent_id = resp.json().get("agent_id")
        print(f"✓ Scaffold agent created: {agent_id}")
        print(f"  Use --agent-id {agent_id} to reuse in future runs.")
        return agent_id
    print(f"✗ Failed to create agent: {resp.status_code} — {resp.text[:300]}")
    return None


def patch_scaffold_agent_prompt(agent_id: str, prompt: str) -> bool:
    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {"prompt": prompt},
                "dynamic_variables": {"dynamic_variable_placeholders": _DVS},
            }
        }
    }
    resp = requests.patch(f"{BASE_URL}/agents/{agent_id}", headers=_hdrs(), json=payload)
    if resp.status_code == 200:
        print(f"✓ Prompt patched on agent {agent_id}")
        return True
    print(f"✗ Failed to patch agent: {resp.status_code} — {resp.text[:200]}")
    return False


def verify_agent_alive(agent_id: str) -> bool:
    return requests.get(f"{BASE_URL}/agents/{agent_id}", headers=_hdrs()).status_code == 200


def delete_scaffold_agent(agent_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agents/{agent_id}", headers=_hdrs())
    if resp.status_code in (200, 204):
        print(f"✓ Agent {agent_id} deleted.")
    else:
        print(f"✗ Failed to delete agent {agent_id}: {resp.status_code}")


def push_test(t: Dict) -> Optional[str]:
    payload = {
        "name": t["name"],
        "chat_history": t["chat_history"],
        "success_condition": t["success_condition"],
        "success_examples": t.get("success_examples", []),
        "failure_examples": t.get("failure_examples", []),
    }
    resp = requests.post(f"{BASE_URL}/agent-testing/create", headers=_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        return data.get("test_id") or data.get("id")
    print(f"  ✗ Failed to create '{t['name']}': {resp.status_code} — {resp.text[:200]}")
    return None


def delete_test(test_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agent-testing/{test_id}", headers=_hdrs())
    if resp.status_code not in (200, 204):
        print(f"  ✗ Failed to delete test {test_id}: {resp.status_code}")


def dispatch_tests(agent_id: str, test_ids: List[str]) -> Optional[str]:
    payload = {"tests": [{"test_id": tid} for tid in test_ids]}
    resp = requests.post(f"{BASE_URL}/agents/{agent_id}/run-tests", headers=_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        inv_id = data.get("invocation_id") or data.get("id")
        print(f"✓ Tests dispatched — invocation: {inv_id}")
        return inv_id
    print(f"✗ Failed to dispatch tests: {resp.status_code} — {resp.text[:300]}")
    return None


def poll_invocation(invocation_id: str) -> Optional[Dict]:
    deadline = time.time() + POLL_TIMEOUT_SECS
    while time.time() < deadline:
        resp = requests.get(f"{BASE_URL}/test-invocations/{invocation_id}", headers=_hdrs())
        if resp.status_code == 200:
            data = resp.json()
            runs = data.get("test_runs", [])
            pending = sum(1 for r in runs if r.get("status") not in ("passed", "failed"))
            if runs and pending == 0:
                return data
            elapsed = int(time.time() - (deadline - POLL_TIMEOUT_SECS))
            print(f"  … [{elapsed}s] {len(runs) - pending}/{len(runs)} done — waiting {POLL_INTERVAL_SECS}s …")
        time.sleep(POLL_INTERVAL_SECS)
    print(f"✗ Timed out after {POLL_TIMEOUT_SECS}s")
    return None


def _fingerprint(chat_history: List[Dict]) -> str:
    user_msgs = [m["message"] for m in chat_history if m.get("role") == "user"]
    last_msg = chat_history[-1]["message"] if chat_history else ""
    return f"{user_msgs[0] if user_msgs else ''}||{last_msg}"


def _build_name_map(runs: List[Dict], tests: List[Dict]) -> Dict[str, str]:
    test_fp = {_fingerprint(t["chat_history"]): t["name"] for t in tests}
    name_map = {}
    for run in runs:
        ti = run.get("test_info", {}) or {}
        hist = ti.get("chat_history", [])
        name_map[run["test_run_id"]] = test_fp.get(_fingerprint(hist), run["test_run_id"])
    return name_map


def print_results(result: Dict, name_map: Dict[str, str]) -> set:
    runs = result.get("test_runs", [])
    newly_passed = set()
    passed_runs = [r for r in runs if r.get("status") == "passed"]
    failed_runs = [r for r in runs if r.get("status") != "passed"]

    print(f"\n── Results ({'✓' if not failed_runs else '✗'} {len(passed_runs)}/{len(runs)}) ─────────────────────────")

    if passed_runs:
        print(f"\n  PASSED ({len(passed_runs)})")
        for r in passed_runs:
            name = name_map.get(r["test_run_id"], r["test_run_id"])
            print(f"  ✓  {name}")
            newly_passed.add(name)

    if failed_runs:
        print(f"\n  FAILED ({len(failed_runs)})")
        for r in failed_runs:
            name = name_map.get(r["test_run_id"], r["test_run_id"])
            agent_responses = r.get("agent_responses") or []
            agent_msg = next(
                (str(x.get("message") or "") for x in agent_responses if x.get("role") == "agent"),
                "[no spoken output]",
            )
            all_tool_calls = []
            for resp in agent_responses:
                if resp.get("role") == "agent":
                    all_tool_calls.extend(resp.get("tool_calls") or [])
            tool_names = [tc.get("tool_name", "") for tc in all_tool_calls]
            tool_args = [tc.get("parameters") or tc.get("tool_input") or tc.get("arguments") or {}
                         for tc in all_tool_calls]
            ev = r.get("evaluation") or {}
            rationale = ev.get("rationale") or ""
            print(f"  ✗  {name}")
            print(f"       Agent: \"{agent_msg[:200]}\"")
            if tool_names:
                print(f"       Tools: {tool_names}")
                for tn, ta in zip(tool_names, tool_args):
                    if ta:
                        print(f"         → {tn}: {json.dumps(ta)[:300]}")
            if rationale:
                print(f"       Reason: {rationale[:200]}")
    print()
    return newly_passed


def load_passed_tests() -> set:
    if _PASSED_FILE.exists():
        return set(json.loads(_PASSED_FILE.read_text(encoding="utf-8")))
    return set()


def save_passed_tests(passed: set) -> None:
    _PASSED_FILE.write_text(json.dumps(sorted(passed), indent=2), encoding="utf-8")


def load_session_agent() -> Optional[str]:
    if _SESSION_FILE.exists():
        try:
            return json.loads(_SESSION_FILE.read_text(encoding="utf-8")).get("agent_id")
        except Exception:
            return None
    return None


def save_session_agent(agent_id: str) -> None:
    _SESSION_FILE.write_text(json.dumps({"agent_id": agent_id}, indent=2), encoding="utf-8")


def clear_session_agent() -> None:
    if _SESSION_FILE.exists():
        _SESSION_FILE.unlink()


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    global _SESSION_FILE, _PASSED_FILE

    parser = argparse.ArgumentParser(description="Node 1c (appointment lookup recovery) scaffold test — 6 tests, not full coverage")
    parser.add_argument("--run", action="store_true", help="Execute the tests after pushing")
    parser.add_argument("--agent-id", help="Reuse a specific EL scaffold agent ID (bypasses session management, never auto-deleted)")
    parser.add_argument("--cleanup", action="store_true", help="Delete the session agent and exit")
    parser.add_argument("--keep-agent", action="store_true", help="Keep agent alive even if all tests pass")
    parser.add_argument("--show-prompt", action="store_true", help="Print the combined prompt and exit")
    parser.add_argument("--reset", action="store_true", help="Ignore previously passed tests and run everything")
    parser.add_argument("--filter", default="", help="Only run tests whose name contains this string (e.g. 'T2')")
    parser.add_argument("--candidate", action="store_true",
                         help="Test the Override:Enabled self-contained rewrite "
                              "(node_1c_appointment_lookup_recovery.candidate.txt) instead of "
                              "the current live Override:Disabled file + system_prompt.txt. "
                              "Uses a separate scaffold agent + pass registry so it never "
                              "collides with the baseline's state.")
    args = parser.parse_args()

    if args.candidate:
        _SESSION_FILE = SHARED_DIR / "node1c_candidate_scaffold_agent.json"
        _PASSED_FILE = SHARED_DIR / "node1c_candidate_passed_tests.json"

    if not ELEVENLABS_API_KEY:
        print("✗ ELEVENLABS_API_KEY not set in environment / .env")
        sys.exit(1)

    if args.show_prompt:
        prompt = load_node1c_prompt(candidate=args.candidate)
        if prompt:
            prompt = presubstitute_name_known_instruction(prompt)
            print("\n" + "=" * 60 + " COMBINED PROMPT " + "=" * 60)
            print(prompt)
        sys.exit(0)

    if args.cleanup:
        agent_id = args.agent_id or load_session_agent()
        if agent_id:
            delete_scaffold_agent(agent_id)
            clear_session_agent()
        else:
            print("No session agent found.")
        sys.exit(0)

    prompt = load_node1c_prompt(candidate=args.candidate)
    if not prompt:
        sys.exit(1)
    _had_token = "{{name_known_instruction}}" in prompt
    prompt = presubstitute_name_known_instruction(prompt)
    if _had_token:
        print(f"✓ {{{{name_known_instruction}}}} presubstituted with the 'already known' branch "
              f"({len(NAME_KNOWN_INSTRUCTION_SKIP)} chars) — see test_node6a_phone_skip_scaffold.py "
              f"for why presubstitution, not dynamic_variable_placeholders alone, is used here.")

    all_tests = generate_tests()
    previously_passed = set() if args.reset else load_passed_tests()

    if args.filter:
        all_tests = [t for t in all_tests if args.filter.lower() in t["name"].lower()]
        print(f"✓ Filter '{args.filter}' matched {len(all_tests)} tests")

    tests_to_run = all_tests
    if previously_passed:
        tests_to_run = [t for t in all_tests if t["name"] not in previously_passed]
        skipped = len(all_tests) - len(tests_to_run)
        print(f"✓ Generated {len(all_tests)} tests — skipping {skipped} already passing, running {len(tests_to_run)}")
    else:
        print(f"✓ Generated {len(all_tests)} test cases (6 max by design — see file docstring for scope)")

    if not tests_to_run:
        print("✓ All tests already passing — nothing to run.")
        print("  Use --reset to force a full re-run.")
        return

    agent_id = args.agent_id
    session_managed = False

    if agent_id:
        print(f"Patching prompt on pinned agent {agent_id}...")
        if not patch_scaffold_agent_prompt(agent_id, prompt):
            sys.exit(1)
        time.sleep(5)
    else:
        session_managed = True
        existing = load_session_agent()
        if existing:
            if verify_agent_alive(existing):
                print(f"✓ Session agent found: {existing}")
                if patch_scaffold_agent_prompt(existing, prompt):
                    agent_id = existing
                    time.sleep(5)
                else:
                    clear_session_agent()
            else:
                print(f"  Session agent {existing} no longer exists — creating fresh.")
                clear_session_agent()

        if not agent_id:
            agent_id = create_scaffold_agent(prompt)
            if not agent_id:
                sys.exit(1)
            save_session_agent(agent_id)
            time.sleep(3)

    print(f"\nPushing {len(tests_to_run)} test(s) …")
    test_ids = []
    for t in tests_to_run:
        tid = push_test(t)
        if tid:
            test_ids.append(tid)
            print(f"  ✓ {t['name']}")

    if not test_ids:
        print("✗ No tests pushed — aborting.")
        sys.exit(1)

    if not args.run:
        print(f"\n✓ {len(test_ids)} test(s) pushed. Re-run with --run to execute.")
        sys.exit(0)

    print(f"\nDispatching {len(test_ids)} test(s) against agent {agent_id} …")
    inv_id = dispatch_tests(agent_id, test_ids)
    if not inv_id:
        sys.exit(1)

    print("\nPolling for results …")
    inv_data = poll_invocation(inv_id)
    if inv_data is None:
        print("✗ No results received.")
        sys.exit(1)

    name_map = _build_name_map(inv_data.get("test_runs", []), tests_to_run)
    newly_passed = print_results(inv_data, name_map)

    for tid in test_ids:
        delete_test(tid)

    if newly_passed:
        updated_passed = previously_passed | newly_passed
        save_passed_tests(updated_passed)
        print(f"✓ Pass registry updated — {len(updated_passed)} test(s) now marked passing.")
    else:
        updated_passed = previously_passed

    n_total = len(inv_data.get("test_runs", []))
    failures = n_total - len(newly_passed)
    all_pass = len(updated_passed) == len(all_tests)

    if session_managed:
        if all_pass and not args.keep_agent:
            print(f"✓ All {len(all_tests)} test(s) passing — deleting scaffold agent.")
            delete_scaffold_agent(agent_id)
            clear_session_agent()
        elif all_pass:
            print(f"ℹ  All tests passing — agent kept (--keep-agent): {agent_id}")
        else:
            remaining = len(all_tests) - len(updated_passed)
            print(f"ℹ  {remaining} test(s) still failing — scaffold agent retained: {agent_id}")

    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
