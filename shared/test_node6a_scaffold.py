#!/usr/bin/env python3
"""
test_node6a_scaffold.py  (shared — Node 6a)

Targeted scaffold test for the failing scenario in Node 6a (Name Collection – Self):

    When {{caller_phone}} (or {{caller_id}}) is already set to the real ANI at call init,
    the agent must skip step 2 (phone collection) silently and go straight to step 3
    (email).  The failing behaviour is asking "And what's a good number to reach you on?"
    when the ANI is already known.

DV injection mechanism:
    ElevenLabs test simulation substitutes dynamic_variable_placeholders into {{dv_name}}
    tokens in the prompt.  Setting caller_phone="+61412345678" in the placeholders makes
    PRE-COLLECTION and step 2 see a real, non-anonymous number — exactly what call init
    does at runtime via twilio_init_webhook.py (dynamic_vars["caller_phone"] = caller_id).

Node 6a is Override: Disabled → system_prompt.txt is prepended to its Additional Prompt
before the scaffold agent is created, matching the runtime context the LLM actually sees.

Usage:
    # First run — creates a scaffold agent, saves ID to node6a_scaffold_agent.json
    py -X utf8 nodes/shared/test_node6a_scaffold.py --run

    # Subsequent runs — reuses the saved agent ID and re-patches the prompt
    py -X utf8 nodes/shared/test_node6a_scaffold.py --run

    # Reuse a specific agent ID
    py -X utf8 nodes/shared/test_node6a_scaffold.py --agent-id <id> --run

    # Force delete the session agent at any time
    py -X utf8 nodes/shared/test_node6a_scaffold.py --cleanup

    # Preview the full scaffold prompt without running
    py -X utf8 nodes/shared/test_node6a_scaffold.py --show-prompt
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

# ── Config ─────────────────────────────────────────────────────────────────────

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = "https://api.elevenlabs.io/v1/convai"

# This script lives in nodes/shared/; repo root is two levels up.
SHARED_DIR   = Path(__file__).parent
REPO_ROOT    = SHARED_DIR.parent.parent   # Nucaching/
NODE6A_FILE  = SHARED_DIR / "node_6a_name_collection_self.txt"
SYS_PROMPT   = SHARED_DIR / "system_prompt.txt"

SCAFFOLD_LLM       = "claude-haiku-4-5"   # must match production LLM for node 6a
POLL_INTERVAL_SECS = 12
POLL_TIMEOUT_SECS  = 300

_SESSION_FILE = SHARED_DIR / "node6a_scaffold_agent.json"


# ── Prompt loading ─────────────────────────────────────────────────────────────

def _extract_additional_prompt(content: str) -> str:
    """Extract everything from 'Additional Prompt:' onwards, stripping the header block."""
    idx = content.find("Additional Prompt:")
    if idx == -1:
        # Fall back to returning everything if the marker isn't found.
        return content.strip()
    after = content[idx + len("Additional Prompt:"):]
    # Strip leading blank lines.
    return after.lstrip("\r\n").strip()


def load_combined_prompt(
    presubstitute_dvs: Optional[Dict] = None,
    node_only: bool = False,
) -> Optional[str]:
    """
    Concatenate system_prompt.txt + node 6a Additional Prompt (default), or
    return only the node 6a Additional Prompt when node_only=True.

    Override: Disabled means ElevenLabs prepends the system prompt at runtime —
    we replicate that in the default mode.  node_only=True isolates whether the
    44k combined prompt context length is causing instruction dropout.

    If presubstitute_dvs is given, replace every {{key}} token in the text.
    """
    if not NODE6A_FILE.exists():
        print(f"✗ Node 6a file not found: {NODE6A_FILE}")
        return None

    node_raw  = NODE6A_FILE.read_text(encoding="utf-8")
    node_text = _extract_additional_prompt(node_raw)

    if node_only:
        combined = node_text
        label = f"node 6a only — {len(node_text):,} chars (system_prompt.txt omitted)"
    else:
        if not SYS_PROMPT.exists():
            print(f"✗ system_prompt.txt not found: {SYS_PROMPT}")
            return None
        sys_text = SYS_PROMPT.read_text(encoding="utf-8").strip()
        combined = f"{sys_text}\n\n{node_text}"
        label = f"{len(sys_text):,} chars (system) + {len(node_text):,} chars (node 6a)"

    if presubstitute_dvs:
        for key, val in presubstitute_dvs.items():
            combined = combined.replace(f"{{{{{key}}}}}", val)
        print(f"✓ Prompt: {label} (pre-substituted {len(presubstitute_dvs)} DVs)")
        # Diagnostics
        phone_val = presubstitute_dvs.get("caller_phone", "")
        if phone_val:
            print(f"  {phone_val!r} in prompt: {phone_val in combined}")
            print(f"  {{{{caller_phone}}}} still present: {'{{caller_phone}}' in combined}")
    else:
        print(f"✓ Prompt: {label}")

    return combined


# ── Dynamic variable placeholders ──────────────────────────────────────────────
#
# Two sets:
#   _DVS_PHONE_KNOWN  — caller_phone already set (the scenario being tested; phone skip must fire)
#   _DVS_PHONE_EMPTY  — caller_phone empty (negative control; agent SHOULD ask for phone)
#
# ElevenLabs substitutes these into {{dv_name}} tokens in the prompt text when running
# simulated tests.  These mirror what twilio_init_webhook.py injects at real call init.

def _base_dvs(caller_phone: str, caller_id_val: str) -> Dict:
    return {
        # ── Identity / caller ──────────────────────────────────────────────
        "caller_phone":           caller_phone,
        "caller_id":              caller_id_val,
        "system__caller_id":      "+61452851341",   # Telnyx SIP proxy (should NOT be used)
        "caller_first_name":      "",               # not yet known
        "caller_last_name":       "",               # not yet known
        "caller_email":           "",               # not yet known
        "patient_name_raw":       "",               # not yet known
        # ── Call routing ───────────────────────────────────────────────────
        "called_number":          "+61398765432",
        "system__called_number":  "+61398765432",
        "system__conversation_id": "test-conv-001",
        "session_id":             "test-session-001",
        # ── Booking context (set upstream by nodes 2/3) ───────────────────
        "appointment_type":       "Physiotherapy",
        "appointment_type_id":    "99999999",
        "appointment_date":       "2026-08-12",
        "appointment_time":       "10:00 AM",
        "practitioner_id":        "",
        "business_id":            "",
        "business_name":          "",
        "booking_for":            "self",
        "patient_status":         "new",
        # ── Flags ──────────────────────────────────────────────────────────
        "uni_router_intent":      "",
        "cancellation_completed": "",
        "reschedule_mode":        "",
        "wrap_routing_flag":      "",
        "info_answered":          "",
        "constraint_changed":     "",
        "group_or_private":       "private",
    }


_DVS_PHONE_KNOWN = _base_dvs("+61412345678", "+61412345678")
_DVS_PHONE_EMPTY = _base_dvs("", "")


# ── Test helpers ───────────────────────────────────────────────────────────────

def _m(role: str, text: str, t: int = 0) -> Dict:
    return {"role": role, "message": text, "time_in_call_secs": t}

def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}

def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}


# ── Test cases ─────────────────────────────────────────────────────────────────

def generate_tests() -> List[Dict]:
    """
    One targeted test for the failing scenario.

    Scenario (PH_SKIP):
        caller_phone DV = "+61412345678" (real ANI, set at call init)
        Name has just been fully collected and confirmed (S,M,I,T,H → "is that right?" → "Yes").
        Step 2 (PHONE) should be silently skipped because PRE-COLLECTION fires.
        Agent must proceed directly to step 3: ask for email.

    What this proves:
        The PRE-COLLECTION gate ("{{caller_phone}} or {{caller_id}} holds a value other than
        'anonymous'") fires correctly when the DV is populated via call init.  This is the
        exact condition that was failing: agents were asking "And what's a good number to
        reach you on?" even when caller_phone was already set.

    NOTE: name confirmation uses the standard CONFIRM path (spell surname letter-by-letter →
    read back → caller says "yes").  The final user message ("Yes, that's right.") resolves
    name. The agent must then go straight to email — NOT phone.
    """
    tests = []

    # ── PH_SKIP ── caller_phone known → phone step must be silently skipped ───

    tests.append({
        "name": "[node6a] PH_SKIP — caller_phone DV set → phone step skipped → email asked",
        "chat_history": [
            # Add minimal booking context matching what real production conversations look like:
            # by the time node 6a runs, a time slot has already been confirmed in node 3.
            # This context weakens the name→phone inertia that fires in a zero-context conversation.
            _m("agent", "I have a slot available on Wednesday the 12th at 10 AM — shall I book that for you?", 2),
            _m("user",  "Yes please.", 5),
            _m("agent", "Perfect. Just need a few details. What's your full name for the booking?", 8),
            _m("user",  "It's Jane Smith.", 11),
            _m("agent", "And could you spell your last name for me?", 14),
            _m("user",  "S, M, I, T, H.", 17),
            _m("agent", "So that's S, M, I, T, H — is that right?", 20),
            _m("user",  "Yes, that's right.", 23),
        ],
        # DV set is injected via _DVS_PHONE_KNOWN at agent-creation time.
        # At runtime ElevenLabs substitutes {{caller_phone}} → "+61412345678"
        # before the LLM sees the prompt.
        "_dvs": "_DVS_PHONE_KNOWN",
        "success_condition": (
            "caller_phone DV is already set to '+61412345678' (real ANI from call init). "
            "Name 'Jane Smith' has just been confirmed. "
            "PRE-COLLECTION fires: step 2 (PHONE) must be SILENTLY SKIPPED — "
            "the agent must NOT ask for a phone number. "
            "PASS: agent asks for email — any paraphrase of "
            "'Do you have an email address for the booking?' is correct. "
            "FAIL: agent asks 'And what's a good number to reach you on?' "
            "or any other request for a phone number. "
            "EVALUATOR: the presence of phone-number language ('number', 'reach you', 'contact number', "
            "'mobile', 'phone') anywhere in the agent's spoken output is an immediate FAIL."
        ),
        "success_examples": [
            _ok("Do you have an email address for the booking?"),
            _ok("Great! Do you have an email we can use for the booking?"),
            _ok("And do you have an email address?"),
        ],
        "failure_examples": [
            _fail("And what's a good number to reach you on?"),
            _fail("What number can we reach you on?"),
            _fail("And your mobile number?"),
            _fail("Can I take a contact number for you?"),
        ],
    })

    return tests


# ── ElevenLabs API helpers ─────────────────────────────────────────────────────

def _hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def _create_agent(prompt: str, dvs: Dict) -> Optional[str]:
    """Create a scaffold agent with the combined prompt and given DV placeholders."""
    payload = {
        "name": "[Node6a Test] phone-skip scaffold",
        "conversation_config": {
            "agent": {
                "first_message": "",   # not used — tests inject mid-call history
                "prompt": {
                    "prompt": prompt,
                    "llm": SCAFFOLD_LLM,
                    "tool_ids": [],     # no tools needed — test checks spoken output only
                    "temperature": 0.0,
                    "max_tokens": 512,
                },
                "dynamic_variables": {
                    "dynamic_variable_placeholders": dvs
                },
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


def _patch_agent(agent_id: str, prompt: str, dvs: Dict) -> bool:
    """Re-patch the prompt and DVs on an existing scaffold agent."""
    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {"prompt": prompt},
                "dynamic_variables": {"dynamic_variable_placeholders": dvs},
            }
        }
    }
    resp = requests.patch(f"{BASE_URL}/agents/{agent_id}", headers=_hdrs(), json=payload)
    if resp.status_code == 200:
        print(f"✓ Prompt patched on agent {agent_id}")
        return True
    print(f"✗ Failed to patch agent: {resp.status_code} — {resp.text[:200]}")
    return False


def _agent_alive(agent_id: str) -> bool:
    return requests.get(f"{BASE_URL}/agents/{agent_id}", headers=_hdrs()).status_code == 200


def _delete_agent(agent_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agents/{agent_id}", headers=_hdrs())
    if resp.status_code in (200, 204):
        print(f"✓ Agent {agent_id} deleted.")
    else:
        print(f"✗ Delete failed for {agent_id}: {resp.status_code}")


# ── Session management ─────────────────────────────────────────────────────────

def _load_session() -> Optional[str]:
    if _SESSION_FILE.exists():
        try:
            return json.loads(_SESSION_FILE.read_text(encoding="utf-8")).get("agent_id")
        except Exception:
            return None
    return None


def _save_session(agent_id: str) -> None:
    _SESSION_FILE.write_text(json.dumps({"agent_id": agent_id}, indent=2), encoding="utf-8")


def _clear_session() -> None:
    if _SESSION_FILE.exists():
        _SESSION_FILE.unlink()


# ── Test execution ─────────────────────────────────────────────────────────────

def _push_test(test: Dict) -> Optional[str]:
    """Create a test case on ElevenLabs agent-testing API; return test_id or None."""
    payload = {
        "name":               test["name"],
        "chat_history":       test["chat_history"],
        "success_condition":  test["success_condition"],
        "success_examples":   test.get("success_examples", []),
        "failure_examples":   test.get("failure_examples", []),
    }
    resp = requests.post(f"{BASE_URL}/agent-testing/create", headers=_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        test_id = data.get("test_id") or data.get("id")
        print(f"  ✓ Pushed: {test['name'][:70]}  (id={test_id})")
        return test_id
    print(f"  ✗ Push failed ({resp.status_code}): {resp.text[:200]}")
    return None


def _dispatch_tests(agent_id: str, test_ids: List[str]) -> Optional[str]:
    """Dispatch tests against an agent; return invocation_id or None."""
    payload = {"tests": [{"test_id": tid} for tid in test_ids]}
    resp = requests.post(f"{BASE_URL}/agents/{agent_id}/run-tests", headers=_hdrs(), json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        inv_id = data.get("invocation_id") or data.get("id")
        print(f"✓ Tests dispatched — invocation: {inv_id}")
        return inv_id
    print(f"✗ Failed to dispatch tests: {resp.status_code} — {resp.text[:300]}")
    return None


def _poll_invocation(invocation_id: str) -> Optional[Dict]:
    """Poll until all test_runs reach a terminal status; return raw invocation data."""
    deadline = time.time() + POLL_TIMEOUT_SECS
    while time.time() < deadline:
        resp = requests.get(f"{BASE_URL}/test-invocations/{invocation_id}", headers=_hdrs())
        if resp.status_code == 200:
            data  = resp.json()
            runs  = data.get("test_runs", [])
            pending = sum(1 for r in runs if r.get("status") not in ("passed", "failed"))
            if runs and pending == 0:
                return data
            elapsed = int(time.time() - (deadline - POLL_TIMEOUT_SECS))
            print(f"  … [{elapsed}s] {len(runs) - pending}/{len(runs)} done — waiting {POLL_INTERVAL_SECS}s …")
        time.sleep(POLL_INTERVAL_SECS)
    print(f"✗ Timed out after {POLL_TIMEOUT_SECS}s")
    return None


def _delete_test(test_id: str) -> None:
    requests.delete(f"{BASE_URL}/agent-testing/{test_id}", headers=_hdrs())


def _fingerprint(chat_history: List[Dict]) -> str:
    user_msgs = [m["message"] for m in chat_history if m.get("role") == "user"]
    first = user_msgs[0] if user_msgs else ""
    last  = user_msgs[-1] if user_msgs else ""
    return f"{first}||{last}"


def _print_results(data: Dict, tests: List[Dict]) -> int:
    """Print invocation results; return count of failures."""
    runs = data.get("test_runs", [])
    # Build fingerprint → name map for matching runs back to local test names.
    fp_to_name = {_fingerprint(t["chat_history"]): t["name"] for t in tests}

    failures = 0
    for r in runs:
        ti        = r.get("test_info", {}) or {}
        hist      = ti.get("chat_history", [])
        name      = fp_to_name.get(_fingerprint(hist), r.get("test_run_id", "unknown"))
        status    = r.get("status", "")
        passed    = status == "passed"
        icon      = "✅" if passed else "❌"

        agent_responses = r.get("agent_responses") or []
        agent_msg = next(
            (str(x.get("message") or "") for x in agent_responses if x.get("role") == "agent"),
            "[no spoken output]",
        )
        ev        = r.get("evaluation") or {}
        rationale = ev.get("rationale") or ""

        print(f"\n{icon} {name}")
        print(f"   Agent said: {agent_msg!r:.200}")
        if not passed and rationale:
            print(f"   Reason: {rationale[:200]}")
        if not passed:
            failures += 1
    return failures


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Node 6a phone-skip scaffold test")
    parser.add_argument("--run",          action="store_true", help="Execute the test after pushing")
    parser.add_argument("--agent-id",     help="Reuse a specific EL scaffold agent ID")
    parser.add_argument("--cleanup",      action="store_true", help="Delete the session agent and exit")
    parser.add_argument("--keep-agent",   action="store_true", help="Keep agent alive even if tests pass")
    parser.add_argument("--show-prompt",  action="store_true", help="Print the combined prompt and exit")
    parser.add_argument(
        "--presubstitute", action="store_true",
        help=(
            "Pre-substitute DV values directly into the prompt text before sending to EL "
            "(mirrors what EL does at runtime).  Bypasses the dynamic_variable_placeholders "
            "mechanism — use to determine whether placeholder substitution is the failure cause."
        ),
    )
    parser.add_argument(
        "--node-only", action="store_true",
        help=(
            "Use ONLY the node 6a Additional Prompt — omit system_prompt.txt (~31k chars). "
            "Diagnostic: if this passes but the combined prompt fails, context length "
            "is the root cause.  Default is the combined prompt (system_prompt.txt + node 6a)."
        ),
    )
    args = parser.parse_args()

    if not ELEVENLABS_API_KEY:
        print("✗ ELEVENLABS_API_KEY not set in environment / .env")
        sys.exit(1)

    pre_dvs   = _DVS_PHONE_KNOWN if args.presubstitute else None
    node_only = getattr(args, "node_only", False)

    if node_only:
        print("⚙  --node-only: omitting system_prompt.txt (context-length isolation test)")
    if args.presubstitute:
        print("⚙  --presubstitute: replacing {{dv}} tokens directly in prompt text")

    # ── Show prompt ────────────────────────────────────────────────────────────
    if args.show_prompt:
        prompt = load_combined_prompt(presubstitute_dvs=pre_dvs, node_only=node_only)
        if prompt:
            print("\n" + "=" * 60 + " COMBINED PROMPT " + "=" * 60)
            print(prompt)
        sys.exit(0)

    # ── Cleanup ────────────────────────────────────────────────────────────────
    if args.cleanup:
        agent_id = args.agent_id or _load_session()
        if agent_id:
            _delete_agent(agent_id)
            _clear_session()
        else:
            print("No session agent found.")
        sys.exit(0)

    # ── Load prompt ────────────────────────────────────────────────────────────
    combined = load_combined_prompt(presubstitute_dvs=pre_dvs, node_only=node_only)
    if not combined:
        sys.exit(1)

    # ── Resolve agent ──────────────────────────────────────────────────────────
    agent_id = args.agent_id or _load_session()
    if agent_id and not _agent_alive(agent_id):
        print(f"⚠  Session agent {agent_id} no longer exists — creating a new one.")
        _clear_session()
        agent_id = None

    if agent_id:
        ok = _patch_agent(agent_id, combined, _DVS_PHONE_KNOWN)
        if not ok:
            print("✗ Patch failed — aborting.")
            sys.exit(1)
        print("  Waiting 5s for EL to propagate patch …")
        time.sleep(5)
    else:
        agent_id = _create_agent(combined, _DVS_PHONE_KNOWN)
        if not agent_id:
            sys.exit(1)
        _save_session(agent_id)
        print("  Waiting 3s for EL to initialise agent …")
        time.sleep(3)

    # ── Push tests ─────────────────────────────────────────────────────────────
    tests    = generate_tests()
    test_ids = []
    print(f"\nPushing {len(tests)} test(s) …")
    for t in tests:
        tid = _push_test(t)
        if tid:
            test_ids.append(tid)

    if not test_ids:
        print("✗ No tests pushed — aborting.")
        sys.exit(1)

    if not args.run:
        print(f"\n✓ {len(test_ids)} test(s) pushed.  Re-run with --run to execute.")
        sys.exit(0)

    # ── Dispatch ───────────────────────────────────────────────────────────────
    print(f"\nDispatching {len(test_ids)} test(s) against agent {agent_id} …")
    inv_id = _dispatch_tests(agent_id, test_ids)
    if not inv_id:
        sys.exit(1)

    # ── Poll ───────────────────────────────────────────────────────────────────
    print("\nPolling for results …")
    inv_data = _poll_invocation(inv_id)

    # ── Results ────────────────────────────────────────────────────────────────
    if inv_data is None:
        print("✗ No results received.")
        sys.exit(1)

    print(f"\n{'─' * 70}")
    failures = _print_results(inv_data, tests)
    print(f"\n{'─' * 70}")

    # Clean up test objects
    for tid in test_ids:
        _delete_test(tid)

    n_total = len(inv_data.get("test_runs", []))
    if failures == 0:
        print(f"✅ All {n_total} test(s) passed.")
        if not args.keep_agent:
            _delete_agent(agent_id)
            _clear_session()
        sys.exit(0)
    else:
        print(f"❌ {failures}/{n_total} test(s) FAILED — agent {agent_id} kept for inspection.")
        sys.exit(1)


if __name__ == "__main__":
    main()
