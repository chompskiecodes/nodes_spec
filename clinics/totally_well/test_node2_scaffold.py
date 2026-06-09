#!/usr/bin/env python
"""
Totally Well — Node 2 Service Resolution scaffold test.

Focus: massage category routing — does the agent present a massage-focused
menu (not the full service menu) and route correctly for specific types
and "any/soonest" preference?

Usage:
  py -X utf8 nodes/clinics/totally_well/test_node2_scaffold.py --run
  py -X utf8 nodes/clinics/totally_well/test_node2_scaffold.py --spec-only
  py -X utf8 nodes/clinics/totally_well/test_node2_scaffold.py --cleanup
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import os as _os
import sys as _sys

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent)
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

try:
    import config as _cfg
    ELEVENLABS_API_KEY = _cfg.Settings().elevenlabs_api_key
except Exception:
    ELEVENLABS_API_KEY = _os.getenv("ELEVENLABS_API_KEY", "")

BASE_URL   = "https://api.elevenlabs.io/v1/convai"
CLINIC     = "Totally Well"
CLINIC_DIR = Path(__file__).parent

UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"

SCAFFOLD_LLM       = "claude-haiku-4-5"
POLL_INTERVAL_SECS = 12
POLL_TIMEOUT_SECS  = 360

_SESSION_FILE = CLINIC_DIR / "node2_scaffold_agent.json"

# ---------------------------------------------------------------------------
# Dynamic variable placeholders
# ---------------------------------------------------------------------------
_DYNAMIC_VAR_PLACEHOLDERS = {
    "called_number":           "+61756365028",
    "caller_id":               "0402841577",
    "system__called_number":   "+61756365028",
    "system__caller_id":       "0402841577",
    "system__conversation_id": "conv_test_scaffold",
    "patient_name_raw":        "",
    "patient_status":          "",
    "appointment_type_id":     "none",
    "appointment_type":        "",
    "booking_for":             "self",
    "uni_router_intent":       "",
    "info_answered":           "",
    "implied_service":         "",
    "timeframe_raw":           "",
    "practitioner_preference": "",
    "preferred_gender":        "",
    "reschedule_mode":         "",
    "location":                "",
    "wrap_routing_flag":       "",
    "practitioner_genders":    "",
    "practitioners_comma": (
        "Bartosz Kulikowski, Renee Fujimoto, Rosario Fernandez, "
        "Ruby De Paulo, Tanya Ly"
    ),
    "service_categories": (
        "Remedial Massage, Relaxation Massage, Clinical Lymphatic Drainage, "
        "Advanced Lymphatic Therapies, Lymphoedema & Lipoedema Management, "
        "Post Surgical Care, Naturopathy, Pregnancy, "
        "Fascia & Cellulite Treatments, Craniosacral Therapy, "
        "Sports & Deep Tissue Rehab"
    ),
}

P = f"[{CLINIC}]"


# ---------------------------------------------------------------------------
# Chat helpers
# ---------------------------------------------------------------------------
def _m(role: str, text: str, t: int = 0) -> Dict:
    el_role = "agent" if role == "assistant" else role
    return {"role": el_role, "message": text, "time_in_call_secs": t}

def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}

def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def generate_tests() -> List[Dict]:
    tests = []

    # -----------------------------------------------------------------------
    # Group M — Massage category routing (primary focus)
    # -----------------------------------------------------------------------

    # M1 — caller says "I'd like a massage" (no specific type)
    tests.append({
        "name": f"{P} M1. Generic massage request — no specific type named",
        "chat_history": [
            _m("user", "Hi, I'd like to book a massage please.", 3),
        ],
        "success_condition": (
            "Agent presents a FOCUSED massage options menu — names specific massage "
            "therapy types such as Remedial Massage, Relaxation Massage, Deep Tissue, "
            "and/or Craniosacral. "
            "Agent does NOT immediately present unrelated services like Naturopathy, "
            "Post Surgical Care, or Lymphoedema Management as primary options. "
            "Agent ends with a question asking which type the caller prefers."
        ),
        "success_examples": [
            _ok("We offer Remedial Massage, Relaxation Massage, Deep Tissue Sports Massage, "
                "Craniosacral Therapy, and Lymphatic Drainage — which type were you after?"),
            _ok("We have a few massage options — Remedial, Relaxation, Deep Tissue, "
                "and Craniosacral. Which were you thinking?"),
        ],
        "failure_examples": [
            _fail("We offer Remedial Massage, Relaxation Massage, Lymphatic Drainage "
                  "therapies, Post Surgical Care, Naturopathy, Pregnancy treatments, "
                  "and other specialised therapies. Which were you after?"),
            _fail("I can help with that — have you been here before?"),
        ],
    })

    # M2 — caller says "remedial massage", agent asks variant, caller confirms new
    tests.append({
        "name": f"{P} M2. Remedial massage — new patient confirmed via variant answer",
        "chat_history": [
            _m("user", "I'd like to book a remedial massage.", 3),
            _m("agent", "Have you had Remedial Massage with us before?", 5),
            _m("user", "No, never been before.", 8),
        ],
        "success_condition": (
            "Agent calls universal_router intent='confirm_service' with "
            "appointment_type_id='1706185375103329858' (Remedial Massage - First Visit) "
            "and patient_status='new' inside the payload. "
            "Tool call only — zero spoken output."
        ),
        "success_examples": [
            _ok("[silent — calls confirm_service with appointment_type_id='1706185375103329858' "
                "patient_status='new']"),
        ],
        "failure_examples": [
            _fail("[calls confirm_service with wrong appointment_type_id]"),
            _fail("[calls confirm_service without patient_status]"),
            _fail("Were you after 45, 60, or 90 minutes?"),
        ],
    })

    # M3 — returning patient picks 60 min remedial
    tests.append({
        "name": f"{P} M3. Remedial massage — returning patient, 60 min",
        "chat_history": [
            _m("user",
               "Remedial massage please, I've been before.",
               3),
            _m("agent",
               "Were you after 45, 60, or 90 minutes?",
               5),
            _m("user", "60 minutes please.", 9),
        ],
        "success_condition": (
            "Agent calls universal_router intent='confirm_service' with "
            "appointment_type_id='1881819781372323677' (Remedial Massage - Standard Appointment) "
            "and patient_status='existing' inside the payload. Tool call only."
        ),
        "success_examples": [
            _ok("[silent — calls confirm_service with appointment_type_id='1881819781372323677' "
                "patient_status='existing']"),
        ],
        "failure_examples": [
            _fail("[calls confirm_service with First Visit ID instead of Standard]"),
            _fail("[calls confirm_service without patient_status]"),
            _fail("Great — let me book that for you."),
        ],
    })

    # M4 — after massage menu, caller says "any / soonest"
    tests.append({
        "name": f"{P} M4. Any massage — soonest available after menu",
        "chat_history": [
            _m("agent",
               "We offer Remedial Massage, Relaxation Massage, Deep Tissue Sports Massage, "
               "Craniosacral Therapy, and Lymphatic Drainage — which type were you after?",
               2),
            _m("user",
               "I don't really mind — just whatever is available soonest.",
               7),
        ],
        "success_condition": (
            "Agent either (a) routes via universal_router intent='confirm_service' for any "
            "specific massage type (Remedial, Relaxation, Deep Tissue, or similar), "
            "or (b) asks a clarifying question to narrow down the caller's preference "
            "(e.g. 'Are you after a muscle-focused massage or a gentle relaxation?'). "
            "Agent does NOT repeat the full service menu unchanged. "
            "Agent does NOT say 'I can't help with that' or route to wrap_up."
        ),
        "success_examples": [
            _ok("[routes via confirm_service for any massage type]"),
            _ok("Are you after a muscle-focused treatment like Remedial or Deep Tissue, "
                "or more of a relaxation massage?"),
        ],
        "failure_examples": [
            _fail("We offer Remedial Massage, Relaxation Massage, Lymphatic Drainage "
                  "therapies, Post Surgical Care, Naturopathy, Pregnancy treatments..."),
            _fail("I'm not able to check availability from here."),
            _fail("[routes to wrap_up]"),
        ],
    })

    # M5 — craniosacral therapy (direct route, Tanya only)
    tests.append({
        "name": f"{P} M5. Craniosacral therapy — direct route",
        "chat_history": [
            _m("user", "I'd like to book a craniosacral therapy session please.", 3),
        ],
        "success_condition": (
            "Agent calls universal_router intent='confirm_service' with "
            "appointment_type_id='1633276199335634254' (Osteopathic Craniosacral Therapy) "
            "and practitioner_preference='Tanya Ly' inside the payload. Tool call only."
        ),
        "success_examples": [
            _ok("[silent — calls confirm_service with appointment_type_id='1633276199335634254' "
                "practitioner_preference='Tanya Ly']"),
        ],
        "failure_examples": [
            _fail("[calls confirm_service with wrong appointment_type_id]"),
            _fail("[calls confirm_service without practitioner_preference='Tanya Ly']"),
            _fail("Have you had Craniosacral Therapy with us before?"),
        ],
    })

    # M6 — deep tissue massage alone → REMEDIAL_MASSAGE, new patient (2-turn flow)
    # The mandatory variant question must fire first; confirm_service on the second turn.
    tests.append({
        "name": f"{P} M6. Deep tissue massage alone — variant asked, new patient",
        "chat_history": [
            _m("user", "I'd like a deep tissue massage.", 3),
            _m("agent",
               "Have you had Remedial Massage with us before?",
               5),
            _m("user", "No I haven't, never been.", 8),
        ],
        "success_condition": (
            "Agent calls universal_router intent='confirm_service' with "
            "appointment_type_id='1706185375103329858' (Remedial Massage - First Visit) "
            "and patient_status='new' inside the payload. "
            "Deep tissue alone (without 'sports' or 'rehab') maps to the Remedial branch. "
            "Tool call only — zero spoken output."
        ),
        "success_examples": [
            _ok("[silent — calls confirm_service with appointment_type_id='1706185375103329858' "
                "patient_status='new']"),
        ],
        "failure_examples": [
            _fail("[calls confirm_service with Sports Rehab ID '1938451578646176789']"),
            _fail("[calls confirm_service with Short appointment ID '1705809119534917124']"),
            _fail("Were you after 45, 60, or 90 minutes?"),
        ],
    })

    # -----------------------------------------------------------------------
    # Group S — Blocking signals (baseline)
    # -----------------------------------------------------------------------

    # S1 — pricing question → info pivot
    tests.append({
        "name": f"{P} S1. Pricing question — info pivot",
        "chat_history": [
            _m("user", "How much does a remedial massage cost?", 3),
        ],
        "success_condition": (
            "Agent calls universal_router intent='info_pivot'. "
            "Pricing questions must never be answered inline in Node 2. "
            "The critical requirement is that the agent routes to info_pivot "
            "and does NOT state a price or fee amount. "
            "Brief spoken output before the tool call is acceptable as long as the price is not named."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router intent='info_pivot']"),
            _ok("[calls universal_router intent='info_pivot']"),
        ],
        "failure_examples": [
            _fail("A Remedial Massage - First Visit is $130."),
            _fail("I don't have pricing details — please ask the practitioner."),
            _fail("Pricing varies — it starts around $100 per session."),
        ],
    })

    # S2 — cancel escape
    tests.append({
        "name": f"{P} S2. Cancel existing appointment",
        "chat_history": [
            _m("user", "Actually I need to cancel my appointment.", 3),
        ],
        "success_condition": (
            "Agent calls universal_router intent='cancel_intent'. "
            "Tool call only — zero spoken output."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router intent='cancel_intent']"),
        ],
        "failure_examples": [
            _fail("[calls universal_router intent='info_pivot']"),
            _fail("I can help with that — what day is your appointment?"),
        ],
    })

    # S3 — wrap-up on goodbye
    tests.append({
        "name": f"{P} S3. Wrap-up on goodbye",
        "chat_history": [
            _m("agent",
               "We offer Remedial Massage, Relaxation Massage, and other services. "
               "Which were you after?",
               2),
            _m("user", "Never mind, goodbye!", 6),
        ],
        "success_condition": (
            "Agent calls universal_router intent='wrap_up'. Tool call only."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router intent='wrap_up']"),
        ],
        "failure_examples": [
            _fail("[calls universal_router intent='info_pivot']"),
            _fail("Goodbye! Take care."),
        ],
    })

    return tests


# ---------------------------------------------------------------------------
# ElevenLabs API helpers  (identical pattern to Node 8 scaffold)
# ---------------------------------------------------------------------------
import requests  # noqa: E402


def _hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def _load_prompt() -> str:
    """Return system_prompt + Additional Prompt (Override: Disabled)."""
    sys_file = CLINIC_DIR.parent.parent / "shared" / "system_prompt.txt"
    node_file = CLINIC_DIR / "node_2_service_resolution.txt"

    sys_prompt = sys_file.read_text(encoding="utf-8-sig").strip() if sys_file.exists() else ""

    raw = node_file.read_text(encoding="utf-8-sig")
    marker = "Additional Prompt:"
    idx = raw.find(marker)
    if idx >= 0:
        node_part = raw[idx + len(marker):].strip()
    else:
        # Fall back: take from first ## heading
        for i, line in enumerate(raw.splitlines()):
            if line.startswith("##") or line.startswith("#"):
                node_part = "\n".join(raw.splitlines()[i:]).strip()
                break
        else:
            node_part = raw.strip()

    if sys_prompt:
        return f"{sys_prompt}\n\n{node_part}"
    return node_part


def create_scaffold_agent(prompt: str) -> Optional[str]:
    payload = {
        "name": f"[Node2 Test] {CLINIC}",
        "conversation_config": {
            "agent": {
                "first_message": "Thanks for calling Totally Well — how can I help you today?",
                "prompt": {
                    "prompt": prompt,
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
    resp = requests.post(f"{BASE_URL}/agents/create", headers=_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        aid = resp.json().get("agent_id")
        print(f"✓ Scaffold agent created: {aid}")
        return aid
    print(f"✗ Create failed: {resp.status_code} — {resp.text[:300]}")
    return None


def patch_scaffold_agent(agent_id: str, prompt: str) -> bool:
    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {"prompt": prompt},
                "dynamic_variables": {
                    "dynamic_variable_placeholders": _DYNAMIC_VAR_PLACEHOLDERS
                },
            }
        }
    }
    resp = requests.patch(f"{BASE_URL}/agents/{agent_id}", headers=_hdrs(), json=payload)
    if resp.status_code == 200:
        print(f"✓ Prompt patched on {agent_id}")
        return True
    print(f"✗ Patch failed: {resp.status_code} — {resp.text[:200]}")
    return False


def delete_scaffold_agent(agent_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agents/{agent_id}", headers=_hdrs())
    if resp.status_code in (200, 204):
        print(f"✓ Deleted scaffold agent {agent_id}")
    else:
        print(f"✗ Delete failed: {resp.status_code}")


def push_tests(agent_id: str, tests: List[Dict]) -> Dict[str, str]:
    id_to_name: Dict[str, str] = {}
    for t in tests:
        payload = {
            "agent_id":          agent_id,
            "name":              t["name"],
            "type":              "llm",
            "success_condition": t["success_condition"],
            "success_examples":  t.get("success_examples", []),
            "failure_examples":  t.get("failure_examples", []),
            "chat_history":      t["chat_history"],
        }
        resp = requests.post(
            f"{BASE_URL}/agent-testing/create", headers=_hdrs(), json=payload
        )
        if resp.status_code in (200, 201):
            tid = resp.json().get("id") or resp.json().get("test_id")
            id_to_name[tid] = t["name"]
            print(f"  ✓ {t['name']}")
        else:
            print(f"  ✗ {t['name']}: {resp.status_code} — {resp.text[:200]}")
    return id_to_name


def run_and_poll(agent_id: str, id_to_name: Dict[str, str]) -> List[Dict]:
    test_ids = list(id_to_name.keys())
    run_resp = requests.post(
        f"{BASE_URL}/agents/{agent_id}/run-tests",
        headers=_hdrs(),
        json={"tests": [{"test_id": tid} for tid in test_ids]},
    )
    if run_resp.status_code not in (200, 202):
        print(f"✗ Run failed: {run_resp.status_code} — {run_resp.text[:200]}")
        return []

    suite_id = run_resp.json().get("id")
    print(f"  Suite: {suite_id} — polling every {POLL_INTERVAL_SECS}s …")

    deadline = time.time() + POLL_TIMEOUT_SECS
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_SECS)
        r = requests.get(f"{BASE_URL}/test-invocations/{suite_id}", headers=_hdrs())
        if r.status_code != 200:
            print(f"  Poll error: {r.status_code}")
            continue
        data = r.json()
        runs = data.get("test_runs", [])
        pending = [x for x in runs if x.get("status") not in ("passed", "failed", "error")]
        print(f"    … {len(pending)}/{len(runs)} still running")
        if not pending:
            for run in runs:
                tid = run.get("test_id") or run.get("test_run_id", "")
                run["_name"] = id_to_name.get(tid, run.get("name", tid))
            return runs
    print("  TIMEOUT")
    return []


def print_results(results: List[Dict]) -> None:
    passed = failed = error = 0
    for r in results:
        status = r.get("status", "unknown")
        name   = r.get("_name") or r.get("name") or r.get("test_run_id", "?")
        cr     = r.get("condition_result", {})
        rat    = cr.get("rationale", {})
        if status == "passed":
            passed += 1
            print(f"  ✓ PASS  {name}")
        elif status == "failed":
            failed += 1
            print(f"  ✗ FAIL  {name}")
            summary = rat.get("summary", "")
            msgs    = rat.get("messages", [])
            if summary:
                print(f"         {summary}")
            if msgs:
                print(f"         {msgs[0][:200]}")
        else:
            error += 1
            print(f"  ? ERR   {name} [{status}]")
    print(f"\n{'='*60}")
    print(f"  {passed} passed  /  {failed} failed  /  {error} error  "
          f"(total {passed + failed + error})")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------
def _load_session() -> Optional[str]:
    if _SESSION_FILE.exists():
        try:
            return json.loads(_SESSION_FILE.read_text(encoding="utf-8")).get("agent_id")
        except Exception:
            return None
    return None


def _save_session(agent_id: str) -> None:
    _SESSION_FILE.write_text(
        json.dumps({"agent_id": agent_id}, indent=2), encoding="utf-8"
    )


def _clear_session() -> None:
    _SESSION_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=f"Node 2 scaffold tests — {CLINIC}")
    ap.add_argument("--run",       action="store_true")
    ap.add_argument("--create",    action="store_true")
    ap.add_argument("--cleanup",   action="store_true")
    ap.add_argument("--spec-only", action="store_true")
    ap.add_argument("--keep-agent",action="store_true")
    ap.add_argument("--agent-id",  help="Reuse this agent ID")
    args = ap.parse_args()

    tests = generate_tests()

    if args.spec_only:
        for t in tests:
            print(t["name"])
        return

    agent_id = args.agent_id or _load_session()

    if args.cleanup:
        if agent_id:
            delete_scaffold_agent(agent_id)
            _clear_session()
        else:
            print("No session agent to clean up.")
        return

    if not args.run:
        print("Use --run to execute, --spec-only to list tests.")
        return

    prompt = _load_prompt()
    print(f"Prompt loaded ({len(prompt)} chars)")

    if args.create and agent_id:
        delete_scaffold_agent(agent_id)
        _clear_session()
        agent_id = None

    if agent_id:
        ok = patch_scaffold_agent(agent_id, prompt)
        if not ok:
            print("Patch failed — creating fresh agent")
            agent_id = None

    if not agent_id:
        agent_id = create_scaffold_agent(prompt)
        if not agent_id:
            sys.exit(1)
        _save_session(agent_id)

    print(f"\nPushing {len(tests)} tests …")
    id_to_name = push_tests(agent_id, tests)

    if not id_to_name:
        print("No tests pushed.")
        sys.exit(1)

    print(f"\nRunning {len(id_to_name)} tests …")
    results = run_and_poll(agent_id, id_to_name)
    print_results(results)

    if not args.keep_agent:
        delete_scaffold_agent(agent_id)
        _clear_session()


if __name__ == "__main__":
    main()
