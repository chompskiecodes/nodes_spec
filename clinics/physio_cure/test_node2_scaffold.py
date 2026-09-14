#!/usr/bin/env python3
"""
test_node2_scaffold.py  (Physio Cure)

Standalone scaffold to test Node 2 (Service Resolution) for Physio Cure — specifically
the PHYSIO_FUNDING_GATE fix (bare "physio" mention must ask the funding-bucket question,
not jump straight to PRIVATE's own gate question).

This runs the REAL prompt (shared system_prompt.txt + this node's Additional Prompt)
against the REAL ElevenLabs agent-testing API (real claude-haiku-4-5 invocation, real
tool schema) — not a local simulation. This is the thing to trust when a meta-simulated
Haiku self-audit passes but a live call still fails: the self-audit reasons about what it
*would* do; this actually invokes the runtime.

Usage:
    py -X utf8 nodes/clinics/physio_cure/test_node2_scaffold.py --run
    py -X utf8 nodes/clinics/physio_cure/test_node2_scaffold.py --run --reset
    py -X utf8 nodes/clinics/physio_cure/test_node2_scaffold.py --cleanup
    py -X utf8 nodes/clinics/physio_cure/test_node2_scaffold.py --agent-id <id> --run
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
# (agent_5201m29b60hjfhwbdb3bwg7fcvrr) — checked via GET /v1/convai/agents/{id} 2026-09-13.
UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"

SCAFFOLD_LLM = "claude-haiku-4-5"
POLL_INTERVAL_SECS = 10
POLL_TIMEOUT_SECS = 240

_SESSION_FILE = CLINIC_DIR / "node2_scaffold_agent.json"


# ── Node 2 prompt loading ────────────────────────────────────────────────────

def strip_node_header(content: str) -> str:
    lines = content.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == "Additional Prompt:":
            start = i + 1
            break
    return "\n".join(lines[start:]).strip()


def load_node2() -> Optional[str]:
    """Node 2 is Override: Disabled — in production it ALWAYS runs combined with
    nodes/shared/system_prompt.txt. Sending the Additional Prompt alone would be an
    unrepresentative, off-script scaffold."""
    path = CLINIC_DIR / "node_2_service_resolution.txt"
    if not path.exists():
        print(f"X Node 2 file not found: {path}")
        return None
    content = path.read_text(encoding="utf-8")
    additional_prompt = strip_node_header(content)

    sys_path = NODES_DIR.parent / "shared" / "system_prompt.txt"
    if not sys_path.exists():
        print(f"X Shared system prompt not found: {sys_path}")
        return None
    system_prompt = sys_path.read_text(encoding="utf-8").strip()

    prompt = system_prompt + "\n\n" + additional_prompt
    print(f"OK Loaded Node 2 for '{CLINIC}' — system_prompt ({len(system_prompt):,} chars) "
          f"+ additional_prompt ({len(additional_prompt):,} chars) = {len(prompt):,} chars total")
    return prompt


# ── Test helpers ─────────────────────────────────────────────────────────────

def _m(role: str, text: str, t: int = 0) -> Dict:
    return {"role": role, "message": text, "time_in_call_secs": t}


def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}


def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}


def generate_tests() -> List[Dict]:
    p = f"[{CLINIC}]"
    menu_list = ("We offer Physiotherapy, Remedial Massage, Group Exercise classes, "
                 "Workplace Assessments, and Telehealth appointments -- which of those were you after?")
    funding_q = ("How will this be funded -- paying privately, through a Medicare care plan, "
                 "health insurance, NDIS or DVA, or is this a work injury claim?")
    private_gate_q = "Have you had a physiotherapy consultation with us before?"

    tests = []

    # REGRESSION CASE — the exact live-call failure reported 2026-09-13.
    tests.append({
        "name": f"{p} REG1 — bare 'physio' reply to MENU_LIST asks funding question, not PRIVATE gate",
        "chat_history": [
            _m("agent", menu_list, 2),
            _m("user", "physio", 5),
        ],
        "success_condition": (
            f'Agent does NOT ask "{private_gate_q}" (PRIVATE branch gate question) or any other '
            f'PRIVATE-branch question. A bare single-word reply "physio" with no funder or payment '
            f'method named matches PHYSIO_FUNDING_GATE, not PRIVATE. Agent asks the funding bucket '
            f'question: "{funding_q}" (or a close paraphrase covering the same options). '
            f'Zero tool calls this turn. FAIL if the agent asks the PRIVATE gate question instead.'
        ),
        "success_examples": [_ok(funding_q)],
        "failure_examples": [
            _fail(private_gate_q),
            _fail("[calls universal_router]"),
        ],
    })

    # Continuation — funding answered "privately" -> correct next question.
    tests.append({
        "name": f"{p} REG2 — 'privately' after funding question asks PRIVATE gate question",
        "chat_history": [
            _m("agent", menu_list, 2),
            _m("user", "physio", 5),
            _m("agent", funding_q, 8),
            _m("user", "Privately.", 11),
        ],
        "success_condition": (
            f'Funding resolved as private. Agent does NOT call universal_router yet and does NOT '
            f'ask about duration. Agent asks the PRIVATE branch\'s own mandatory first question: '
            f'"{private_gate_q}" (or close paraphrase). Zero tool calls this turn.'
        ),
        "success_examples": [_ok(private_gate_q)],
        "failure_examples": [
            _fail("[calls universal_router]"),
            _fail("Would you like a short 20 minute"),
        ],
    })

    # Full flow — new patient, private, physio -> correct confirm_service call.
    tests.append({
        "name": f"{p} REG3 — full flow new patient private physio resolves to correct appointment type",
        "chat_history": [
            _m("agent", menu_list, 2),
            _m("user", "physio", 5),
            _m("agent", funding_q, 8),
            _m("user", "Privately.", 11),
            _m("agent", private_gate_q, 14),
            _m("user", "No, first time.", 17),
        ],
        "success_condition": (
            'New patient, private funding, physio service -- fully resolved. Agent speaks exactly '
            'one short filler phrase (e.g. "One moment.") and calls universal_router with '
            'intent="confirm_service", payload containing appointment_type_id="1167091570785125832", '
            'patient_status="new", variant_type="initial". Agent does NOT ask a duration question '
            '(only the returning-patient path asks that) and does NOT ask anything else. '
            'FAIL if the wrong appointment_type_id is used, if a duration question is asked, or if '
            'no tool call is made.'
        ),
        "success_examples": [
            _ok("One moment. [calls universal_router confirm_service appointment_type_id=1167091570785125832]")
        ],
        "failure_examples": [
            _fail("Would you like a short 20 minute"),
            _fail("[no tool call]"),
            _fail("appointment_type_id=1167095830251832780"),
        ],
    })

    return tests


_DYNAMIC_VAR_PLACEHOLDERS = {
    "called_number": "+61000000000",
    "caller_id": "+61111111111",
    "system__called_number": "+61000000000",
    "system__caller_id": "+61111111111",
    "patient_status": "",
    "appointment_type_id": "none",
    "appointment_type": "",
    "booking_for": "self",
    "uni_router_intent": "",
    "reschedule_mode": "",
    "info_answered": "",
    "implied_service": "",
    "timeframe_raw": "",
    "practitioner_preference": "",
    "preferred_gender": "",
    "wrap_routing_flag": "",
    "return_node": "",
}


def _el_hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def create_scaffold_agent(node2_prompt: str) -> Optional[str]:
    payload = {
        "name": f"[Node2 Test] {CLINIC}",
        "conversation_config": {
            "agent": {
                "first_message": "Thanks for calling Physio Cure, how can I help you today?",
                "prompt": {
                    "prompt": node2_prompt,
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


def patch_scaffold_agent_prompt(agent_id: str, node2_prompt: str) -> bool:
    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {"prompt": node2_prompt},
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

    node2_prompt = load_node2()
    if node2_prompt is None:
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
        if not patch_scaffold_agent_prompt(agent_id, node2_prompt):
            sys.exit(1)
    else:
        agent_id = create_scaffold_agent(node2_prompt)
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
