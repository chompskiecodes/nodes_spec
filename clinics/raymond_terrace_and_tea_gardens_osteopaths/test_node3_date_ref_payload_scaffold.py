#!/usr/bin/env python3
"""
test_node3_date_ref_payload_scaffold.py  (Raymond Terrace and Tea Gardens Osteopaths, P2)

NARROW-SCOPE scaffold — tests ONLY the smart_voice_agent payload shapes the
2026-08-17 date_reference_resolver fix + fleet-wide Node 3 template fix depend on.
Does NOT cover the rest of Node 3 (practitioner/location disambiguation, slot
offer, confirmation, escapes) — see test_node3_scaffold.py conventions for that
broader coverage. Deliberately kept to 5 tests because ElevenLabs agent-testing
invocations cost money to run; do not add unrelated scenarios to this file.

Covers:
  P1 — bare named month, no weekday ("sometime in November")
       -> intent="find_next_available", date_ref_month="November", detail="summary"
       Backend bug fixed: resolve_date_reference() previously fell through every
       branch and silently dropped a bare date_ref_month, returning {}.
  P2 — weekday WITHIN a named month ("a Monday in November")            [NEW rule]
       -> intent="find_next_available", requested_weekday="Monday", date_ref_month="November"
  P3 — weekday_list WITHIN a named month ("Monday, Tuesday or Wednesday in September") [NEW rule]
       -> intent="find_next_available", date_ref_weekday_list=["Monday","Tuesday","Wednesday"],
          date_ref_month="September"
       Backend bug fixed: resolve_date_reference() let a weekday_list win unconditionally
       and silently dropped the month.
  R1 — regression: weekday_list alone, no month ("Thursday or Friday")
       -> intent="availability", date_ref_weekday_list=["Thursday","Friday"], detail="slots"
       Confirms the new month-window branch didn't shadow the existing MULTI-DAY rule.
  R2 — regression: bare recurring weekday alone, no month ("any Mondays")
       -> intent="find_next_available", requested_weekday="Monday", max_days=31
       Confirms the new "weekday WITHIN a month" rule didn't shadow the existing
       "recurring weekday, no band" rule when no month is named.

Agent lifecycle:
  - First run:  one scaffold agent created; ID saved to node3_date_ref_scaffold_agent.json
  - Subsequent: agent reused; prompt patched with latest local file
  - All pass:   agent auto-deleted and session file cleared
  - --cleanup:  force-delete the session agent at any time and exit
  - --keep-agent: suppress auto-delete even when all tests pass

Usage:
    python nodes/clinics/raymond_terrace_and_tea_gardens_osteopaths/test_node3_date_ref_payload_scaffold.py --run
    python nodes/clinics/raymond_terrace_and_tea_gardens_osteopaths/test_node3_date_ref_payload_scaffold.py --run --filter P1
    python nodes/clinics/raymond_terrace_and_tea_gardens_osteopaths/test_node3_date_ref_payload_scaffold.py --cleanup
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
CLINIC = "raymond_terrace_and_tea_gardens_osteopaths"

# Shared fleet-wide tool IDs (same across every clinic's scaffold tests).
SMART_ROUTER_TOOL_ID     = "tool_4501k96qzckzemabz9rwppjms6zj"   # smart_voice_agent / smart_router
UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"   # universal_router

SCAFFOLD_LLM       = "claude-haiku-4-5"  # matches production Node 3 LLM for this clinic (P2 pattern)
POLL_INTERVAL_SECS = 14
POLL_TIMEOUT_SECS  = 300

_SESSION_FILE = CLINIC_DIR / "node3_date_ref_scaffold_agent.json"

# Real clinic data (ebf86b4f-37af-45f4-b41b-21d57469c027), pulled read-only from prod DB
# 2026-08-17 — appointment type + practitioners + locations, so PRACTITIONER PREFERENCE
# and LOCATION resolve/skip deterministically and don't add extra turns before the
# payload-producing tool call under test.
APT_ID   = "412451910419749866"
APT_TYPE = "1 Standard Appointment"
# Only Bruce Sutton offers "1 Standard Appointment" here -> PRACTITIONER PREFERENCE
# finds exactly 1 match -> skips silently (no extra question before the tool call).
# NOTE: avoid any appointment-type name containing a parenthetical number (e.g. the real
# "CCMP (81350)") here — a 2026-08-17 live scaffold run showed the model latching onto
# that decoy digit string as appointment_type_id instead of the real {{appointment_type_id}}
# DV. This was a scaffold fixture defect, not a real Node 3 prompt bug.
PRACTITIONER_SERVICES = "Bruce Sutton=1 Standard Appointment;DVA Raymond Terrace|Elisa Brownhill=New Patient Raymond Terrace"
PRACTITIONERS_WITH_IDS = "Bruce Sutton:412461073866693445, Elisa Brownhill:883714138008722063"
PRACTITIONERS_COMMA = "Bruce Sutton, Elisa Brownhill"
LOCATIONS_COMMA = "Raymond Terrace, Tea Gardens"
# 2026-08-11 is a Tuesday — matches the resolver fix's own pytest fixtures for continuity.
CURRENT_TIME_LOCAL = "2026-08-11 09:00"


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
        if stripped.startswith("#") or stripped.startswith("=") or stripped == "FRAMEWORK":
            return "\n".join(lines[i:]).strip()
    return content.strip()


def load_node3() -> Optional[str]:
    """Node 3 is Override: Disabled — always runs combined with the shared system prompt."""
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

    prompt = system_prompt + "\n\n" + additional_prompt
    print(f"✓ Loaded Node 3 for '{CLINIC}' — system_prompt ({len(system_prompt):,} chars) "
          f"+ additional_prompt ({len(additional_prompt):,} chars) = {len(prompt):,} chars total")
    return prompt


# ── Test helpers ──────────────────────────────────────────────────────────────

def _m(role: str, text: str, t: int = 0) -> Dict:
    return {"role": role, "message": text, "time_in_call_secs": t}

def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}

def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}


def _entry3(apt_type: str) -> list:
    """2-turn pre-tool history: caller names service, agent asks the TIMEFRAME QUESTION."""
    return [
        _m("user",  f"Hi, I'd like to book my {apt_type} appointment please.", 2),
        _m("agent", "When would you like to come in?", 5),
    ]


# ── Test generation ──────────────────────────────────────────────────────────

def generate_tests() -> list:
    tests = []
    p = f"[{CLINIC}]"

    tests.append({
        "name": f"{p} P1 — Bare named month, no weekday: find_next_available date_ref_month",
        "chat_history": _entry3(APT_TYPE) + [
            _m("user", "Do you have anything available sometime in November?", 8),
        ],
        "success_condition": (
            "Caller names a future month (November) with no weekday, no week-ordinal, and no "
            "'this/next month' phrasing. Per TIMEFRAME -> PARAMS, agent calls smart_voice_agent "
            "with intent='find_next_available', date_ref_month='November', detail='summary', "
            "appointment_type_id='412451910419749866'. Agent must NOT send a literal start_date "
            "or max_days itself (the backend resolves the month's window from date_ref_month), "
            "must NOT send date_ref_month_offset (never compute how many months away November is), "
            "and must NOT send requested_weekday or date_ref_weekday_list (no weekday was named). "
            "May say 'Checking that now, one moment.' first, or call silently — both acceptable. "
            "Does NOT ask 'When would you like to come in?' again. Does NOT call universal_router."
        ),
        "success_examples": [
            _ok("Checking that now, one moment. [calls smart_voice_agent intent=find_next_available "
                "date_ref_month=November detail=summary]"),
            _ok("[calls smart_voice_agent intent=find_next_available date_ref_month=November — "
                "silent call is acceptable]"),
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("[no tool call]"),
            _fail("[calls universal_router]"),
            _fail("[calls smart_voice_agent with a literal computed date instead of date_ref_month]"),
            _fail("[calls smart_voice_agent with date_ref_month_offset set instead of, or alongside, date_ref_month]"),
        ],
    })

    tests.append({
        "name": f"{p} P2 — Weekday WITHIN a named month: requested_weekday + date_ref_month",
        "chat_history": _entry3(APT_TYPE) + [
            _m("user", "Do you have a Monday in November?", 8),
        ],
        "success_condition": (
            "Caller names a weekday AND a future month together ('a Monday in November'). "
            "Agent calls smart_voice_agent with intent='find_next_available', "
            "requested_weekday='Monday', date_ref_month='November', "
            "appointment_type_id='412451910419749866'. Agent must NOT send a literal start_date "
            "or max_days itself, and must NOT send date_ref_weekday_list (only one weekday named). "
            "May say 'Checking that now, one moment.' first, or call silently — both acceptable. "
            "Does NOT ask 'When would you like to come in?' again. Does NOT call universal_router."
        ),
        "success_examples": [
            _ok("Checking that now, one moment. [calls smart_voice_agent intent=find_next_available "
                "requested_weekday=Monday date_ref_month=November]"),
            _ok("[calls smart_voice_agent intent=find_next_available requested_weekday=Monday "
                "date_ref_month=November — silent call is acceptable]"),
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("[no tool call]"),
            _fail("[calls universal_router]"),
            _fail("[calls smart_voice_agent with requested_weekday=Monday but omits date_ref_month]"),
            _fail("[calls smart_voice_agent with date_ref_month=November but omits requested_weekday]"),
        ],
    })

    tests.append({
        "name": f"{p} P3 — Weekday LIST WITHIN a named month: date_ref_weekday_list + date_ref_month",
        "chat_history": _entry3(APT_TYPE) + [
            _m("user", "Any day — Monday, Tuesday or Wednesday, any time — in September works for me.", 8),
        ],
        "success_condition": (
            "Caller names three weekdays AND a future month together, in ONE request. Agent makes "
            "exactly ONE smart_voice_agent call with intent='find_next_available', "
            "date_ref_weekday_list=['Monday','Tuesday','Wednesday'] (caller's stated order), "
            "date_ref_month='September', appointment_type_id='412451910419749866'. Agent must NOT "
            "send requested_weekday (this is the list shape, not the single-weekday shape) and must "
            "NOT send a literal start_date or max_days itself. Agent must NOT make multiple "
            "sequential tool calls (e.g. one per weekday) — this shape is always a single call. "
            "May say 'Checking that now, one moment.' first, or call silently — both acceptable. "
            "Does NOT ask 'When would you like to come in?' again. Does NOT call universal_router."
        ),
        "success_examples": [
            _ok("Checking that now, one moment. [calls smart_voice_agent ONCE — intent=find_next_available "
                "date_ref_weekday_list=[Monday,Tuesday,Wednesday] date_ref_month=September]"),
            _ok("[calls smart_voice_agent ONCE — intent=find_next_available date_ref_weekday_list=[Monday,"
                "Tuesday,Wednesday] date_ref_month=September — silent call is acceptable]"),
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("[no tool call]"),
            _fail("[calls universal_router]"),
            _fail("[calls smart_voice_agent with requested_weekday=Monday instead of date_ref_weekday_list]"),
            _fail("[calls smart_voice_agent multiple times, once per weekday]"),
            _fail("[calls smart_voice_agent with date_ref_weekday_list set but date_ref_month omitted]"),
        ],
    })

    tests.append({
        "name": f"{p} R1 — Regression: weekday list alone, no month (MULTI-DAY, unaffected by the fix)",
        "chat_history": _entry3(APT_TYPE) + [
            _m("user", "Thursday or Friday, either one works for me.", 8),
        ],
        "success_condition": (
            "Caller names two specific weekdays with NO month mentioned. Per the MULTI-DAY rule, "
            "agent calls smart_voice_agent ONCE with intent='availability', "
            "date_ref_weekday_list=['Thursday','Friday'] (caller's stated order), detail='slots', "
            "appointment_type_id='412451910419749866'. Agent must NOT send date_ref_month (none was "
            "named) and must NOT send requested_weekday. This confirms the new month-window handling "
            "did not change behaviour when no month is present. "
            "May say 'Checking that now, one moment.' first, or call silently — both acceptable. "
            "Does NOT ask 'When would you like to come in?' again. Does NOT call universal_router."
        ),
        "success_examples": [
            _ok("Checking that now, one moment. [calls smart_voice_agent intent=availability "
                "date_ref_weekday_list=[Thursday,Friday] detail=slots]"),
            _ok("[calls smart_voice_agent intent=availability date_ref_weekday_list=[Thursday,Friday] "
                "— silent call is acceptable]"),
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("[no tool call]"),
            _fail("[calls universal_router]"),
            _fail("[calls smart_voice_agent with a date_ref_month value present]"),
        ],
    })

    tests.append({
        "name": f"{p} R2 — Regression: bare recurring weekday alone, no month (unaffected by the fix)",
        "chat_history": _entry3(APT_TYPE) + [
            _m("user", "Do you have any Mondays available?", 8),
        ],
        "success_condition": (
            "Caller asks an open-ended recurring-weekday question with NO month mentioned. Agent "
            "calls smart_voice_agent with intent='find_next_available', requested_weekday='Monday', "
            "max_days=31, appointment_type_id='412451910419749866'. Agent must NOT send date_ref_month "
            "(none was named) and must NOT send date_ref_weekday_list (only one weekday named). This "
            "confirms the new 'weekday WITHIN a month' rule did not swallow the existing plain "
            "recurring-weekday rule when no month is present. "
            "May say 'Checking that now, one moment.' first, or call silently — both acceptable. "
            "Does NOT ask 'When would you like to come in?' again. Does NOT call universal_router."
        ),
        "success_examples": [
            _ok("Checking that now, one moment. [calls smart_voice_agent intent=find_next_available "
                "requested_weekday=Monday max_days=31]"),
            _ok("[calls smart_voice_agent intent=find_next_available requested_weekday=Monday "
                "max_days=31 — silent call is acceptable]"),
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("[no tool call]"),
            _fail("[calls universal_router]"),
            _fail("[calls smart_voice_agent with a date_ref_month value present]"),
        ],
    })

    return tests


# ── ElevenLabs API helpers ────────────────────────────────────────────────────

def _el_hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def create_scaffold_agent(node3_prompt: str) -> Optional[str]:
    payload = {
        "name": f"[Node3 DateRef Payload Test] {CLINIC}",
        "conversation_config": {
            "agent": {
                "first_message": "Thanks for calling Raymond Terrace and Tea Gardens Osteopaths, how can I help you today?",
                "prompt": {
                    "prompt": node3_prompt,
                    "llm": SCAFFOLD_LLM,
                    "tool_ids": [
                        SMART_ROUTER_TOOL_ID,
                        UNIVERSAL_ROUTER_TOOL_ID,
                    ],
                    "temperature": 0.0,
                    "max_tokens": 1024,
                },
                "dynamic_variables": {
                    "dynamic_variable_placeholders": {
                        "called_number":           "+61285318641",
                        "caller_id":               "+61411111111",
                        "caller_phone":             "+61411111111",
                        "system__called_number":   "+61285318641",
                        "system__caller_id":       "+61411111111",
                        "current_time_local":      CURRENT_TIME_LOCAL,
                        "appointment_type_id":     APT_ID,
                        "appointment_type":        APT_TYPE,
                        "booking_for":             "",
                        "patient_status":          "existing",
                        "uni_router_intent":       "",
                        "timeframe_raw":           "",
                        "practitioner_preference": "",
                        "practitioner_services":   PRACTITIONER_SERVICES,
                        "practitioners_with_ids":  PRACTITIONERS_WITH_IDS,
                        "practitioners_comma":     PRACTITIONERS_COMMA,
                        "locations_comma":         LOCATIONS_COMMA,
                        "new_patient_allocation_enabled": "true",
                        "info_answered":           "",
                        "cancellation_completed":  "",
                        "reschedule_mode":         "",
                        "return_node":             "",
                        "patient_name_raw":        "Test Caller",
                    }
                },
            },
            "conversation": {"text_only": True},
        },
    }
    resp = requests.post(f"{BASE_URL}/agents/create", headers=_el_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        agent_id = resp.json().get("agent_id")
        print(f"✓ Scaffold agent created: {agent_id}")
        print(f"  Use --agent-id {agent_id} to reuse this agent in future runs.")
        return agent_id
    print(f"✗ Failed to create agent: {resp.status_code} — {resp.text[:300]}")
    return None


def delete_scaffold_agent(agent_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    if resp.status_code in (200, 204):
        print(f"✓ Agent {agent_id} deleted.")
    else:
        print(f"✗ Failed to delete agent {agent_id}: {resp.status_code}")


def load_session_agent() -> Optional[str]:
    if _SESSION_FILE.exists():
        try:
            return json.loads(_SESSION_FILE.read_text(encoding="utf-8")).get("main")
        except Exception:
            pass
    return None


def save_session_agent(agent_id: str) -> None:
    _SESSION_FILE.write_text(json.dumps({"main": agent_id}, indent=2), encoding="utf-8")


def clear_session_agent() -> None:
    if _SESSION_FILE.exists():
        _SESSION_FILE.unlink()


def verify_agent_alive(agent_id: str) -> bool:
    resp = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    return resp.status_code == 200


def patch_scaffold_agent_prompt(agent_id: str, node3_prompt: str) -> bool:
    payload = {"conversation_config": {"agent": {"prompt": {"prompt": node3_prompt}}}}
    resp = requests.patch(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs(), json=payload)
    if resp.status_code == 200:
        print(f"✓ Prompt patched on session agent {agent_id}")
        return True
    print(f"✗ Failed to patch agent prompt: {resp.status_code} — {resp.text[:200]}")
    return False


def delete_test(test_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agent-testing/{test_id}", headers=_el_hdrs())
    if resp.status_code not in (200, 204):
        print(f"  ✗ Failed to delete test {test_id}: {resp.status_code}")


def delete_tests(test_ids: List[str]) -> None:
    for tid in test_ids:
        delete_test(tid)
    if test_ids:
        print(f"✓ {len(test_ids)} test(s) deleted from agent-testing UI.")


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
    print(f"  ✗ Failed to create '{t['name']}': {resp.status_code} — {resp.text[:200]}")
    return None


def dispatch_tests(agent_id: str, test_ids: List[str]) -> Optional[str]:
    payload = {"tests": [{"test_id": tid} for tid in test_ids]}
    resp = requests.post(f"{BASE_URL}/agents/{agent_id}/run-tests", headers=_el_hdrs(), json=payload)
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
        resp = requests.get(f"{BASE_URL}/test-invocations/{invocation_id}", headers=_el_hdrs())
        if resp.status_code == 200:
            data = resp.json()
            runs = data.get("test_runs", [])
            pending = sum(1 for r in runs if r.get("status") not in ("passed", "failed"))
            if runs and pending == 0:
                return data
            elapsed = int(time.time() - (deadline - POLL_TIMEOUT_SECS))
            print(f"  … [{elapsed}s] {len(runs) - pending}/{len(runs)} done, waiting {POLL_INTERVAL_SECS}s")
        time.sleep(POLL_INTERVAL_SECS)
    print("✗ Timed out waiting for results.")
    return None


def print_results(result: Dict, name_map: Dict[str, str]) -> set:
    runs = result.get("test_runs", [])
    newly_passed = set()
    passed_runs = [r for r in runs if r.get("status") == "passed"]
    failed_runs  = [r for r in runs if r.get("status") != "passed"]

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
                "[no spoken output]"
            )
            all_tool_calls = []
            for resp in agent_responses:
                if resp.get("role") == "agent":
                    all_tool_calls.extend(resp.get("tool_calls") or [])
            tool_names = [tc.get("tool_name", "") for tc in all_tool_calls]
            tool_args  = [tc.get("parameters") or tc.get("tool_input") or tc.get("arguments") or {}
                          for tc in all_tool_calls]
            ev = r.get("evaluation") or {}
            rationale = ev.get("rationale") or ""
            print(f"  ✗  {name}")
            print(f"       Agent: \"{agent_msg[:120]}\"")
            if tool_names:
                print(f"       Tools: {tool_names}")
                for tn, ta in zip(tool_names, tool_args):
                    if ta:
                        print(f"         → {tn}: {json.dumps(ta)[:250]}")
            if rationale:
                print(f"       Reason: {rationale[:150]}")
    print()
    return newly_passed


def _build_name_map(runs: List[Dict], tests: List[Dict], name_map: Dict[str, str]) -> None:
    def fingerprint(hist: List[Dict]) -> str:
        user_msgs = [m["message"] for m in hist if m.get("role") == "user"]
        return f"{user_msgs[0] if user_msgs else ''}||{user_msgs[-1] if user_msgs else ''}"
    test_fp = {fingerprint(t["chat_history"]): t["name"] for t in tests}
    for run in runs:
        ti   = run.get("test_info", {}) or {}
        hist = ti.get("chat_history", [])
        fp   = fingerprint(hist)
        name_map[run["test_run_id"]] = test_fp.get(fp, run["test_run_id"])


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Node 3 date_ref payload-only test scaffold — {CLINIC} (5 tests, NOT full coverage)"
    )
    parser.add_argument("--agent-id",   help="Pin to a specific agent ID (bypasses session management — never auto-deleted)")
    parser.add_argument("--run",        action="store_true", help="Run tests after creating/patching them")
    parser.add_argument("--keep-agent", action="store_true", help="Do not auto-delete even when all tests pass")
    parser.add_argument("--cleanup",    action="store_true", help="Delete the session agent and exit (no tests run)")
    parser.add_argument("--reset",      action="store_true", help="Ignore previously passed tests and run everything")
    parser.add_argument("--filter",     default="", help="Only run tests whose name contains this string (e.g. 'P1')")
    args = parser.parse_args()

    if not ELEVENLABS_API_KEY:
        print("✗ ELEVENLABS_API_KEY not set in .env"); sys.exit(1)

    node3_prompt = load_node3()
    if not node3_prompt:
        sys.exit(1)

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
        print(f"✓ Generated {len(all_tests)} test cases (payload-only, 5 max by design)")

    if not tests_to_run:
        print("✓ All tests already passing — nothing to run.")
        print("  Use --reset to force a full re-run.")
        return

    if args.cleanup:
        agent_id = load_session_agent()
        if agent_id:
            print(f"Cleaning up session agent {agent_id}...")
            delete_scaffold_agent(agent_id)
            clear_session_agent()
        else:
            print("No session agent found — nothing to clean up.")
        return

    agent_id = args.agent_id
    session_managed = False

    if agent_id:
        print(f"Patching prompt on pinned agent {agent_id}...")
        patch_scaffold_agent_prompt(agent_id, node3_prompt)
    else:
        session_managed = True
        existing = load_session_agent()
        if existing:
            if verify_agent_alive(existing):
                print(f"✓ Session agent found: {existing}")
                if patch_scaffold_agent_prompt(existing, node3_prompt):
                    agent_id = existing
                else:
                    clear_session_agent()
            else:
                print(f"  Session agent {existing} no longer exists — creating fresh.")
                clear_session_agent()

        if not agent_id:
            agent_id = create_scaffold_agent(node3_prompt)
            if not agent_id:
                sys.exit(1)
            save_session_agent(agent_id)

    print(f"\nPushing {len(tests_to_run)} tests to ElevenLabs agent-testing API...")
    test_ids = []
    for t in tests_to_run:
        tid = push_test(t)
        if tid:
            test_ids.append(tid)
            print(f"  ✓ {t['name']}")
    print(f"✓ {len(test_ids)}/{len(tests_to_run)} test cases created")

    name_map: Dict[str, str] = {}
    newly_passed: set = set()

    if args.run and test_ids:
        print(f"\nRunning {len(test_ids)} tests on agent {agent_id}...")
        inv_id = dispatch_tests(agent_id, test_ids)
        if inv_id:
            result = poll_invocation(inv_id)
            if result:
                _build_name_map(result.get("test_runs", []), tests_to_run, name_map)
                newly_passed |= print_results(result, name_map)

        if newly_passed:
            updated_passed = previously_passed | newly_passed
            save_passed_tests(updated_passed)
            print(f"✓ Pass registry updated — {len(updated_passed)} tests now marked passing.")

    if test_ids:
        delete_tests(test_ids)

    if session_managed and args.run:
        updated_passed = previously_passed | newly_passed
        all_pass = (len(updated_passed) == len(all_tests))
        if all_pass and not args.keep_agent:
            print(f"✓ All {len(all_tests)} tests passing — deleting scaffold agent.")
            delete_scaffold_agent(agent_id)
            clear_session_agent()
        elif all_pass:
            print(f"ℹ  All tests passing — agent kept (--keep-agent): {agent_id}")
        else:
            remaining = len(all_tests) - len(updated_passed)
            print(f"ℹ  {remaining} test(s) still failing — scaffold agent retained for next run: {agent_id}")
            print(f"   (auto-reused on next run, or --cleanup to force delete)")
    elif session_managed and not args.run:
        print(f"ℹ  Tests pushed but not run — scaffold agent retained: {agent_id}")

    print("Done.")


def load_passed_tests() -> set:
    path = CLINIC_DIR / "node3_date_ref_passed_tests.json"
    if path.exists():
        return set(json.loads(path.read_text(encoding="utf-8")))
    return set()


def save_passed_tests(passed: set) -> None:
    path = CLINIC_DIR / "node3_date_ref_passed_tests.json"
    path.write_text(json.dumps(sorted(passed), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
