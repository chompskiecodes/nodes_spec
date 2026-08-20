#!/usr/bin/env python3
"""
test_node3_confirmation_only.py  (Northern Physio)

Minimal, cost-scoped live scaffold test for ONE change only: Node 3's CONFIRMATION
redesign (see project_node3_escape_confirmation_mandatory_part_fix_2026_08_15.md
memory / .claude/rules/node-edit-verification.md). Deliberately does NOT run the
full node3 scaffold battery in test_node3_scaffold.py (25+ tests, real API cost) —
scaffold tests cost money, and this change only touches the CONFIRMATION block, so
only CONFIRMATION is tested here.

Reuses the existing session scaffold agent (node3_scaffold_agent.json) rather than
creating a new one. IMPORTANT: that agent was created with SCAFFOLD_LLM="gpt-4.1"
by test_node3_scaffold.py, which is stale — production Node 3 runs claude-haiku-4-5
(confirmed via nodes/clinics/northern_physio/node_3_availability_handler.txt's own
"LLM: claude-haiku-4-5" header). This script patches BOTH the prompt AND the llm
field on the reused agent so the test actually exercises the real production model,
not gpt-4.1. Flagged separately for the full-battery file to be fixed too — out of
scope for this narrow run.

Exactly 2 tests:
  C1  — caller confirms a time -> universal_router intent="confirm_time" called
        with confirmed_time_spoken / confirmed_day_spoken / practitioner_name in
        the payload (the 3 new fields the backend now uses to build a real spoken
        message instead of the old inert "Routed successfully").
  C1B — the confirm_time tool result returns with a message field -> agent speaks
        it verbatim next turn, nothing added, no tool call. This is the actual
        production bug this change fixes (message:null observed live 20/20 times
        under the old same-turn filler-only design).

Usage:
    python nodes/clinics/northern_physio/test_node3_confirmation_only.py --run
    python nodes/clinics/northern_physio/test_node3_confirmation_only.py --agent-id <id> --run
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
CLINIC = "northern_physio"

SMART_ROUTER_TOOL_ID     = "tool_4501k96qzckzemabz9rwppjms6zj"   # smart_voice_agent / smart_router
UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"   # universal_router

# Matches production Node 3 LLM — see node_3_availability_handler.txt's "LLM:" header.
# The full-battery test_node3_scaffold.py hardcodes the stale "gpt-4.1"; do not copy that here.
SCAFFOLD_LLM       = "claude-haiku-4-5"
POLL_INTERVAL_SECS = 14
POLL_TIMEOUT_SECS  = 300

_SESSION_FILE_N3 = CLINIC_DIR / "node3_scaffold_agent.json"


# ── Prompt loading (identical to test_node3_scaffold.py's load_node3) ─────────

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
    """Node 3 is Override: Disabled — combine with the shared system prompt, as production does."""
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
    print(f"✓ Loaded Node 3 for '{CLINIC}' — {len(prompt):,} chars total")

    if 'CONFIRMATION — fires the instant confirmed_time is set. Call universal_router intent="confirm_time"' not in prompt:
        print("✗ Loaded prompt does NOT contain the new CONFIRMATION wording — "
              "did scripts/generate_node3.py --clinics northern_physio run since the template edit?")
        return None
    print("✓ Confirmed: loaded prompt contains the NEW CONFIRMATION design (call-then-speak-verbatim).")
    return prompt


# ── Test helpers ──────────────────────────────────────────────────────────────

def _m(role: str, text: str, t: int = 0) -> Dict:
    return {"role": role, "message": text, "time_in_call_secs": t}

def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}

def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}


def _entry_history(apt_type: str) -> List[Dict]:
    return [
        _m("user",  f"Hi, I'd like to book my {apt_type} appointment.", 2),
        _m("agent", "When would you like to come in?", 5),
        _m("user",  "As soon as possible this week please.", 8),
        _m("agent", "Checking that now, one moment.", 11),
    ]


# ── Test generation — exactly 2 tests ───────────────────────────────────────────

def generate_tests(fixtures: dict) -> list:
    p = f"[{CLINIC}]"
    apt_type = fixtures["default_appointment_type"]
    two_slots = fixtures["fixtures"]["single_practitioner_two_slots"]

    payload_no_meta = {k: v for k, v in two_slots.items() if not k.startswith("_")}
    fixture_msg = _m("agent", f"[smart_router response received]: {json.dumps(payload_no_meta)}", 14)

    band_q = "Do you prefer the morning or afternoon?"

    tests = []

    # C1 — caller confirms a time -> confirm_time called with the 3 new spoken-form fields.
    tests.append({
        "name": f"{p} C1 — Time confirmed: universal_router confirm_time called with spoken-form payload fields",
        "chat_history": _entry_history(apt_type) + [
            fixture_msg,
            _m("agent", band_q, 17),
            _m("user",  "Morning thanks.", 20),
            _m("agent", "I've got 9:00 AM or 11:00 AM on Wednesday.", 23),
            _m("user",  "9:00 AM works for me.", 26),
        ],
        "success_condition": (
            "PASS if the agent calls universal_router intent='confirm_time' with "
            "appointment_date='2026-04-08', appointment_time='09:00' (24h, not '9:00 AM'), "
            "practitioner_id='PRACT_001', business_id='BIZ_001', AND all three new fields: "
            "confirmed_time_spoken (a caller-facing form of 9:00 AM, e.g. '9:00 AM' or '9 AM'), "
            "confirmed_day_spoken (naming Wednesday the 8th), and practitioner_name='Dithu Beeram'. "
            "Per the current CONFIRMATION design, the tool call may be silent or carry a short "
            "filler phrase in this same turn — do NOT fail solely for a missing or present filler. "
            "FAIL if the agent speaks the full appointment recap in THIS turn (e.g. 'You're "
            "confirmed for 9am Wednesday with Dithu' before the tool result has returned), says "
            "'you're booked'/'you're all set'/'anything else?', omits any of the three new "
            "spoken-form payload fields, or calls smart_voice_agent/smart_router instead of "
            "universal_router."
        ),
        "success_examples": [
            _ok("One moment. [calls universal_router confirm_time appointment_date=2026-04-08 "
                "appointment_time=09:00 practitioner_id=PRACT_001 business_id=BIZ_001 "
                "confirmed_time_spoken='9:00 AM' confirmed_day_spoken='Wednesday the 8th' "
                "practitioner_name='Dithu Beeram']"),
            _ok("[silent — calls universal_router confirm_time with all fields above. "
                "No spoken output before the tool call = acceptable under the new design]"),
        ],
        "failure_examples": [
            _fail("Perfect, 9:00 AM Wednesday the 8th with Dithu Beeram at South Morang. "
                  "[calls universal_router confirm_time]"),
            _fail("[calls universal_router confirm_time but omits confirmed_time_spoken / "
                  "confirmed_day_spoken / practitioner_name]"),
            _fail("[calls smart_router instead of universal_router]"),
        ],
    })

    # C1B — tool result returns with a message field -> spoken verbatim, nothing added, no tool call.
    tests.append({
        "name": f"{p} C1B — Post-confirmation: speak confirm_time's message field verbatim, nothing added",
        "chat_history": _entry_history(apt_type) + [
            fixture_msg,
            _m("agent", band_q, 17),
            _m("user",  "Morning thanks.", 20),
            _m("agent", "I've got 9:00 AM or 11:00 AM on Wednesday.", 23),
            _m("user",  "9:00 AM works for me.", 26),
            _m("agent", "One moment.", 27),
            _m("agent",
               '[universal_router response]: {"status": "success", '
               '"message": "Great — you\'re confirmed for 9:00 AM on Wednesday the 8th with Dithu Beeram.", '
               '"uni_router_intent": "confirm_time"}',
               28),
        ],
        "success_condition": (
            "PASS if the agent's next spoken turn is exactly the tool result's message field, "
            "verbatim — \"Great — you're confirmed for 9:00 AM on Wednesday the 8th with Dithu "
            "Beeram.\" — with NO tool call in this turn, and nothing added or omitted: no opening "
            "word of its own ('Perfect,', 'So,'), no 'anything else?', no restating the service "
            "name, no asking for name/email (those belong to a later node). "
            "FAIL if the agent paraphrases, drops, or embellishes the message field, adds its own "
            "opening acknowledgement on top of the message field's own 'Great —', asks a follow-up "
            "question, or calls any tool in this turn."
        ),
        "success_examples": [
            _ok("Great — you're confirmed for 9:00 AM on Wednesday the 8th with Dithu Beeram."),
        ],
        "failure_examples": [
            _fail("Perfect! Great — you're confirmed for 9:00 AM on Wednesday the 8th with Dithu Beeram."),
            _fail("You're all set for 9am Wednesday with Dithu. Anything else?"),
            _fail("Great — you're confirmed for 9:00 AM on Wednesday the 8th with Dithu Beeram. "
                  "[also calls a tool]"),
        ],
    })

    return tests


# ── ElevenLabs API helpers ────────────────────────────────────────────────────

def _el_hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def load_session_agents() -> Dict:
    if _SESSION_FILE_N3.exists():
        try:
            d = json.loads(_SESSION_FILE_N3.read_text(encoding="utf-8"))
            return {"main": d.get("main"), "e2": d.get("e2")}
        except Exception:
            pass
    return {"main": None, "e2": None}


def verify_agent_alive(agent_id: str) -> bool:
    resp = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    return resp.status_code == 200


def patch_scaffold_agent_prompt_and_llm(agent_id: str, node3_prompt: str) -> bool:
    """Overwrite prompt AND llm — the reused agent was created with the stale gpt-4.1."""
    payload = {
        "conversation_config": {
            "agent": {"prompt": {"prompt": node3_prompt, "llm": SCAFFOLD_LLM, "temperature": 0.0}}
        }
    }
    resp = requests.patch(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs(), json=payload)
    if resp.status_code == 200:
        print(f"✓ Prompt + llm={SCAFFOLD_LLM} patched on agent {agent_id}")
        return True
    print(f"✗ Failed to patch agent: {resp.status_code} — {resp.text[:200]}")
    return False


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
            print(f"  … waiting {POLL_INTERVAL_SECS}s ({len(runs) - pending}/{len(runs)} done)")
        time.sleep(POLL_INTERVAL_SECS)
    print("✗ Timed out waiting for results.")
    return None


def print_results(result: Dict, name_map: Dict[str, str]) -> None:
    runs = result.get("test_runs", [])
    passed_runs = [r for r in runs if r.get("status") == "passed"]
    failed_runs  = [r for r in runs if r.get("status") != "passed"]

    print(f"\n── Results ({'✓' if not failed_runs else '✗'} {len(passed_runs)}/{len(runs)}) ─────────────────────────")

    if passed_runs:
        print(f"\n  PASSED ({len(passed_runs)})")
        for r in passed_runs:
            print(f"  ✓  {name_map.get(r['test_run_id'], r['test_run_id'])}")

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
            print(f"       Agent: \"{agent_msg[:200]}\"")
            if tool_names:
                print(f"       Tools: {tool_names}")
                for tn, ta in zip(tool_names, tool_args):
                    if ta:
                        print(f"         → {tn}: {json.dumps(ta)[:300]}")
            if rationale:
                print(f"       Reason: {rationale[:200]}")
    print()


def _build_name_map(runs: List[Dict], tests: List[Dict], name_map: Dict[str, str]) -> None:
    def fingerprint(hist: List[Dict]) -> str:
        # Include the LAST message regardless of role, not just the last USER message —
        # C1 and C1B share an identical first/last user turn (C1B's extra turns after the
        # caller confirms are all agent-role tool-result injections), so a user-only
        # fingerprint collides between them and mislabels both results as the same test.
        user_msgs = [m["message"] for m in hist if m.get("role") == "user"]
        last_msg = hist[-1]["message"] if hist else ""
        return f"{user_msgs[0] if user_msgs else ''}||{last_msg}"
    test_fp = {fingerprint(t["chat_history"]): t["name"] for t in tests}
    for run in runs:
        ti   = run.get("test_info", {}) or {}
        hist = ti.get("chat_history", [])
        fp   = fingerprint(hist)
        name_map[run["test_run_id"]] = test_fp.get(fp, run["test_run_id"])


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Node 3 CONFIRMATION-only scaffold test (northern_physio)")
    parser.add_argument("--agent-id", help="Pin to a specific agent ID (default: reuse session agent from node3_scaffold_agent.json)")
    parser.add_argument("--run", action="store_true", help="Run the 2 tests after pushing them")
    args = parser.parse_args()

    if not ELEVENLABS_API_KEY:
        print("✗ ELEVENLABS_API_KEY not set in .env"); sys.exit(1)

    node3_prompt = load_node3()
    if not node3_prompt:
        sys.exit(1)

    fixtures_path = CLINIC_DIR / "node3_fixtures.json"
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))

    tests = generate_tests(fixtures)
    print(f"✓ Generated exactly {len(tests)} tests (CONFIRMATION only — not the full battery)")

    agent_id = args.agent_id
    if not agent_id:
        session = load_session_agents()
        agent_id = session.get("main")
        if not agent_id or not verify_agent_alive(agent_id):
            print("✗ No live session agent found. Run test_node3_scaffold.py --run once first "
                  "to create one, or pass --agent-id explicitly.")
            sys.exit(1)
        print(f"✓ Reusing existing session agent: {agent_id}")

    if not patch_scaffold_agent_prompt_and_llm(agent_id, node3_prompt):
        sys.exit(1)

    test_ids = []
    for t in tests:
        tid = push_test(t)
        if tid:
            test_ids.append(tid)
            print(f"  ✓ pushed {t['name']}")
    if not test_ids:
        print("✗ No tests pushed."); sys.exit(1)

    if args.run:
        print(f"\nRunning {len(test_ids)} tests on agent {agent_id}...")
        inv_id = dispatch_tests(agent_id, test_ids)
        name_map: Dict[str, str] = {}
        if inv_id:
            result = poll_invocation(inv_id)
            if result:
                _build_name_map(result.get("test_runs", []), tests, name_map)
                print_results(result, name_map)

    # Always clean up test cases from the agent-testing UI — keeps it tidy, no cost either way.
    for tid in test_ids:
        delete_test(tid)
    print(f"✓ {len(test_ids)} test case(s) deleted from agent-testing UI.")
    print(f"ℹ  Agent {agent_id} left as-is (session-managed by test_node3_scaffold.py — "
          f"not deleted here). Its prompt/llm were patched to the CONFIRMATION-tested state; "
          f"the next full-battery run will re-patch it back to that file's own settings.")
    print("Done.")


if __name__ == "__main__":
    main()
