#!/usr/bin/env python3
"""
test_node3_entry_sequence_scaffold.py  (Physio Cure)

SINGLE-SCENARIO repro scaffold for the 2026-09-13/14 live-call regression:
Node 3's first turn asked "When would you like to come in?" immediately on
entry, skipping PRACTITIONER PREFERENCE and LOCATION entirely — even after
the ENTRY SEQUENCE GATE fix (nodes submodule commit 194428d) was patched
live via fast_patch.py. This does NOT test the full Node 3 battery — it
targets exactly one scenario, using the exact chat history from the live
transcript, so this can be iterated quickly against Haiku.

Usage:
    python nodes/clinics/physio_cure/test_node3_entry_sequence_scaffold.py --run
    python nodes/clinics/physio_cure/test_node3_entry_sequence_scaffold.py --agent-id <id> --run
    python nodes/clinics/physio_cure/test_node3_entry_sequence_scaffold.py --cleanup
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
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = "https://api.elevenlabs.io/v1/convai"

CLINIC_DIR = Path(__file__).parent
CLINIC = "physio_cure"

# Shared tool IDs (same across the fleet — confirmed via other clinics' scaffold scripts)
SMART_ROUTER_TOOL_ID     = "tool_4501k96qzckzemabz9rwppjms6zj"   # smart_voice_agent / smart_router
UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"   # universal_router

SCAFFOLD_LLM       = "claude-haiku-4-5"  # matches production Node 3 LLM for physio_cure
POLL_INTERVAL_SECS = 10
POLL_TIMEOUT_SECS  = 300

_SESSION_FILE = CLINIC_DIR / "node3_entry_sequence_scaffold_agent.json"

# Real DB-confirmed values (2026-09-14) — see conversation notes.
APPOINTMENT_TYPE_ID = "1720874020271818742"   # "2. Private Short Subsequent", 20 min
APPOINTMENT_TYPE    = "2. Private Short Subsequent"
PRIMARY_BUSINESS_ID   = "11821"
PRIMARY_BUSINESS_NAME = "Physio Cure (Elwood)"
PRACTITIONERS_COMMA = "Dr Harry Bebawy, Margareth Carvalheiro, Pawankumar Jeevnani, Livia Yip"
PRACTITIONER_SERVICES = (
    "Dr Harry Bebawy=Private Physiotherapy Session;2. Private Short Subsequent|"
    "Margareth Carvalheiro=Private Physiotherapy Session;2. Private Short Subsequent|"
    "Pawankumar Jeevnani=Private Physiotherapy Session;2. Private Short Subsequent|"
    "Livia Yip=Private Physiotherapy Session;2. Private Short Subsequent"
)
PRACTITIONERS_WITH_IDS = (
    "Dr Harry Bebawy:145192, Margareth Carvalheiro:1122155417963595002, "
    "Pawankumar Jeevnani:1998279099461666084, Livia Yip:2026581376815334702"
)


def strip_node_header(content: str) -> str:
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "Additional Prompt:":
            start = i + 1
            while start < len(lines) and not lines[start].strip():
                start += 1
            return "\n".join(lines[start:]).strip()
    return content.strip()


def load_node3() -> Optional[str]:
    """Node 3 is Override: Disabled — always runs combined with the shared system prompt."""
    path = CLINIC_DIR / "node_3_availability_handler.txt"
    if not path.exists():
        print(f"X Node 3 file not found: {path}")
        return None
    content = path.read_text(encoding="utf-8")
    additional_prompt = strip_node_header(content)

    sys_path = CLINIC_DIR.parent.parent / "shared" / "system_prompt.txt"
    if not sys_path.exists():
        print(f"X Shared system prompt not found: {sys_path}")
        return None
    system_prompt = sys_path.read_text(encoding="utf-8").strip()

    prompt = system_prompt + "\n\n" + additional_prompt
    print(f"OK Loaded Node 3 for '{CLINIC}' — system_prompt ({len(system_prompt):,} chars) "
          f"+ additional_prompt ({len(additional_prompt):,} chars) = {len(prompt):,} chars total")
    return prompt


def _m(role: str, text: str, t: int = 0) -> Dict:
    return {"role": role, "message": text, "time_in_call_secs": t}


def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}


def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}


def _confirm_service_turn(t: int, routing_reminder: Optional[str] = None) -> Dict:
    """
    Node 2's real handoff turn — "Just a sec." + universal_router intent="confirm_service"
    — omitted from the original scaffold (which jumped straight from the caller's "20" to
    Node 3 generating, with only DVs carrying the resolved state). Modeling this turn for
    real puts the tool result at actual maximum recency, directly before Node 3 speaks —
    exactly where a routing hint would need to sit to compete with the duration Q&A's own
    recency advantage (see docs/in-progress/node3_entry_sequence_gate_haiku_ceiling_2026_09_14.md,
    "lever 2"). `routing_reminder`, when given, is injected into the tool result content
    as a real backend fix would produce it — this tests the lever itself, not a wording
    change to the node prompt.
    """
    result: Dict = {
        "service_resolved": True,
        "appointment_type_id": APPOINTMENT_TYPE_ID,
        "appointment_type": APPOINTMENT_TYPE,
        "practitioner_preference": "",
        "location_preference": "",
    }
    if routing_reminder:
        result["routing_reminder"] = routing_reminder
    return {
        "role": "agent",
        "message": "Just a sec.",
        "time_in_call_secs": t,
        "tool_calls": [{
            "request_id": "req_confirm_service_1",
            "tool_name": "universal_router",
            "params_as_json": json.dumps({
                "intent": "confirm_service",
                "appointment_type_id": APPOINTMENT_TYPE_ID,
                "appointment_type": APPOINTMENT_TYPE,
            }),
            "tool_has_been_called": True,
            "type": "webhook",
        }],
        "tool_results": [{
            "request_id": "req_confirm_service_1",
            "tool_name": "universal_router",
            "result_value": json.dumps(result),
            "is_error": False,
            "tool_has_been_called": True,
            "type": "webhook",
        }],
    }


def build_test(routing_reminder: Optional[str] = None, model_confirm_service_turn: bool = False) -> Dict:
    """
    Exact chat history from the 2026-09-14 live-call transcript that exposed the
    regression: caller opens with "book private funded physio", confirms returning
    patient, picks the 20-minute variant. Node 2 hands off to Node 3 with
    {{appointment_type_id}} resolved, {{timeframe_raw}} empty, no practitioner or
    location ever stated. This is Node 3's very first turn.

    `model_confirm_service_turn=True` inserts Node 2's real "Just a sec." + tool-call turn
    (see `_confirm_service_turn`) instead of jumping straight from "20" to Node 3's turn.
    `routing_reminder`, when given, is passed through into that turn's tool result — this
    is lever 2 from the ceiling tracker doc: inject the hint at max recency via the tool
    result instead of the node prompt.
    """
    history = [
        _m("agent", "Have you had a physiotherapy consultation with us before?", 2),
        _m("user",  "yes", 5),
        _m("agent", "Would you like a short 20 minute, standard 30 minute, long 40 minute, or extended 60 minute session?", 8),
        _m("user",  "20", 11),
    ]
    if model_confirm_service_turn:
        history.append(_confirm_service_turn(14, routing_reminder))
    name_suffix = ""
    if model_confirm_service_turn:
        name_suffix = " + reminder" if routing_reminder else " + real handoff turn"
    return {
        "name": f"[{CLINIC}] ENTRY-SEQ — fresh Node 3 entry must not ask timeframe first{name_suffix}",
        "chat_history": history,
        "success_condition": (
            "This is Node 3's very first turn for this call. {{appointment_type_id}} is resolved "
            "(1720874020271818742, '2. Private Short Subsequent'). {{timeframe_raw}} is empty. "
            "Neither a practitioner nor a location has been stated anywhere in this history. "
            "{{business_id}}/{{business_name}} are pre-populated with the clinic's primary location "
            "(11821 / 'Physio Cure (Elwood)') but the caller never confirmed this — per the node's own "
            "LOC-GATE rule this population does NOT count as the location question being answered. "
            "Per ENTRY SEQUENCE GATE, the agent must evaluate PRACTITIONER PREFERENCE first (with 4 "
            "practitioners matching this service, it should ask 'Did you want to book with Dr Harry "
            "Bebawy, Margareth Carvalheiro, Pawankumar Jeevnani, or Livia Yip, or is anyone fine?' as a "
            "spoken-only turn), and ONLY once that is resolved may LOCATION or the TIMEFRAME QUESTION "
            "ever be reached. "
            "PASS if the agent's turn is the PRACTITIONER PREFERENCE question (naming the four "
            "practitioners) OR, if a scoring quirk causes practitioner resolution to be silently skipped, "
            "the LOCATION question ('Which location works for you — Physio Cure (Elwood), Physio First "
            "(Beaumaris), or is any location fine?'). "
            "FAIL if the agent's turn is 'When would you like to come in?' (or any equivalent timeframe "
            "question) with no practitioner or location question asked first, or if the agent calls "
            "smart_voice_agent this turn."
        ),
        "success_examples": [
            _ok("Did you want to book with Dr Harry Bebawy, Margareth Carvalheiro, Pawankumar Jeevnani, "
                "or Livia Yip, or is anyone fine?"),
            _ok("Which location works for you — Physio Cure (Elwood), Physio First (Beaumaris), or is "
                "any location fine?"),
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("[calls smart_voice_agent]"),
        ],
    }


def _el_hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def create_scaffold_agent(node3_prompt: str) -> Optional[str]:
    payload = {
        "name": f"[Node3 EntrySeq Test] {CLINIC}",
        "conversation_config": {
            "agent": {
                "first_message": "Thanks for calling Physio Cure, how can I help you today?",
                "prompt": {
                    "prompt": node3_prompt,
                    "llm": SCAFFOLD_LLM,
                    "tool_ids": [SMART_ROUTER_TOOL_ID, UNIVERSAL_ROUTER_TOOL_ID],
                    "temperature": 0.0,
                    "max_tokens": 1024,
                },
                "dynamic_variables": {
                    "dynamic_variable_placeholders": {
                        "called_number":         "+61000000000",
                        "caller_id":              "+61111111111",
                        "caller_phone":           "+61111111111",
                        "system__called_number":  "+61000000000",
                        "system__caller_id":      "+61111111111",
                        "system__time":           "2026-09-14T09:00:00+10:00",
                        "appointment_type_id":    APPOINTMENT_TYPE_ID,
                        "appointment_type":       APPOINTMENT_TYPE,
                        "booking_for":            "",
                        "patient_status":         "existing",
                        "uni_router_intent":      "",
                        "timeframe_raw":          "",
                        "practitioner_preference": "",
                        "practitioner_services":  PRACTITIONER_SERVICES,
                        "practitioners_with_ids": PRACTITIONERS_WITH_IDS,
                        "practitioners_comma":    PRACTITIONERS_COMMA,
                        "new_patient_allocation_enabled": "true",
                        "info_answered":          "",
                        "cancellation_completed": "",
                        "reschedule_mode":        "",
                        "return_node":            "",
                        "waitlist_enabled":       "true",
                        # Pre-populated from the clinic's primary business, per twilio_init_webhook —
                        # NOT a confirmed caller answer. This is the LOC-GATE trap condition.
                        "business_id":            PRIMARY_BUSINESS_ID,
                        "business_name":          PRIMARY_BUSINESS_NAME,
                    }
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
    print(f"X Failed to create agent: {resp.status_code} — {resp.text[:300]}")
    return None


def patch_scaffold_agent_prompt(agent_id: str, node3_prompt: str) -> bool:
    payload = {"conversation_config": {"agent": {"prompt": {"prompt": node3_prompt}}}}
    resp = requests.patch(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs(), json=payload)
    if resp.status_code == 200:
        print(f"OK Prompt patched on session agent {agent_id}")
        return True
    print(f"X Failed to patch agent prompt: {resp.status_code} — {resp.text[:200]}")
    return False


def verify_agent_alive(agent_id: str) -> bool:
    resp = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    return resp.status_code == 200


def delete_scaffold_agent(agent_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    if resp.status_code in (200, 204):
        print(f"OK Agent {agent_id} deleted.")
    else:
        print(f"X Failed to delete agent {agent_id}: {resp.status_code}")


def push_test(t: Dict) -> Optional[str]:
    payload = {
        "name":              t["name"],
        "chat_history":      t["chat_history"],
        "success_condition": t["success_condition"],
        "success_examples":  t["success_examples"],
        "failure_examples":  t["failure_examples"],
    }
    resp = requests.post(f"{BASE_URL}/agent-testing/create", headers=_el_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        return data.get("test_id") or data.get("id")
    print(f"X Failed to create test: {resp.status_code} — {resp.text[:300]}")
    return None


def delete_test(test_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agent-testing/{test_id}", headers=_el_hdrs())
    if resp.status_code not in (200, 204):
        print(f"  X Failed to delete test {test_id}: {resp.status_code}")


def dispatch_tests(agent_id: str, test_ids: List[str]) -> Optional[str]:
    payload = {"tests": [{"test_id": tid} for tid in test_ids]}
    resp = requests.post(f"{BASE_URL}/agents/{agent_id}/run-tests", headers=_el_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        inv_id = data.get("invocation_id") or data.get("id")
        print(f"OK Tests dispatched — invocation: {inv_id}")
        return inv_id
    print(f"X Failed to dispatch tests: {resp.status_code} — {resp.text[:300]}")
    return None


def poll_invocation(invocation_id: str, expected_runs: int = 1) -> Optional[Dict]:
    deadline = time.time() + POLL_TIMEOUT_SECS
    while time.time() < deadline:
        resp = requests.get(f"{BASE_URL}/test-invocations/{invocation_id}", headers=_el_hdrs())
        if resp.status_code == 200:
            data = resp.json()
            runs = data.get("test_runs", [])
            pending = sum(1 for r in runs if r.get("status") not in ("passed", "failed"))
            if runs and pending == 0 and len(runs) >= expected_runs:
                return data
            print(f"  ... waiting {POLL_INTERVAL_SECS}s ({len(runs) - pending}/{max(len(runs),1)} done)")
        time.sleep(POLL_INTERVAL_SECS)
    print("X Timed out waiting for results.")
    return None


def print_result(result: Dict, label: str = "", test_id: Optional[str] = None) -> bool:
    runs = result.get("test_runs", [])
    if test_id:
        runs = [r for r in runs if r.get("test_id") == test_id] or runs
    if not runs:
        print("X No test runs returned.")
        return False
    r = runs[0]
    status = r.get("status")
    header = f"── {label} — Result: {status.upper()} " if label else f"\n── Result: {status.upper()} "
    print(f"\n{header}{'─' * max(1, 50 - len(header))}")
    agent_responses = r.get("agent_responses") or []
    agent_msg = next(
        (str(x.get("message") or "") for x in agent_responses if x.get("role") == "agent"),
        "[no spoken output]"
    )
    all_tool_calls = []
    for resp in agent_responses:
        if resp.get("role") == "agent":
            all_tool_calls.extend(resp.get("tool_calls") or [])
    tool_names = [tc.get("tool_name", "") for tc in all_tool_calls]
    tool_args  = [tc.get("parameters") or tc.get("tool_input") or tc.get("arguments") or {}
                  for tc in all_tool_calls]
    print(f"  Agent said: \"{agent_msg}\"")
    if tool_names:
        print(f"  Tools called: {tool_names}")
        for tn, ta in zip(tool_names, tool_args):
            if ta:
                print(f"    -> {tn}: {json.dumps(ta)[:300]}")
    ev = r.get("evaluation") or {}
    rationale = ev.get("rationale") or ""
    if rationale:
        print(f"  Evaluator rationale: {rationale}")
    print()
    return status == "passed"


ROUTING_REMINDER_TEXT = (
    "practitioner_preference and location are NOT resolved for this booking. Before asking "
    "about timeframe, ask which practitioner the caller prefers (or if anyone is fine), then "
    "which location works for them (or if any location is fine)."
)

# Stronger-worded variant of the same lever (still injected via tool result, not the node
# prompt) — MANDATORY framing, explicit negative example, explicit next-action instruction.
ROUTING_REMINDER_TEXT_STRONG = (
    "MANDATORY ROUTING NOTE (read before generating your next response): practitioner and "
    "location are NOT yet resolved for this booking. Your NEXT response MUST ask about "
    "practitioner preference (naming the practitioners) — do NOT ask about timeframe in this "
    "response. Do NOT say \"When would you like to come in?\" or any equivalent. The correct "
    "next response is a practitioner-preference question, nothing else."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Node 3 ENTRY SEQUENCE single-scenario scaffold — physio_cure")
    parser.add_argument("--agent-id", help="Pin to a specific agent ID (bypasses session management)")
    parser.add_argument("--run", action="store_true", help="Run the test after creating/patching the agent")
    parser.add_argument("--cleanup", action="store_true", help="Delete the session agent and exit")
    parser.add_argument(
        "--variants", default="baseline",
        help="Comma-separated: baseline (original, no handoff turn modeled), "
             "handoff (real Node2 tool-call turn, no reminder), "
             "reminder (real handoff turn + routing_reminder in tool result). "
             "e.g. --variants baseline,handoff,reminder",
    )
    args = parser.parse_args()

    if not ELEVENLABS_API_KEY:
        print("X ELEVENLABS_API_KEY not set in .env"); sys.exit(1)

    if args.cleanup:
        if _SESSION_FILE.exists():
            data = json.loads(_SESSION_FILE.read_text(encoding="utf-8"))
            aid = data.get("agent_id")
            if aid:
                delete_scaffold_agent(aid)
            _SESSION_FILE.unlink()
        else:
            print("No session agent found — nothing to clean up.")
        return

    node3_prompt = load_node3()
    if not node3_prompt:
        sys.exit(1)

    variant_names = [v.strip() for v in args.variants.split(",") if v.strip()]
    variant_builders = {
        "baseline": lambda: build_test(),
        "handoff":  lambda: build_test(model_confirm_service_turn=True),
        "reminder": lambda: build_test(model_confirm_service_turn=True, routing_reminder=ROUTING_REMINDER_TEXT),
        "reminder_strong": lambda: build_test(model_confirm_service_turn=True, routing_reminder=ROUTING_REMINDER_TEXT_STRONG),
    }
    tests = []
    for name in variant_names:
        if name not in variant_builders:
            print(f"X Unknown variant '{name}' — choices: {list(variant_builders)}"); sys.exit(1)
        tests.append((name, variant_builders[name]()))

    agent_id = args.agent_id
    if agent_id:
        print(f"Patching prompt on pinned agent {agent_id}...")
        patch_scaffold_agent_prompt(agent_id, node3_prompt)
    else:
        existing = None
        if _SESSION_FILE.exists():
            existing = json.loads(_SESSION_FILE.read_text(encoding="utf-8")).get("agent_id")
        if existing and verify_agent_alive(existing):
            print(f"OK Session agent found: {existing}")
            if patch_scaffold_agent_prompt(existing, node3_prompt):
                agent_id = existing
        if not agent_id:
            agent_id = create_scaffold_agent(node3_prompt)
            if not agent_id:
                sys.exit(1)
            _SESSION_FILE.write_text(json.dumps({"agent_id": agent_id}), encoding="utf-8")

    pushed = []
    for name, t in tests:
        test_id = push_test(t)
        if not test_id:
            sys.exit(1)
        print(f"OK Test pushed [{name}]: {test_id}")
        pushed.append((name, test_id))

    if args.run:
        inv_id = dispatch_tests(agent_id, [tid for _, tid in pushed])
        all_passed = True
        if inv_id:
            result = poll_invocation(inv_id, expected_runs=len(pushed))
            if result:
                runs = result.get("test_runs", [])
                for name, test_id in pushed:
                    matching = {"test_runs": [r for r in runs if r.get("test_id") == test_id]}
                    if not matching["test_runs"]:
                        # fall back to positional match if API doesn't echo test_id
                        idx = [tid for _, tid in pushed].index(test_id)
                        matching = {"test_runs": [runs[idx]]} if idx < len(runs) else {"test_runs": []}
                    passed = print_result(matching, label=name)
                    all_passed = all_passed and passed
            else:
                all_passed = False
        else:
            all_passed = False
        for _, test_id in pushed:
            delete_test(test_id)
        print("\nALL PASSED" if all_passed else "\nSOME FAILED")
        sys.exit(0 if all_passed else 1)
    else:
        for _, test_id in pushed:
            delete_test(test_id)
        print("Test(s) validated (not run). Re-run with --run.")


if __name__ == "__main__":
    main()
