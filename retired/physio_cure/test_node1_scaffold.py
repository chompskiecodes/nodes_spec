#!/usr/bin/env python3
"""
test_node1_scaffold.py  (Physio Cure)

Standalone scaffold to test Node 1 (Entry Greeting Router) for Physio Cure — specifically
the RETURNING PATIENT LOOKUP OFFER fix and the INTENT-IN-MESSAGE INTERCEPT GATE fix that
was supposed to stop the offer being skipped in favour of Signal 1.

This runs the REAL prompt (shared system_prompt.txt + this node's Additional Prompt)
against the REAL ElevenLabs agent-testing API (real claude-haiku-4-5 invocation, real
tool schema) — not a local simulation. This is the thing to trust when a meta-simulated
Haiku self-audit passes but a live call still fails: the self-audit reasons about what it
*would* do; this actually invokes the runtime.

Usage:
    py -X utf8 nodes/clinics/physio_cure/test_node1_scaffold.py --run
    py -X utf8 nodes/clinics/physio_cure/test_node1_scaffold.py --run --reset
    py -X utf8 nodes/clinics/physio_cure/test_node1_scaffold.py --cleanup
    py -X utf8 nodes/clinics/physio_cure/test_node1_scaffold.py --agent-id <id> --run
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

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = "https://api.elevenlabs.io/v1/convai"

CLINIC_DIR = Path(__file__).parent
NODES_DIR = CLINIC_DIR.parent

CLINIC = "physio_cure"

# Same fleet-shared universal_router tool ID confirmed live on Physio Cure's own agent
# (agent_5201m29b60hjfhwbdb3bwg7fcvrr) — checked via GET /v1/convai/agents/{id} 2026-09-17.
UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"

SCAFFOLD_LLM = "claude-haiku-4-5"
POLL_INTERVAL_SECS = 10
POLL_TIMEOUT_SECS = 240

_SESSION_FILE = CLINIC_DIR / "node1_scaffold_agent.json"


# ── Node 1 prompt loading ────────────────────────────────────────────────────

def strip_node_header(content: str) -> str:
    lines = content.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == "Additional Prompt:":
            start = i + 1
            break
    return "\n".join(lines[start:]).strip()


def load_node1() -> Optional[str]:
    """Node 1 is Override: Disabled — in production it ALWAYS runs combined with
    nodes/shared/system_prompt.txt. Sending the Additional Prompt alone would be an
    unrepresentative, off-script scaffold."""
    path = CLINIC_DIR / "node_1_entry_greeting_router.txt"
    if not path.exists():
        print(f"X Node 1 file not found: {path}")
        return None
    content = path.read_text(encoding="utf-8")
    additional_prompt = strip_node_header(content)

    sys_path = NODES_DIR.parent / "shared" / "system_prompt.txt"
    if not sys_path.exists():
        print(f"X Shared system prompt not found: {sys_path}")
        return None
    system_prompt = sys_path.read_text(encoding="utf-8").strip()

    prompt = system_prompt + "\n\n" + additional_prompt
    print(f"OK Loaded Node 1 for '{CLINIC}' — system_prompt ({len(system_prompt):,} chars) "
          f"+ additional_prompt ({len(additional_prompt):,} chars) = {len(prompt):,} chars total")
    return prompt


# ── Test helpers ─────────────────────────────────────────────────────────────

def _m(role: str, text: str, t: int = 0) -> Dict:
    return {"role": role, "message": text, "time_in_call_secs": t}


def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}


def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}


# STEP 1 has two wordings: OTHER when the request names someone other than the caller
# ("for Kevin Rolfs"), SELF when the caller is booking for themselves.
OFFER_QUESTION_OTHER = (
    "If they've been to the clinic before I can find their previous appointment so you "
    "can easily book another. Would that be helpful?"
)
OFFER_QUESTION_SELF = (
    "If you've been to the clinic before I can find your previous appointment so you "
    "can easily book another. Would that be helpful?"
)


def generate_tests() -> List[Dict]:
    p = f"[{CLINIC}]"
    greeting = "You've reached Physio Cure AI receptionist! How can I help you?"

    tests = []

    # REGRESSION CASE — the exact live-call failure reported 2026-09-17.
    tests.append({
        "name": f"{p} REG1 — exact live transcript: 'book next appointment for Kevin Rolfs' fires the offer, not Signal 1",
        "chat_history": [
            _m("agent", greeting, 0),
            _m("user", "Hi, can I please book next appointment for Kevin Rolfs?", 2),
        ],
        "success_condition": (
            f'Agent speaks exactly the RETURNING PATIENT LOOKUP OFFER question: "{OFFER_QUESTION_OTHER}" '
            f'with zero tool calls this turn. FAIL if the agent instead speaks a Signal 1 ack '
            f'(e.g. "Lovely! Let me get that sorted for you.") and calls universal_router '
            f'intent="book_intent" — that is the exact live failure mode being tested here.'
        ),
        "success_examples": [_ok(OFFER_QUESTION_OTHER)],
        "failure_examples": [
            _fail("Lovely! Let me get that sorted for you."),
            _fail("[calls universal_router intent=book_intent]"),
        ],
    })

    # Buried trigger variant.
    tests.append({
        "name": f"{p} REG2 — buried trigger: 'book an appointment -- my next one' fires the offer",
        "chat_history": [
            _m("agent", greeting, 0),
            _m("user", "Hi, can I book an appointment -- my next one, actually, for Kevin Rolfs?", 2),
        ],
        "success_condition": (
            f'Agent speaks exactly: "{OFFER_QUESTION_OTHER}" with zero tool calls this turn. FAIL if the '
            f'agent instead acks and calls universal_router intent="book_intent" immediately -- the '
            f'leading "book an appointment" phrasing must not cause Signal 1 to fire before the '
            f'trailing "my next one" repeat-visit language is scanned.'
        ),
        "success_examples": [_ok(OFFER_QUESTION_OTHER)],
        "failure_examples": [
            _fail("Lovely!"),
            _fail("[calls universal_router intent=book_intent]"),
        ],
    })

    # Regression check — plain booking with no repeat-visit language must NOT trigger the offer.
    tests.append({
        "name": f"{p} REG3 — plain booking, no repeat-visit language, Signal 1 fires immediately (regression)",
        "chat_history": [
            _m("agent", greeting, 0),
            _m("user", "Hi, I'd like to book an appointment please.", 2),
        ],
        "success_condition": (
            'Agent acks (e.g. "Lovely!" / "Of course!") and calls universal_router intent="book_intent" '
            'immediately, in the same turn. FAIL if the RETURNING PATIENT LOOKUP OFFER question is '
            'asked -- "book an appointment" alone, with no "next"/"another"/"follow-up"/"usual"/"again" '
            'language, must not trigger it.'
        ),
        "success_examples": [_ok("Lovely! [calls universal_router intent=book_intent]")],
        "failure_examples": [_fail(OFFER_QUESTION_SELF), _fail(OFFER_QUESTION_OTHER)],
    })

    # Regression check — first-time exclusion still works.
    tests.append({
        "name": f"{p} REG4 — caller states first-time status in same message, offer does not fire (exclusion)",
        "chat_history": [
            _m("agent", greeting, 0),
            _m("user", "Hi, this would be my first time, can I book an appointment please?", 2),
        ],
        "success_condition": (
            'Agent proceeds directly to Signal 1 (ack + book_intent, patient_status="new" in payload), '
            'with no RETURNING PATIENT LOOKUP OFFER question asked. FAIL if the offer question is '
            'spoken despite the caller explicitly stating this is their first time.'
        ),
        "success_examples": [_ok("Of course! [calls universal_router intent=book_intent patient_status=new]")],
        "failure_examples": [_fail(OFFER_QUESTION_SELF), _fail(OFFER_QUESTION_OTHER)],
    })

    # Continuation — caller agrees to the offer.
    tests.append({
        "name": f"{p} REG5 — caller agrees to the offer, fires details_past with return_node=1",
        "chat_history": [
            _m("agent", greeting, 0),
            _m("user", "Hi, can I please book my next appointment for Kevin Rolfs?", 2),
            _m("agent", OFFER_QUESTION_OTHER, 5),
            _m("user", "Yes please", 8),
        ],
        "success_condition": (
            'Agent speaks "Just a sec." AND in the same response calls '
            'universal_router with intent="details_past", called_number, caller_id, and payload '
            'containing return_node="1", booking_for="other" and family_member_name="Kevin Rolfs" '
            '(the request named Kevin). FAIL if patient_name is included in the payload, if '
            'return_node is omitted, or if the tool call and spoken phrase are not both present.'
        ),
        "success_examples": [
            _ok('Just a sec. [calls universal_router intent=details_past return_node=1 booking_for=other family_member_name=Kevin Rolfs]')
        ],
        "failure_examples": [
            _fail("[no tool call]"),
            _fail("[calls universal_router intent=book_intent]"),
        ],
    })

    # Self caller — the offer is worded "you/your", not the third-party "they/their".
    tests.append({
        "name": f"{p} REG6 — self repeat-visit request gets the self-worded offer ('you/your')",
        "chat_history": [
            _m("agent", greeting, 0),
            _m("user", "Hi, can I please book my next appointment?", 2),
        ],
        "success_condition": (
            f'Agent speaks exactly: "{OFFER_QUESTION_SELF}" with zero tool calls this turn. FAIL if '
            f'the agent says "they"/"their" about the caller (the third-party wording), or if it '
            f'instead acks and calls universal_router intent="book_intent" immediately.'
        ),
        "success_examples": [_ok(OFFER_QUESTION_SELF)],
        "failure_examples": [
            _fail(OFFER_QUESTION_OTHER),
            _fail("Lovely! [calls universal_router intent=book_intent]"),
        ],
    })

    # Named family member — keeps the third-party wording.
    tests.append({
        "name": f"{p} REG7 — named daughter request keeps the third-party offer ('they/their')",
        "chat_history": [
            _m("agent", greeting, 0),
            _m("user", "Hi, I'd like to book a follow-up appointment for my daughter Sarah.", 2),
        ],
        "success_condition": (
            f'Agent speaks exactly: "{OFFER_QUESTION_OTHER}" with zero tool calls this turn. FAIL if '
            f'the agent says "you"/"your" (the request names someone other than the caller), or if '
            f'it instead acks and calls universal_router intent="book_intent" immediately.'
        ),
        "success_examples": [_ok(OFFER_QUESTION_OTHER)],
        "failure_examples": [
            _fail(OFFER_QUESTION_SELF),
            _fail("Lovely! [calls universal_router intent=book_intent]"),
        ],
    })

    # Self caller agrees to the self-worded offer — STEP 2 accepts either STEP 1 wording.
    tests.append({
        "name": f"{p} REG8 — caller agrees to the self-worded offer, details_past with return_node only",
        "chat_history": [
            _m("agent", greeting, 0),
            _m("user", "Hi, can I please book my next appointment?", 2),
            _m("agent", OFFER_QUESTION_SELF, 5),
            _m("user", "Yes please", 8),
        ],
        "success_condition": (
            'Agent speaks "Just a sec." AND in the same response calls universal_router with '
            'intent="details_past", called_number, caller_id, and payload containing '
            'return_node="1" and nothing about a third party. FAIL if the payload includes '
            'booking_for or family_member_name (the caller is booking for themselves), or if the '
            'tool call and spoken phrase are not both present.'
        ),
        "success_examples": [
            _ok('Just a sec. [calls universal_router intent=details_past return_node=1]')
        ],
        "failure_examples": [
            _fail("[no tool call]"),
            _fail("[calls universal_router intent=details_past return_node=1 booking_for=other]"),
            _fail("[calls universal_router intent=book_intent]"),
        ],
    })

    return tests


_DYNAMIC_VAR_PLACEHOLDERS = {
    "called_number": "+61000000000",
    "caller_id": "+61111111111",
    "caller_phone": "+61111111111",
    "system__called_number": "+61000000000",
    "system__conversation_id": "conv_test000000000000000",
    "caller_first_name": "",
    "caller_last_name": "",
    "caller_email": "",
    "patient_status": "",
    "appointment_type_id": "",
    "appointment_type": "",
    "appointment_date": "",
    "appointment_time": "",
    "booking_for": "",
    "family_member_name": "",
    "uni_router_intent": "",
    "reschedule_mode": "",
    "info_answered": "none",
    "implied_service": "",
    "timeframe_raw": "",
    "practitioner_preference": "",
    "practitioner_id": "",
    "preferred_gender": "",
    "wrap_routing_flag": "",
    "return_node": "",
    "location": "",
    "location_addresses": "",
    "practitioner_genders": "none",
    "service_ids": "",
    "business_id": "",
    "business_name": "",
    "group_or_private": "",
    "caller_complaint": "",
    "price": "",
    "recent_booking_id": "",
    "recent_booking_phone": "",
    "resolved_patient_id": "",
    "patient_name_raw": "",
    "cancellation_completed": "",
    "reschedule_offer_pending": "",
    "appointment_lookup_failed": "",
    "appointment_lookup_intent": "",
    "patient_lookup_done": "",
    "details_delivered": "",
    "waitlist_enabled": "false",
}


def _el_hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def create_scaffold_agent(node1_prompt: str) -> Optional[str]:
    payload = {
        "name": f"[Node1 Test] {CLINIC}",
        "conversation_config": {
            "agent": {
                "first_message": "You've reached Physio Cure AI receptionist! How can I help you?",
                "prompt": {
                    "prompt": node1_prompt,
                    "llm": SCAFFOLD_LLM,
                    "tool_ids": [UNIVERSAL_ROUTER_TOOL_ID],
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
        print(f"OK Scaffold agent created: {agent_id}")
        return agent_id
    print(f"X Failed to create agent: {resp.status_code} - {resp.text[:300]}")
    return None


def delete_scaffold_agent(agent_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    if resp.status_code in (200, 204):
        print(f"OK Agent {agent_id} deleted.")
    else:
        print(f"X Failed to delete agent {agent_id}: {resp.status_code}")


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


def verify_agent_alive(agent_id: str) -> bool:
    resp = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    return resp.status_code == 200


def patch_scaffold_agent_prompt(agent_id: str, node1_prompt: str) -> bool:
    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {"prompt": node1_prompt},
                "dynamic_variables": {
                    "dynamic_variable_placeholders": _DYNAMIC_VAR_PLACEHOLDERS
                },
            }
        }
    }
    resp = requests.patch(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs(), json=payload)
    if resp.status_code == 200:
        print(f"OK Prompt patched on session agent {agent_id}")
        return True
    print(f"X Failed to patch agent prompt: {resp.status_code} - {resp.text[:200]}")
    return False


def push_test(t: Dict) -> Optional[str]:
    payload = {
        "name": t["name"],
        "chat_history": t["chat_history"],
        "success_condition": t["success_condition"],
        "success_examples": t["success_examples"],
        "failure_examples": t["failure_examples"],
    }
    resp = requests.post(f"{BASE_URL}/agent-testing/create", headers=_el_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        return data.get("test_id") or data.get("id")
    print(f"  X Failed to create '{t['name']}': {resp.status_code} - {resp.text[:200]}")
    return None


def dispatch_tests(agent_id: str, test_ids: List[str]) -> Optional[str]:
    payload = {"tests": [{"test_id": tid} for tid in test_ids]}
    resp = requests.post(f"{BASE_URL}/agents/{agent_id}/run-tests", headers=_el_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        inv_id = data.get("invocation_id") or data.get("id")
        print(f"OK Tests dispatched - invocation: {inv_id}")
        return inv_id
    print(f"X Failed to dispatch tests: {resp.status_code} - {resp.text[:300]}")
    return None


def poll_invocation(invocation_id: str) -> Optional[Dict]:
    deadline = time.time() + POLL_TIMEOUT_SECS
    while time.time() < deadline:
        resp = requests.get(f"{BASE_URL}/test-invocations/{invocation_id}", headers=_el_hdrs())
        if resp.status_code == 200:
            data = resp.json()
            runs = data.get("test_runs", [])
            pending = sum(1 for r in runs if r.get("status") not in ("passed", "failed"))
            if runs and pending == 0:
                return data
            print(f"  ... {len(runs) - pending}/{len(runs)} done, waiting {POLL_INTERVAL_SECS}s")
        time.sleep(POLL_INTERVAL_SECS)
    print("X Timed out waiting for results.")
    return None


def print_results(result: Dict, name_map: Dict[str, str]) -> bool:
    runs = result.get("test_runs", [])
    passed_runs = [r for r in runs if r.get("status") == "passed"]
    failed_runs = [r for r in runs if r.get("status") != "passed"]

    print(f"\n-- Results ({len(passed_runs)}/{len(runs)} passed) --")
    for r in runs:
        tid = r.get("test_id") or r.get("id")
        name = name_map.get(tid, tid)
        status = r.get("status")
        marker = "PASS" if status == "passed" else "FAIL"
        print(f"\n[{marker}] {name}")
        summary = r.get("summary") or r.get("result_summary") or ""
        if summary:
            print(f"  summary: {summary}")
        transcript = r.get("agent_responses") or r.get("transcript") or r.get("conversation") or None
        if transcript:
            print(f"  transcript: {json.dumps(transcript, indent=2)[:1500]}")
        if status != "passed":
            print(f"  RAW: {json.dumps(r, indent=2)[:2000]}")

    return len(failed_runs) == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--agent-id", default=None)
    parser.add_argument("--keep-agent", action="store_true")
    args = parser.parse_args()

    if not ELEVENLABS_API_KEY:
        print("X ELEVENLABS_API_KEY not set")
        sys.exit(1)

    if args.cleanup:
        agent_id = args.agent_id or load_session_agent()
        if agent_id:
            delete_scaffold_agent(agent_id)
            clear_session_agent()
        else:
            print("No session agent to clean up.")
        return

    node1_prompt = load_node1()
    if node1_prompt is None:
        sys.exit(1)

    if args.reset:
        existing = load_session_agent()
        if existing:
            delete_scaffold_agent(existing)
        clear_session_agent()

    agent_id = args.agent_id or load_session_agent()
    if agent_id and not verify_agent_alive(agent_id):
        print(f"! Session agent {agent_id} no longer exists — creating a new one.")
        agent_id = None

    if agent_id:
        if not patch_scaffold_agent_prompt(agent_id, node1_prompt):
            sys.exit(1)
    else:
        agent_id = create_scaffold_agent(node1_prompt)
        if not agent_id:
            sys.exit(1)
        save_session_agent(agent_id)

    if not args.run:
        print("Agent ready. Pass --run to execute tests.")
        return

    tests = generate_tests()
    print(f"\nPushing {len(tests)} test(s)...")
    test_ids = []
    name_map = {}
    for t in tests:
        tid = push_test(t)
        if tid:
            test_ids.append(tid)
            name_map[tid] = t["name"]

    if not test_ids:
        print("X No tests pushed successfully.")
        sys.exit(1)

    inv_id = dispatch_tests(agent_id, test_ids)
    if not inv_id:
        sys.exit(1)

    result = poll_invocation(inv_id)
    if result is None:
        sys.exit(1)

    all_passed = print_results(result, name_map)

    # Clean up test cases from the agent-testing UI regardless of outcome.
    for tid in test_ids:
        requests.delete(f"{BASE_URL}/agent-testing/{tid}", headers=_el_hdrs())

    if all_passed and not args.keep_agent:
        delete_scaffold_agent(agent_id)
        clear_session_agent()
        print("\nAll tests passed. Scaffold agent deleted.")
    elif not all_passed:
        print(f"\nSome tests FAILED. Scaffold agent {agent_id} retained for inspection.")
        print(f"Use --agent-id {agent_id} to reuse it, or --cleanup to delete it.")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
