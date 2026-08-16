#!/usr/bin/env python3
"""
test_node3_practitioner_pref_repro.py  (Angus Osteopathic & Sport Injuries Clinics)

NARROW repro scaffold — NOT a full Node 3 test battery (see northern_physio's
test_node3_scaffold.py for that pattern). This exists to answer one question:

  Does the live Node 3 prompt, on claude-haiku-4-5 (production LLM/temp), reliably
  ask the PRACTITIONER PREFERENCE question when {{appointment_type}} matches 2+
  practitioners in {{practitioner_services}} — or does it intermittently skip
  straight to the TIMEFRAME QUESTION, as observed on two live calls
  (conv_2301kzzpcnjcf04s1rfhhch3r5zf and a second live call reported by the user)?

Method: push the SAME test scenario N times as separate ElevenLabs agent-testing
cases (each becomes an independent test_id), dispatch all N in one invocation, and
report the empirical pass rate. This directly measures non-determinism instead of
inferring it from a single run — a single clean scenario-probe pass (already done
manually, see chat history) proved the model CAN do it correctly; this measures how
RELIABLY it does it under the platform's actual sampling.

Includes one CONTROL scenario (single-match service — should NOT ask) run the same
number of times, to confirm the harness itself is discriminating pass/fail correctly
and isn't just rubber-stamping every response as a pass.

Uses the exact live DVs from conv_2301kzzpcnjcf04s1rfhhch3r5zf:
  appointment_type="Follow up appointment", booking_for="self", patient_status="existing",
  practitioner_services = 3 practitioners, all offering the same 3 services (Barry Watkins,
  Moraglouise Smith, Richard Fulton).

Usage:
    python nodes/clinics/angus_osteopathic_sport_injuries_clinics/test_node3_practitioner_pref_repro.py --run
    python nodes/clinics/angus_osteopathic_sport_injuries_clinics/test_node3_practitioner_pref_repro.py --run --n 20
    python nodes/clinics/angus_osteopathic_sport_injuries_clinics/test_node3_practitioner_pref_repro.py --cleanup
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
CLINIC = "angus_osteopathic_sport_injuries_clinics"

SMART_ROUTER_TOOL_ID     = "tool_4501k96qzckzemabz9rwppjms6zj"   # smart_voice_agent
UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"   # universal_router

SCAFFOLD_LLM        = "claude-haiku-4-5"   # matches live Node 3 LLM exactly
POLL_INTERVAL_SECS  = 12
POLL_TIMEOUT_SECS   = 480

_SESSION_FILE = CLINIC_DIR / "node3_repro_scaffold_agent.json"

# Real DVs from conv_2301kzzpcnjcf04s1rfhhch3r5zf, confirmed via the ElevenLabs API
# (conversation_initiation_client_data.dynamic_variables) — not synthetic.
PRACTITIONER_SERVICES = (
    "Barry Watkins=Initial Consultation;Follow up appointment;Initial Consultation & 2 follow up appointments"
    "|Moraglouise Smith=Initial Consultation;Follow up appointment;Initial Consultation & 2 follow up appointments"
    "|Richard Fulton=Initial Consultation;Follow up appointment;Initial Consultation & 2 follow up appointments"
)
PRACTITIONERS_WITH_IDS = (
    "Barry Watkins:1897254931560138527, Moraglouise Smith:1898015627570841416, Richard Fulton:92973"
)
PRACTITIONERS_COMMA = "Barry Watkins, Moraglouise Smith, Richard Fulton"

# Control fixture: only ONE practitioner offers "Follow up appointment" (0-1 match) —
# PRACTITIONER PREFERENCE must stay SILENT and skip straight to the TIMEFRAME QUESTION.
# Proves the harness can correctly fail a response that wrongly asks for a preference
# when the rule says it shouldn't (not just rubber-stamping every response as a pass).
PRACTITIONER_SERVICES_CONTROL = (
    "Barry Watkins=Deep Tissue Massage"
    "|Moraglouise Smith=Follow up appointment"
    "|Richard Fulton=Sports Massage"
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
    """
    Node 3 is `Override: Disabled` — in production it ALWAYS runs combined with
    nodes/shared/system_prompt.txt (the agent-level prompt), never on its own.
    An earlier version of this scaffold sent only the stripped Additional Prompt
    and got a completely off-script response ("Let me pull up your details
    first" + immediate smart_voice_agent call, matching NO branch in Node 3's
    own text) on both the repro and control scenarios — that was this harness
    being unrepresentative of production, not a finding about the live node.
    """
    path = CLINIC_DIR / "node_3_availability_handler.txt"
    if not path.exists():
        print(f"✗ Node 3 file not found: {path}")
        return None
    content = path.read_text(encoding="utf-8")
    additional_prompt = strip_node_header(content)

    sys_path = CLINIC_DIR.parent.parent / "shared" / "system_prompt.txt"
    if not sys_path.exists():
        print(f"✗ Shared system prompt not found: {sys_path}")
        return None
    system_prompt = sys_path.read_text(encoding="utf-8").strip()

    combined = system_prompt + "\n\n" + additional_prompt
    print(f"✓ Loaded live Node 3 for '{CLINIC}' — system_prompt ({len(system_prompt):,} chars) "
          f"+ additional_prompt ({len(additional_prompt):,} chars) = {len(combined):,} chars total")
    return combined


def _m(role: str, text: str, t: int = 0) -> Dict:
    return {"role": role, "message": text, "time_in_call_secs": t}


def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}


def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}


# Replicates the ACTUAL turn-by-turn shape of the real call (conv_2301kzzpcnjcf04s1rfhhch3r5zf)
# up through the exact moment Node 3 activates for the first time — not a single synthetic
# opening line. The transition from Node 2 to Node 3 happens purely via a silent
# confirm_service tool call/result with NO new user utterance in between, so this history
# correctly ends on an AGENT turn (mirroring northern_physio's _entry_history() pattern,
# which also ends chat_history on an agent turn before a tool-result injection).
# A first synthetic single-line version of this history (just the caller's opening
# sentence, no prior turns) produced a totally different, unrelated failure mode
# ("Just a sec." + immediate smart_voice_agent call, matching no branch in Node 3's own
# text) on both repro AND control — that was this harness lacking the context Node 3
# actually receives mid-call, not a finding about the live node's real behaviour.
REPRO_HISTORY = [
    _m("user", "book", 1),
    _m("agent", "Lovely!", 2),
    _m("agent", "Have you been to Angus Osteopathic & Sport Injuries Clinics before?", 3),
    _m("user", "yes", 4),
    _m("agent", "Just a sec.", 5),
    _m("agent",
       "[universal_router confirm_service result received: status=success, "
       "intent=confirm_service, uni_router_intent=service_resolved, "
       "appointment_type_id=553304, appointment_type=\"Follow up appointment\", "
       "patient_status=existing, variant_type=followup — routed successfully. "
       "You have just transitioned into this node (3. Availability Handler) for the "
       "first time this call. No tool call has been made in this node yet. "
       "{{timeframe_raw}} is empty.]",
       6),
]

# Control: identical turn structure; only the DV override (practitioner_services) differs
# (see build_control_test / PRACTITIONER_SERVICES_CONTROL).
CONTROL_HISTORY = list(REPRO_HISTORY)


def build_repro_test(index: int) -> Dict:
    return {
        "name": f"[angus] PPref-repro #{index}",
        "chat_history": REPRO_HISTORY,
        "success_condition": (
            "This is the agent's first turn in the node. {{appointment_type}}='Follow up appointment' "
            "matches all three practitioners in {{practitioner_services}} (Barry Watkins, Moraglouise "
            "Smith, Richard Fulton all offer 'Follow up appointment') — 3 matches, well past the '2+' "
            "threshold in the PRACTITIONER PREFERENCE rule. Per BOOKING FLOW step 1 "
            "({{booking_for}}='self' or empty), the agent MUST resolve PRACTITIONER PREFERENCE BEFORE "
            "asking the TIMEFRAME QUESTION. PASS requires the agent's spoken turn to ask a "
            "practitioner-preference question naming some/all of Barry Watkins, Moraglouise Smith, "
            "Richard Fulton (e.g. 'Did you want to book with Barry Watkins, Moraglouise Smith, or "
            "Richard Fulton, or is anyone fine?') — a close wording variant is fine, but it MUST name "
            "at least two of the three practitioners or clearly offer a choice among them. "
            "FAIL if the agent instead asks 'When would you like to come in?' (or any timeframe "
            "question) without first asking about practitioner preference, or calls any tool this turn."
        ),
        "success_examples": [
            _ok("Did you want to book with Barry Watkins, Moraglouise Smith, or Richard Fulton, "
                "or is anyone fine?"),
            _ok("Do you have a preference — Barry, Moraglouise, or Richard — or is anyone okay?"),
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("[calls smart_voice_agent]"),
            _fail("[calls universal_router]"),
        ],
    }


def build_control_test(index: int) -> Dict:
    return {
        "name": f"[angus] PPref-CONTROL #{index}",
        "chat_history": CONTROL_HISTORY,
        "success_condition": (
            "CONTROL scenario — {{practitioner_services}} for this test is overridden so that ONLY "
            "Moraglouise Smith offers 'Follow up appointment' (Barry Watkins offers Deep Tissue "
            "Massage, Richard Fulton offers Sports Massage — neither matches {{appointment_type}}). "
            "This is a 0-1 match case, so per the PRACTITIONER PREFERENCE rule the agent must skip "
            "the practitioner question SILENTLY and go straight to the TIMEFRAME QUESTION. "
            "PASS: agent's first turn asks 'When would you like to come in?' (or a close variant) "
            "with NO mention of practitioner names or preference, and no tool call. "
            "FAIL: agent asks about practitioner preference/choice, names any practitioner, or "
            "calls any tool this turn."
        ),
        "success_examples": [
            _ok("When would you like to come in?"),
        ],
        "failure_examples": [
            _fail("Did you want to book with Moraglouise Smith, or is anyone fine?"),
            _fail("[calls smart_voice_agent]"),
            _fail("[calls universal_router]"),
        ],
    }


def _el_hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def create_scaffold_agent(node3_prompt: str, practitioner_services: str,
                           practitioners_with_ids: str, label: str) -> Optional[str]:
    payload = {
        "name": f"[Node3 PPref Repro] {CLINIC} ({label})",
        "conversation_config": {
            "agent": {
                "first_message": "Thanks for calling Angus Osteopathic & Sport Injuries Clinics, how can I help?",
                "prompt": {
                    "prompt": node3_prompt,
                    "llm": SCAFFOLD_LLM,
                    "tool_ids": [SMART_ROUTER_TOOL_ID, UNIVERSAL_ROUTER_TOOL_ID],
                    "temperature": 0.0,
                    "max_tokens": 1024,
                },
                "dynamic_variables": {
                    "dynamic_variable_placeholders": {
                        "called_number":            "+447457402591",
                        "caller_id":                "+447457400000",
                        "system__called_number":    "+447457402591",
                        "system__caller_id":        "+447457400000",
                        "system__time":             "2026-08-14T09:00:00+01:00",
                        "appointment_type_id":      "553304",
                        "appointment_type":         "Follow up appointment",
                        "booking_for":              "self",
                        "patient_status":           "existing",
                        "variant_type":             "followup",
                        "cancellation_completed":   "none",
                        "uni_router_intent":        "service_resolved",
                        "timeframe_raw":            "",
                        "practitioner_preference":  "",
                        "patient_name_raw":         "",
                        "caller_first_name":        "",
                        "practitioners_comma":      PRACTITIONERS_COMMA,
                        "practitioner_services":    practitioner_services,
                        "practitioners_with_ids":   practitioners_with_ids,
                        "info_answered":            "",
                        "reschedule_mode":          "",
                        "return_node":              "",
                        "constraint_changed":       "",
                    }
                },
            },
            "conversation": {"text_only": True},
        },
    }
    resp = requests.post(f"{BASE_URL}/agents/create", headers=_el_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        agent_id = resp.json().get("agent_id")
        print(f"✓ Scaffold agent created ({label}): {agent_id}")
        return agent_id
    print(f"✗ Failed to create agent ({label}): {resp.status_code} — {resp.text[:300]}")
    return None


def delete_scaffold_agent(agent_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    print(f"{'✓' if resp.status_code in (200, 204) else '✗'} delete {agent_id}: {resp.status_code}")


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
    print(f"  ✗ Failed to create '{t['name']}': {resp.status_code} — {resp.text[:200]}")
    return None


def delete_test(test_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agent-testing/{test_id}", headers=_el_hdrs())
    if resp.status_code not in (200, 204):
        print(f"  ✗ Failed to delete test {test_id}: {resp.status_code}")


def dispatch_tests(agent_id: str, test_ids: List[str]) -> Optional[str]:
    payload = {"tests": [{"test_id": tid} for tid in test_ids]}
    resp = requests.post(f"{BASE_URL}/agents/{agent_id}/run-tests", headers=_el_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        inv_id = data.get("invocation_id") or data.get("id")
        print(f"✓ Dispatched {len(test_ids)} runs — invocation: {inv_id}")
        return inv_id
    print(f"✗ Failed to dispatch tests: {resp.status_code} — {resp.text[:300]}")
    return None


def poll_invocation(invocation_id: str) -> Optional[Dict]:
    deadline = time.time() + POLL_TIMEOUT_SECS
    start = time.time()
    while time.time() < deadline:
        resp = requests.get(f"{BASE_URL}/test-invocations/{invocation_id}", headers=_el_hdrs())
        if resp.status_code == 200:
            data = resp.json()
            runs = data.get("test_runs", [])
            pending = sum(1 for r in runs if r.get("status") not in ("passed", "failed"))
            if runs and pending == 0:
                return data
            elapsed = int(time.time() - start)
            print(f"  … [{elapsed}s] {len(runs) - pending}/{len(runs)} done, waiting {POLL_INTERVAL_SECS}s")
        time.sleep(POLL_INTERVAL_SECS)
    print("✗ Timed out waiting for results.")
    return None


def report(label: str, result: Dict) -> None:
    runs = result.get("test_runs", [])
    passed = [r for r in runs if r.get("status") == "passed"]
    failed = [r for r in runs if r.get("status") != "passed"]
    n = len(runs)
    print(f"\n── {label}: {len(passed)}/{n} passed ({100*len(passed)/n:.0f}%) ─────")
    if failed:
        print(f"  FAILED runs ({len(failed)}):")
        for r in failed:
            agent_responses = r.get("agent_responses") or []
            agent_msg = next(
                (str(x.get("message") or "") for x in agent_responses if x.get("role") == "agent"),
                "[no spoken output]"
            )
            tool_calls = []
            for resp in agent_responses:
                if resp.get("role") == "agent":
                    tool_calls.extend(resp.get("tool_calls") or [])
            tool_names = [tc.get("tool_name", "") for tc in tool_calls]
            ev = r.get("evaluation") or {}
            print(f"    ✗ agent said: \"{agent_msg[:100]}\"  tools={tool_names}")
            if ev.get("rationale"):
                print(f"      reason: {ev['rationale'][:150]}")


def load_session() -> Dict:
    if _SESSION_FILE.exists():
        try:
            return json.loads(_SESSION_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"main": None, "control": None}


def save_session(main_id, control_id) -> None:
    _SESSION_FILE.write_text(json.dumps({"main": main_id, "control": control_id}, indent=2), encoding="utf-8")


def clear_session() -> None:
    if _SESSION_FILE.exists():
        _SESSION_FILE.unlink()


def verify_agent_alive(agent_id: str) -> bool:
    resp = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    return resp.status_code == 200


def main() -> None:
    parser = argparse.ArgumentParser(description="Node 3 PRACTITIONER PREFERENCE repro scaffold — Angus")
    parser.add_argument("--run", action="store_true", help="Run the repro N times and report the pass rate")
    parser.add_argument("--n", type=int, default=15, help="Number of independent runs per scenario (default 15)")
    parser.add_argument("--cleanup", action="store_true", help="Delete session scaffold agents and exit")
    parser.add_argument("--skip-control", action="store_true", help="Skip the control scenario")
    args = parser.parse_args()

    if not ELEVENLABS_API_KEY:
        print("✗ ELEVENLABS_API_KEY not set in .env"); sys.exit(1)

    session = load_session()

    if args.cleanup:
        for key, cid in session.items():
            if cid:
                delete_scaffold_agent(cid)
        clear_session()
        return

    node3_prompt = load_node3()
    if not node3_prompt:
        sys.exit(1)

    # Main (repro) agent
    main_id = session.get("main")
    if main_id and verify_agent_alive(main_id):
        print(f"✓ Reusing session repro agent: {main_id}")
    else:
        main_id = create_scaffold_agent(node3_prompt, PRACTITIONER_SERVICES, PRACTITIONERS_WITH_IDS, "repro")
        if not main_id:
            sys.exit(1)
        session["main"] = main_id

    control_id = None
    if not args.skip_control:
        control_id = session.get("control")
        if control_id and verify_agent_alive(control_id):
            print(f"✓ Reusing session control agent: {control_id}")
        else:
            control_id = create_scaffold_agent(node3_prompt, PRACTITIONER_SERVICES_CONTROL,
                                                PRACTITIONERS_WITH_IDS, "control")
            if control_id:
                session["control"] = control_id

    save_session(session.get("main"), session.get("control"))

    if not args.run:
        print("Agents created/verified. Re-run with --run to execute the repro.")
        return

    # Push N repro tests
    print(f"\nPushing {args.n} independent repro test runs...")
    repro_tests = [build_repro_test(i) for i in range(1, args.n + 1)]
    repro_ids = [tid for t in repro_tests if (tid := push_test(t))]
    print(f"✓ {len(repro_ids)}/{args.n} repro tests created")

    control_ids = []
    if control_id:
        print(f"\nPushing {args.n} independent control test runs...")
        control_tests = [build_control_test(i) for i in range(1, args.n + 1)]
        control_ids = [tid for t in control_tests if (tid := push_test(t))]
        print(f"✓ {len(control_ids)}/{args.n} control tests created")

    # Dispatch and poll
    if repro_ids:
        inv_id = dispatch_tests(main_id, repro_ids)
        if inv_id:
            result = poll_invocation(inv_id)
            if result:
                report("PRACTITIONER PREFERENCE repro (real live-call DVs)", result)

    if control_ids:
        inv_id = dispatch_tests(control_id, control_ids)
        if inv_id:
            result = poll_invocation(inv_id)
            if result:
                report("Control (2-match, different DV set — sanity check on harness)", result)

    # Clean up test cases (not the agents — keep for re-runs)
    all_test_ids = repro_ids + control_ids
    for tid in all_test_ids:
        delete_test(tid)
    print(f"\n✓ {len(all_test_ids)} test case(s) cleaned from agent-testing UI.")
    print(f"Scaffold agents retained for re-runs: main={main_id} control={control_id}")
    print(f"Use --cleanup to delete them when done.")


if __name__ == "__main__":
    main()
