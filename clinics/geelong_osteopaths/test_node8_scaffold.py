#!/usr/bin/env python3
"""
test_node8_scaffold.py  (Geelong Osteopaths)

Tests Node 8 (Information Handler) routing behaviour.

Every test follows the same pattern:
  1. Caller asks an information question.
  2. Agent answers and asks "Did you have any other questions?"
  3. Caller says something that should trigger (or not trigger) a universal_router call.
  The test verifies the correct intent and payload fields.

Test groups
  R  — NO HANDLER: caller signals done → info_answered
  B  — BOOKING SIGNAL HANDLER: caller expresses booking intent → info_answered
  S  — BLOCKING SIGNALS: cancel / reschedule / wrap-up / leave-message / running-late
  E  — EDGE CASES: bare "yes", follow-up question, speak to practitioner
  X  — CONTEXT ISOLATION: mid-booking arrival; confirms Node 8 doesn't continue prior node's flow

Usage:
    python nodes/clinics/geelong_osteopaths/test_node8_scaffold.py --create --run
    python nodes/clinics/geelong_osteopaths/test_node8_scaffold.py --run
    python nodes/clinics/geelong_osteopaths/test_node8_scaffold.py --cleanup
    python nodes/clinics/geelong_osteopaths/test_node8_scaffold.py --spec-only
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

CLINIC_DIR = Path(__file__).parent
CLINIC = "geelong_osteopaths"

UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"
SMART_ROUTER_TOOL_ID     = "tool_4501k96qzckzemabz9rwppjms6zj"

SCAFFOLD_LLM       = "gpt-4.1"
POLL_INTERVAL_SECS = 12
POLL_TIMEOUT_SECS  = 360

_SESSION_FILE = CLINIC_DIR / "node8_scaffold_agent.json"

# ── Shared constants for test construction ────────────────────────────────────

# Address Q&A — used as the "prior info answer" in most tests
_ADDR_Q = "what's the address?"
_ADDR_A = (
    "The Geelong West Osteopaths is at 34 Shannon Ave, Geelong West VIC 3218. "
    "Did you have any other questions?"
)

# Hours Q&A — used as an alternate info answer to avoid test fingerprint collisions
_HRS_Q = "what are your opening hours?"
_HRS_A = (
    "We're open Monday to Friday from 8am to 6pm, and Saturday mornings from 8am to 1pm. "
    "Did you have any other questions?"
)

# Prefix used in all test names
P = f"[{CLINIC}]"

# ── Dynamic variable placeholders ─────────────────────────────────────────────

_DYNAMIC_VAR_PLACEHOLDERS = {
    "called_number":             "+61000000000",
    "caller_id":                 "+61111111111",
    "system__called_number":     "+61000000000",
    "system__caller_id":         "+61111111111",
    "service_categories":        "Osteopathy",
    "location_addresses":        "Geelong West Osteopaths=34 Shannon Ave, Geelong West VIC 3218",
    "practitioners_comma":       "Sarah Miller, James Chen",
    "practitioner_services":     (
        "Sarah Miller: Osteopathy New Patient, Osteopathy Return; "
        "James Chen: Osteopathy New Patient, Osteopathy Return"
    ),
    "practitioner_genders":      "Sarah Miller=female, James Chen=male",
    "service_ids":               "Osteopathy New Patient=213916, Osteopathy Return=213928",
    # Booking-flow context variables (set by prior nodes in production)
    "uni_router_intent":         "",
    "reschedule_mode":           "",
    "booking_for":               "self",
    "patient_status":            "",
    "appointment_type":          "Osteopathy New Patient",
    "appointment_type_id":       "213916",
    "wrap_routing_flag":         "",
    "return_node":               "",
    "info_answered":             "",
    "implied_service":           "",
    "timeframe_raw":             "",
    "practitioner_preference":   "",
    "preferred_gender":          "",
    "patient_name_raw":          "",
    "first_name":                "",
    "last_name":                 "",
    "reschedule_mode":           "",
}

# ── Prompt loading ────────────────────────────────────────────────────────────

def strip_node_header(content: str) -> str:
    lines = content.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "Additional Prompt:":
            start = i + 1
            while start < len(lines) and not lines[start].strip():
                start += 1
            return "\n".join(lines[start:]).strip()
        if stripped.startswith("#") or stripped.startswith("=") or stripped in ("FRAMEWORK", "MINI-FRAMEWORK"):
            return "\n".join(lines[i:]).strip()
    return content.strip()


def load_node8() -> Optional[str]:
    path = CLINIC_DIR / "node_8_information_handler.txt"
    if not path.exists():
        print(f"✗ Node 8 file not found: {path}")
        return None
    content = path.read_text(encoding="utf-8")
    prompt = strip_node_header(content)
    print(f"✓ Loaded Node 8 for '{CLINIC}' ({len(prompt):,} chars)")
    return prompt

# ── Test helpers ──────────────────────────────────────────────────────────────

def _m(role: str, text: str, t: int = 0) -> Dict:
    return {"role": role, "message": text, "time_in_call_secs": t}

def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}

def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}


# ── Test generation ───────────────────────────────────────────────────────────

def generate_tests() -> List[Dict]:
    tests = []

    # ── R group: NO HANDLER — caller signals done → info_answered ────────────
    # These are the "I'm done" phrases listed in the NO HANDLER section.
    # Critical: phrases like "that's all" and "I'm done" must NOT trigger wrap_up.

    no_handler_cases = [
        ("R1", "no",            "bare 'no'"),
        ("R2", "no thanks",     "'no thanks'"),
        ("R3", "nothing else",  "'nothing else'"),
        ("R4", "that's it",     "'that's it'"),
        ("R5", "I'm good",      "'I'm good'"),
        ("R6", "I'm all set",   "'I'm all set'"),
        ("R7", "that's all",    "'that's all' — must NOT trigger wrap_up"),
        ("R8", "I'm done",      "'I'm done' — must NOT trigger wrap_up"),
        ("R9", "that's everything", "'that's everything'"),
    ]

    for code, phrase, label in no_handler_cases:
        # Alternate between address and hours answers to ensure unique fingerprints
        if int(code[1:]) % 2 == 1:
            q, a = _ADDR_Q, _ADDR_A
        else:
            q, a = _HRS_Q, _HRS_A
        tests.append({
            "name": f"{P} {code} — NO HANDLER: {label}",
            "chat_history": [
                _m("user",  q,  2),
                _m("agent", a,  5),
                _m("user",  phrase, 8),
            ],
            "success_condition": (
                f'Agent calls universal_router with intent="info_answered". '
                f'Payload includes info_pivot_source="node_8". '
                f'Tool call is the entirety of this turn — zero spoken output. '
                f'EVALUATOR NOTE: do NOT fail for a silent tool call. '
                f'Specifically: if the phrase is "that\'s all" or "I\'m done", '
                f'intent MUST be "info_answered" not "wrap_up".'
            ),
            "success_examples": [_ok('[silent — calls universal_router intent="info_answered"]')],
            "failure_examples": [
                _fail("Is there anything else I can help with?"),
                _fail('[calls universal_router intent="wrap_up"]'),
                _fail("[no tool call]"),
            ],
        })

    # ── B group: BOOKING SIGNAL HANDLER — explicit booking intent → info_answered

    booking_cases = [
        ("B1", "let's book it",                None,          "explicit booking intent"),
        ("B2", "book me in",                   None,          "direct booking request"),
        ("B3", "I'll take it",                 None,          "'I'll take it' after info"),
        ("B4", "yes, can we book for 9am Tuesday?", "9am Tuesday", "time included — timeframe_raw must be set"),
        ("B5", "great, I'd like to make a booking", None,     "booking intent after info"),
    ]

    for code, phrase, timeframe, label in booking_cases:
        tests.append({
            "name": f"{P} {code} — BOOKING SIGNAL: {label}",
            "chat_history": [
                _m("user",  _ADDR_Q, 2),
                _m("agent", _ADDR_A, 5),
                _m("user",  phrase,  8),
            ],
            "success_condition": (
                f'Agent calls universal_router with intent="info_answered". '
                + (
                    f'Payload must include timeframe_raw="{timeframe}". '
                    if timeframe else
                    ""
                )
                + f'Payload includes info_pivot_source="node_8". '
                f'Tool call is the entirety of this turn — zero spoken output. '
                f'EVALUATOR NOTE: do NOT fail for a silent tool call. '
                f'CRITICAL: intent must be "info_answered" — NOT "confirm_service", '
                f'"confirm_patient_name", or any other booking-specific intent.'
            ),
            "success_examples": [_ok('[silent — calls universal_router intent="info_answered"]')],
            "failure_examples": [
                _fail('[calls universal_router intent="confirm_service"]'),
                _fail('[calls universal_router intent="confirm_patient_name"]'),
                _fail("When would you like to come in?"),
                _fail("[no tool call]"),
            ],
        })

    # ── S group: BLOCKING SIGNALS ─────────────────────────────────────────────

    # S1: Cancel
    tests.append({
        "name": f"{P} S1 — BLOCKING: cancel intent → cancel_intent",
        "chat_history": [
            _m("user",  _ADDR_Q,                          2),
            _m("agent", _ADDR_A,                          5),
            _m("user",  "actually I need to cancel my appointment", 8),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="cancel_intent". '
            'Tool call is the entirety of this turn — zero spoken output. '
            'EVALUATOR NOTE: do NOT fail for a silent tool call.'
        ),
        "success_examples": [_ok('[silent — calls universal_router intent="cancel_intent"]')],
        "failure_examples": [
            _fail('[calls universal_router intent="info_answered"]'),
            _fail("I can help you with that"),
            _fail("[no tool call]"),
        ],
    })

    # S2: Reschedule
    tests.append({
        "name": f"{P} S2 — BLOCKING: reschedule → cancel_intent + reschedule_mode=true",
        "chat_history": [
            _m("user",  _HRS_Q,                  2),
            _m("agent", _HRS_A,                  5),
            _m("user",  "I need to reschedule my appointment", 8),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="cancel_intent" AND reschedule_mode="true". '
            'Both fields must be present. Tool call is the entirety of this turn — zero spoken output.'
        ),
        "success_examples": [
            _ok('[silent — calls universal_router intent="cancel_intent" reschedule_mode="true"]')
        ],
        "failure_examples": [
            _fail('[calls universal_router intent="cancel_intent" without reschedule_mode]'),
            _fail('[calls universal_router intent="info_answered"]'),
            _fail("[no tool call]"),
        ],
    })

    # S3: Wrap-up "bye"
    tests.append({
        "name": f"{P} S3 — BLOCKING: 'bye' → wrap_up",
        "chat_history": [
            _m("user",  _ADDR_Q, 2),
            _m("agent", _ADDR_A, 5),
            _m("user",  "bye",   8),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="wrap_up". '
            'Tool call is the entirety of this turn — zero spoken output. '
            'EVALUATOR NOTE: "bye" is the exact trigger for wrap_up — '
            'do NOT confuse with info_answered.'
        ),
        "success_examples": [_ok('[silent — calls universal_router intent="wrap_up"]')],
        "failure_examples": [
            _fail('[calls universal_router intent="info_answered"]'),
            _fail("Take care, goodbye!"),
            _fail("[no tool call]"),
        ],
    })

    # S4: Wrap-up "goodbye"
    tests.append({
        "name": f"{P} S4 — BLOCKING: 'goodbye' → wrap_up",
        "chat_history": [
            _m("user",  _HRS_Q,    2),
            _m("agent", _HRS_A,    5),
            _m("user",  "goodbye", 8),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="wrap_up". '
            'Tool call is the entirety of this turn — zero spoken output.'
        ),
        "success_examples": [_ok('[silent — calls universal_router intent="wrap_up"]')],
        "failure_examples": [
            _fail('[calls universal_router intent="info_answered"]'),
            _fail("[no tool call]"),
        ],
    })

    # S5: Leave message
    tests.append({
        "name": f"{P} S5 — BLOCKING: leave message request → leave_message flow",
        "chat_history": [
            _m("user",  _ADDR_Q, 2),
            _m("agent", _ADDR_A, 5),
            _m("user",  "can you pass on a message to the team?", 8),
        ],
        "success_condition": (
            'Agent says "What would you like me to pass on?" (or close paraphrase). '
            'Agent does NOT call any tool this turn. '
            'EVALUATOR NOTE: the agent must speak and halt — no tool call yet.'
        ),
        "success_examples": [_ok("What would you like me to pass on?")],
        "failure_examples": [
            _fail('[calls universal_router immediately]'),
            _fail('[calls universal_router intent="info_answered"]'),
            _fail("[no spoken output]"),
        ],
    })

    # S6: Running late
    tests.append({
        "name": f"{P} S6 — BLOCKING: running late → running_late",
        "chat_history": [
            _m("user",  _HRS_Q,                                  2),
            _m("agent", _HRS_A,                                  5),
            _m("user",  "actually I'm running a bit late for my appointment today", 8),
        ],
        "success_condition": (
            'Agent asks for the caller\'s name (if not already known), '
            'then calls universal_router with intent="running_late". '
            'On this turn (name unknown): agent speaks "Can I get your name?" and halts. '
            'EVALUATOR NOTE: asking for the name before the tool call is correct behaviour.'
        ),
        "success_examples": [_ok("Can I get your name?")],
        "failure_examples": [
            _fail('[calls universal_router intent="info_answered"]'),
            _fail("Sure, I'll let them know"),
            _fail("[no spoken output]"),
        ],
    })

    # ── E group: EDGE CASES ───────────────────────────────────────────────────

    # E1: Bare "yes" → YES HANDLER → "Go ahead." (no tool call)
    tests.append({
        "name": f"{P} E1 — EDGE: bare 'yes' → YES HANDLER, no routing",
        "chat_history": [
            _m("user",  _ADDR_Q, 2),
            _m("agent", _ADDR_A, 5),
            _m("user",  "yes",   8),
        ],
        "success_condition": (
            'Agent says "Go ahead." (exact phrase, or close equivalent). '
            'Agent does NOT call universal_router. '
            'No tool call this turn.'
        ),
        "success_examples": [_ok("Go ahead.")],
        "failure_examples": [
            _fail('[calls universal_router intent="info_answered"]'),
            _fail('[calls universal_router intent="wrap_up"]'),
            _fail("Did you have any other questions?"),
        ],
    })

    # E2: Follow-up question → QUESTION HANDLER → answers, no routing
    tests.append({
        "name": f"{P} E2 — EDGE: follow-up question → QUESTION HANDLER, answers again",
        "chat_history": [
            _m("user",  _ADDR_Q,                                   2),
            _m("agent", _ADDR_A,                                   5),
            _m("user",  "and how much does a new patient appointment cost?", 8),
        ],
        "success_condition": (
            'Agent re-evaluates from FAST CLASSIFY and handles the pricing question '
            '(PRICING AND DURATION INTERCEPT). Agent speaks an answer about new patient pricing '
            'or calls smart_router to look it up. '
            'Agent does NOT call universal_router with info_answered this turn. '
            'EVALUATOR NOTE: calling smart_router intent="get_service_price" is CORRECT here.'
        ),
        "success_examples": [
            _ok("Let me check that for you, one moment. [calls smart_router get_service_price]"),
            _ok("A new patient appointment is $[price]. Did you have any other questions?"),
        ],
        "failure_examples": [
            _fail('[calls universal_router intent="info_answered"]'),
            _fail("[no spoken output, no tool call]"),
        ],
    })

    # E3: Speak to practitioner → SPEAK TO PRACTITIONER handler
    tests.append({
        "name": f"{P} E3 — EDGE: speak to practitioner → messaging offer",
        "chat_history": [
            _m("user",  _HRS_Q,                           2),
            _m("agent", _HRS_A,                           5),
            _m("user",  "can I speak to Sarah directly?", 8),
        ],
        "success_condition": (
            'Agent says it\'s not able to transfer calls directly and offers to send an email. '
            'Exact or close paraphrase: "I\'m not able to transfer calls directly — '
            'would you like me to send them an email so they can follow up with you?" '
            'Agent does NOT call universal_router this turn.'
        ),
        "success_examples": [
            _ok("I'm not able to transfer calls directly — would you like me to send them an email?")
        ],
        "failure_examples": [
            _fail('[immediately calls universal_router intent="leave_message"]'),
            _fail('[calls universal_router intent="info_answered"]'),
        ],
    })

    # ── X group: CONTEXT ISOLATION ────────────────────────────────────────────
    # These tests simulate Node 8 being entered mid-booking (from Node 6a name collection).
    # The chat_history contains an active booking flow to create the contamination risk.
    # Critical check: Node 8 must NOT continue the booking flow or call non-Node-8 intents.

    _MID_BOOKING_HISTORY_BASE = [
        _m("user",  "I'd like to book an osteopathy appointment.",           2),
        _m("agent", "Are you a new or returning patient?",                   5),
        _m("user",  "I'm a new patient.",                                    8),
        _m("agent", "Can I have your full name for the booking?",           11),
    ]

    # X1: arrives mid-booking, asks address, then signals done → info_answered (not booking)
    tests.append({
        "name": f"{P} X1 — CONTEXT ISOLATION: mid-booking → address question → 'no thanks' → info_answered",
        "chat_history": _MID_BOOKING_HISTORY_BASE + [
            _m("user",  _ADDR_Q, 14),
            _m("agent", _ADDR_A, 17),
            _m("user",  "no thanks", 20),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="info_answered". '
            'CRITICAL: Agent must NOT ask for the caller\'s name, must NOT continue the booking flow, '
            'and must NOT call universal_router with "confirm_patient_name" or "confirm_service". '
            'Tool call is the entirety of this turn — zero spoken output.'
        ),
        "success_examples": [_ok('[silent — calls universal_router intent="info_answered"]')],
        "failure_examples": [
            _fail('[calls universal_router intent="confirm_patient_name"]'),
            _fail('[calls universal_router intent="confirm_service"]'),
            _fail("Can I have your full name for the booking?"),
            _fail("And what's your last name?"),
            _fail("[no tool call]"),
        ],
    })

    # X2: arrives mid-booking, asks address, then expresses booking intent → info_answered (not confirm_patient_name)
    tests.append({
        "name": f"{P} X2 — CONTEXT ISOLATION: mid-booking → address question → 'let's book' → info_answered",
        "chat_history": _MID_BOOKING_HISTORY_BASE + [
            _m("user",  _ADDR_Q,      14),
            _m("agent", _ADDR_A,      17),
            _m("user",  "let's book", 20),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="info_answered". '
            'CRITICAL: intent must be "info_answered" — NOT "confirm_patient_name", '
            '"confirm_service", or any other booking-specific intent. '
            'Node 8 does not have a booking path. '
            'Tool call is the entirety of this turn — zero spoken output.'
        ),
        "success_examples": [_ok('[silent — calls universal_router intent="info_answered"]')],
        "failure_examples": [
            _fail('[calls universal_router intent="confirm_patient_name"]'),
            _fail('[calls universal_router intent="confirm_service"]'),
            _fail("Can I have your full name for the booking?"),
            _fail("Great, what time works for you?"),
            _fail("[no tool call]"),
        ],
    })

    # X3: arrives mid-booking, asks hours, answers "I'm done" → info_answered (not wrap_up or booking)
    tests.append({
        "name": f"{P} X3 — CONTEXT ISOLATION: mid-booking → hours question → 'I'm done' → info_answered",
        "chat_history": _MID_BOOKING_HISTORY_BASE + [
            _m("user",  _HRS_Q,   14),
            _m("agent", _HRS_A,   17),
            _m("user",  "I'm done", 20),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="info_answered". '
            'CRITICAL: "I\'m done" must NOT trigger wrap_up and must NOT continue the booking flow. '
            'Intent must be "info_answered". '
            'Tool call is the entirety of this turn — zero spoken output.'
        ),
        "success_examples": [_ok('[silent — calls universal_router intent="info_answered"]')],
        "failure_examples": [
            _fail('[calls universal_router intent="wrap_up"]'),
            _fail('[calls universal_router intent="confirm_patient_name"]'),
            _fail("Can I have your full name?"),
            _fail("[no tool call]"),
        ],
    })

    print(f"✓ Generated {len(tests)} tests")
    return tests


# ── ElevenLabs API helpers ────────────────────────────────────────────────────

def _el_hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def create_scaffold_agent(node8_prompt: str) -> Optional[str]:
    payload = {
        "name": f"[Node8 Test] {CLINIC}",
        "conversation_config": {
            "agent": {
                "first_message": "Thanks for calling — how can I help you today?",
                "prompt": {
                    "prompt": node8_prompt,
                    "llm": SCAFFOLD_LLM,
                    "tool_ids": [UNIVERSAL_ROUTER_TOOL_ID, SMART_ROUTER_TOOL_ID],
                    "temperature": 0.0,
                    "max_tokens": 1024,
                },
                "dynamic_variables": {
                    "dynamic_variable_placeholders": _DYNAMIC_VAR_PLACEHOLDERS
                },
            },
            "conversation": {"text_only": True},
        },
    }
    resp = requests.post(f"{BASE_URL}/agents/create", headers=_el_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        agent_id = resp.json().get("agent_id")
        print(f"✓ Scaffold agent created: {agent_id}")
        return agent_id
    print(f"✗ Failed to create agent: {resp.status_code} — {resp.text[:300]}")
    return None


def patch_scaffold_agent(agent_id: str, node8_prompt: str) -> bool:
    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {"prompt": node8_prompt},
                "dynamic_variables": {
                    "dynamic_variable_placeholders": _DYNAMIC_VAR_PLACEHOLDERS
                },
            }
        }
    }
    resp = requests.patch(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs(), json=payload)
    if resp.status_code == 200:
        print(f"✓ Prompt patched on session agent {agent_id}")
        return True
    print(f"✗ Failed to patch agent: {resp.status_code} — {resp.text[:200]}")
    return False


def delete_scaffold_agent(agent_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    if resp.status_code in (200, 204):
        print(f"✓ Agent {agent_id} deleted.")
    else:
        print(f"✗ Failed to delete agent {agent_id}: {resp.status_code}")


def verify_agent_alive(agent_id: str) -> bool:
    resp = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    return resp.status_code == 200


# ── Session file helpers ──────────────────────────────────────────────────────

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


# ── Test lifecycle ────────────────────────────────────────────────────────────

def push_tests(agent_id: str, tests: List[Dict]) -> List[str]:
    test_ids = []
    for t in tests:
        payload = {
            "agent_id": agent_id,
            "name":     t["name"],
            "type":     "llm",
            "criteria": [
                {
                    "type":    "text",
                    "value":   t["success_condition"],
                    "success_examples": t.get("success_examples", []),
                    "failure_examples": t.get("failure_examples", []),
                }
            ],
            "script": {
                "type":         "user_message",
                "messages":     t["chat_history"],
                "user_persona": "",
            },
        }
        resp = requests.post(f"{BASE_URL}/agent-testing", headers=_el_hdrs(), json=payload)
        if resp.status_code in (200, 201):
            tid = resp.json().get("test_id") or resp.json().get("id")
            test_ids.append(tid)
            print(f"  ✓ Created: {t['name']}")
        else:
            print(f"  ✗ Failed {t['name']}: {resp.status_code} — {resp.text[:200]}")
    return test_ids


def delete_test(test_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agent-testing/{test_id}", headers=_el_hdrs())
    if resp.status_code not in (200, 204):
        print(f"  ✗ Failed to delete test {test_id}: {resp.status_code}")


def run_tests(agent_id: str, test_ids: List[str]) -> None:
    run_resp = requests.post(
        f"{BASE_URL}/agent-testing/run",
        headers=_el_hdrs(),
        json={"agent_id": agent_id, "test_ids": test_ids},
    )
    if run_resp.status_code not in (200, 202):
        print(f"✗ Failed to start test run: {run_resp.status_code} — {run_resp.text[:200]}")
        return

    print(f"  Test run started — polling every {POLL_INTERVAL_SECS}s …")
    deadline = time.time() + POLL_TIMEOUT_SECS
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_SECS)
        results = []
        for tid in test_ids:
            r = requests.get(f"{BASE_URL}/agent-testing/{tid}", headers=_el_hdrs())
            if r.status_code == 200:
                results.append(r.json())
        pending = [r for r in results if r.get("status") not in ("passed", "failed", "error")]
        if not pending:
            break
        print(f"    … {len(pending)} still running")

    _print_results(results)


def _print_results(results: List[Dict]) -> None:
    passed = failed = error = 0
    for r in results:
        status = r.get("status", "unknown")
        name   = r.get("name", r.get("id", "?"))
        verdict = r.get("criteria", [{}])[0].get("condition_result", "")
        if status == "passed":
            passed += 1
            print(f"  ✓ PASS  {name}")
        elif status == "failed":
            failed += 1
            print(f"  ✗ FAIL  {name}")
            if verdict:
                print(f"         {verdict[:200]}")
        else:
            error += 1
            print(f"  ? ERR   {name} [{status}]")
    print(f"\n{'='*60}")
    print(f"  {passed} passed  /  {failed} failed  /  {error} error  (total {passed+failed+error})")
    print(f"{'='*60}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Node 8 scaffold tests — Geelong Osteopaths")
    parser.add_argument("--create",     action="store_true", help="Force create a new scaffold agent (deletes existing)")
    parser.add_argument("--run",        action="store_true", help="Push tests and run them")
    parser.add_argument("--cleanup",    action="store_true", help="Delete the session agent and exit")
    parser.add_argument("--spec-only",  action="store_true", help="Print test specs without running")
    parser.add_argument("--keep-agent", action="store_true", help="Don't auto-delete agent on all-pass")
    parser.add_argument("--agent-id",   default=None,        help="Use this agent ID instead of session file")
    args = parser.parse_args()

    if not ELEVENLABS_API_KEY:
        print("✗ ELEVENLABS_API_KEY not set")
        sys.exit(1)

    node8_prompt = load_node8()
    if not node8_prompt:
        sys.exit(1)

    tests = generate_tests()

    if args.spec_only:
        for t in tests:
            print(f"\n{'─'*60}")
            print(f"NAME: {t['name']}")
            print(f"TURNS: {len(t['chat_history'])}")
            last = t['chat_history'][-1]
            print(f"TRIGGER: [{last['role']}] {last['message']}")
            print(f"SUCCESS: {t['success_condition'][:120]}...")
        return

    if args.cleanup:
        agent_id = args.agent_id or load_session_agent()
        if agent_id:
            delete_scaffold_agent(agent_id)
            clear_session_agent()
        else:
            print("No session agent to clean up.")
        return

    # Resolve agent
    agent_id = args.agent_id or load_session_agent()

    if args.create or not agent_id:
        if agent_id and verify_agent_alive(agent_id):
            print(f"  Deleting existing session agent {agent_id} …")
            delete_scaffold_agent(agent_id)
        agent_id = create_scaffold_agent(node8_prompt)
        if not agent_id:
            sys.exit(1)
        save_session_agent(agent_id)
    else:
        if not verify_agent_alive(agent_id):
            print(f"  Session agent {agent_id} not found — creating new one …")
            agent_id = create_scaffold_agent(node8_prompt)
            if not agent_id:
                sys.exit(1)
            save_session_agent(agent_id)
        else:
            patch_scaffold_agent(agent_id, node8_prompt)

    if not args.run:
        print(f"\n  Agent ready: {agent_id}")
        print(f"  Run with: python {Path(__file__).name} --run --agent-id {agent_id}")
        return

    print(f"\n── Pushing {len(tests)} tests to agent {agent_id} …")
    test_ids = push_tests(agent_id, tests)

    if not test_ids:
        print("✗ No tests pushed — aborting run.")
        sys.exit(1)

    print(f"\n── Running {len(test_ids)} tests …")
    run_tests(agent_id, test_ids)


if __name__ == "__main__":
    main()
