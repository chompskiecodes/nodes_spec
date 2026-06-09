#!/usr/bin/env python
"""
Totally Well — Node 8 Information Handler scaffold test.

Primary focus: does GPT-4.1 correctly handle massage availability queries
(multi-type lookup, synthesis, booking handoff)?

Usage:
  py -X utf8 test_node8_scaffold.py --run
  py -X utf8 test_node8_scaffold.py --spec-only
  py -X utf8 test_node8_scaffold.py --cleanup
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
import os as _os
# Add repo root to path so config.py is importable when script is run from anywhere
import sys as _sys
_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent)
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

try:
    import config as _cfg
    ELEVENLABS_API_KEY = _cfg.Settings().elevenlabs_api_key
except Exception:
    ELEVENLABS_API_KEY = _os.getenv("ELEVENLABS_API_KEY", "")

BASE_URL  = "https://api.elevenlabs.io/v1/convai"
CLINIC    = "Totally Well"
CLINIC_DIR = Path(__file__).parent

UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"
SMART_ROUTER_TOOL_ID     = "tool_4501k96qzckzemabz9rwppjms6zj"

SCAFFOLD_LLM       = "gpt-4.1"
POLL_INTERVAL_SECS = 12
POLL_TIMEOUT_SECS  = 360

_SESSION_FILE = CLINIC_DIR / "node8_scaffold_agent.json"

# ---------------------------------------------------------------------------
# Dynamic variable placeholders
# ---------------------------------------------------------------------------
_DYNAMIC_VAR_PLACEHOLDERS = {
    "called_number":           "+61756365028",
    "caller_id":               "0402841577",
    "system__called_number":   "+61756365028",
    "system__caller_id":       "0402841577",
    "system__conversation_id": "conv_test_scaffold",
    "caller_first_name":       "",
    "patient_name_raw":        "",
    "patient_status":          "",
    "appointment_type_id":     "",
    "appointment_type":        "",
    "booking_for":             "",
    "uni_router_intent":       "",
    "info_answered":           "",
    "implied_service":         "",
    "timeframe_raw":           "",
    "practitioner_preference": "",
    "preferred_gender":        "",
    "reschedule_mode":         "",
    "confirmed_location":      "",
    "return_node":             "",
    "pending_service":         "",
    # Node 8 specific
    "service_categories": (
        "Remedial Massage, Relaxation Massage, Clinical Lymphatic Drainage, "
        "Advanced Lymphatic Therapies, Lymphoedema & Lipoedema Management, "
        "Post Surgical Care, Naturopathy, Pregnancy, "
        "Fascia & Cellulite Treatments, Craniosacral Therapy, "
        "Sports & Deep Tissue Rehab"
    ),
    "location_addresses": (
        "Totally Well=Shop 4, 18 Robina Town Centre Drive, Robina QLD 4226"
    ),
    "practitioners_comma": (
        "Bartosz Kulikowski, Renee Fujimoto, Rosario Fernandez, "
        "Ruby De Paulo, Tanya Ly"
    ),
    "practitioner_services": (
        "Bartosz Kulikowski=Deep Tissue/Sports Massage & Rehab, "
        "Renee Fujimoto=Remedial Massage - Standard Appointment, "
        "Rosario Fernandez=Return Appointment _ Clinical Lymphatic Drainage, "
        "Ruby De Paulo=Remedial Massage - Standard Appointment, "
        "Tanya Ly=Return appointment - Advanced Lymphatic Drainage"
    ),
    "practitioner_genders": "",
    # massage_survey response field — starts empty; updated by backend when massage_survey handler runs
    "massage_survey_result": "",
    "service_ids": (
        "Deep Tissue Massage=1938457516237136921, "
        "Deep Tissue/Sports Massage & Rehab=1938451578646176789, "
        "Osteopathic Remedial Therapy=1750384331878049213, "
        "Remedial Massage - First Visit=1706185375103329858, "
        "Remedial Massage - Long appointment=1706185901446538819, "
        "Remedial Massage - Short appointment=1705809119534917124, "
        "Remedial Massage - Standard Appointment=1881819781372323677, "
        "Relaxation Massage - Long appointment=1706188927662040645, "
        "Relaxation Massage - Standard appointment=1706188520655169092, "
        "Initial Appointment _ Clinical Lymphatic Drainage=1706305781919393396, "
        "Return Appointment _ Clinical Lymphatic Drainage=1881249572026591023, "
        "Osteopathic Craniosacral Therapy=1633276199335634254, "
        "Initial appointment _ Post-Surgical Care=1822286589808616868, "
        "Return appointment _ Post-Surgical Care=1885192125738394731, "
        "Pregnancy Massage=1652172200255432409, "
        "Pregnancy Lymphatic Drainage=1719517364715792074, "
        "Express Naturopathy Appointment=1652118930304542420, "
        "Return Naturopathy Appointment=1633027083355563269"
    ),
}

P = f"[{CLINIC}]"


# ---------------------------------------------------------------------------
# Chat helpers
# ---------------------------------------------------------------------------
def _m(role: str, text: str, t: int = 0) -> Dict:
    # EL API requires "user" or "agent" (not "assistant")
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
    # Group M — Massage availability (primary focus)
    # These tests check whether GPT-4.1 handles massage availability queries
    # correctly despite the prompt's TOOL RESTRICTION on smart_voice_agent.
    # -----------------------------------------------------------------------

    # M1 — caller asks what massage is available today (general)
    tests.append({
        "name": f"{P} M1. General massage availability — what do you have today",
        "chat_history": [
            _m("user",
               "What kind of massage do you have available today? "
               "I'm free this morning.",
               3),
        ],
        "success_condition": (
            "Agent either (a) names the massage types the clinic offers and asks "
            "which the caller would prefer, without fabricating specific appointment times; "
            "or (b) routes back to the booking flow silently via universal_router "
            "intent='info_answered' so Node 3 can check real-time availability; "
            "or (c) calls universal_router intent='massage_survey' and then speaks a "
            "pre-composed availability summary from {{massage_survey_result}}. "
            "Agent does NOT state specific times (e.g. '10 AM', '3:40 PM') "
            "without first calling an availability tool and getting a result."
        ),
        "success_examples": [
            _ok("We offer Remedial, Relaxation, Deep Tissue, Lymphatic Drainage, "
                "and Craniosacral massage — which type were you thinking? "
                "Is there anything else I can help you with?"),
            _ok("[silent — calls universal_router intent='info_answered']"),
            _ok("[calls universal_router intent='massage_survey', then speaks massage_survey_result verbatim]"),
        ],
        "failure_examples": [
            _fail("We have availability at 9 AM and 11 AM this morning."),
            _fail("Deep tissue is available at 10 AM this morning with Bartosz."),
        ],
    })

    # M2 — caller names two specific types, asks about availability
    tests.append({
        "name": f"{P} M2. Two named types — deep tissue and craniosacral",
        "chat_history": [
            _m("user",
               "Do you have deep tissue massage and craniosacral therapy "
               "available this Saturday?",
               3),
        ],
        "success_condition": (
            "Agent routes to the booking flow by calling universal_router intent='info_answered' "
            "with implied_service set to one of the named services (Deep Tissue Massage or "
            "Craniosacral Therapy or a close variant). "
            "Agent does NOT say it cannot check availability or tell the caller to call the clinic. "
            "Agent does NOT fabricate specific appointment times without a tool call result. "
            "Tool call only — zero spoken output."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router intent='info_answered' "
                "implied_service='Deep Tissue Massage' timeframe_raw='this Saturday']"),
            _ok("[silent — calls universal_router intent='info_answered' "
                "implied_service='Osteopathic Craniosacral Therapy' timeframe_raw='this Saturday']"),
        ],
        "failure_examples": [
            _fail("I'm unable to check real-time availability from here."),
            _fail("Deep tissue is Saturday at 1:10 PM and 2:20 PM."),
            _fail("Both are available Saturday morning at 10 AM."),
        ],
    })

    # M3 — follow-up: one type unavailable, asks about another
    tests.append({
        "name": f"{P} M3. Follow-up — asks remedial after lymphatic unavailable",
        "chat_history": [
            _m("assistant",
               "There's no Clinical Lymphatic Drainage available this morning "
               "— the next slot is today at 3:40 PM with Rosario. "
               "Is there anything else I can help you with?",
               3),
            _m("user",
               "What about remedial massage? Anything this morning?",
               8),
        ],
        "success_condition": (
            "Agent looks up availability for Remedial Massage specifically "
            "and presents a real result from the tool call, "
            "OR routes to info_answered. "
            "Agent must NOT re-use the 3:40 PM Lymphatic Drainage time "
            "as if it applies to Remedial Massage."
        ),
        "success_examples": [
            _ok("The next available Remedial Massage is [day] with [name] at [time]. "
                "Is there anything else I can help you with?"),
            _ok("[silent — calls universal_router intent='info_answered']"),
        ],
        "failure_examples": [
            _fail("Remedial massage is also available at 3:40 PM today with Rosario."),
            _fail("I don't have that information — is there anything else I can help with?"),
        ],
    })

    # M4 — booking signal after agent presents availability results
    tests.append({
        "name": f"{P} M4. Book after availability — picks deep tissue",
        "chat_history": [
            _m("assistant",
               "Deep Tissue Massage is next available Saturday morning at 10 AM or 11 AM "
               "with Bartosz. Craniosacral Therapy is Saturday afternoon at 1:10 PM or "
               "2:20 PM with Tanya. Is there anything else I can help you with?",
               2),
            _m("user", "I'll book the deep tissue please.", 8),
        ],
        "success_condition": (
            "Agent calls universal_router intent='info_answered' and includes "
            "implied_service referencing deep tissue massage "
            "(e.g. 'Deep Tissue Massage' or 'Deep Tissue/Sports Massage & Rehab'). "
            "Tool call only — zero spoken output."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router intent='info_answered' "
                "implied_service='Deep Tissue Massage']"),
            _ok("[silent — calls universal_router intent='info_answered' "
                "implied_service='Deep Tissue/Sports Massage & Rehab']"),
        ],
        "failure_examples": [
            _fail("Great, I'll book that for you!"),
            _fail("[calls universal_router intent='confirm_service']"),
            _fail("[calls universal_router intent='info_answered' with no implied_service]"),
        ],
    })

    # M5 — caller says "any" after menu presented
    tests.append({
        "name": f"{P} M5. Any massage — whichever is soonest",
        "chat_history": [
            _m("assistant",
               "We offer Remedial, Relaxation, Deep Tissue, Lymphatic Drainage, "
               "and Craniosacral massage — which type were you thinking? "
               "Is there anything else I can help you with?",
               2),
            _m("user",
               "I don't really mind — whatever is available soonest.",
               7),
        ],
        "success_condition": (
            "Agent either (a) checks availability for multiple massage types and "
            "presents the soonest across them, "
            "or (b) routes to info_answered so the booking flow can run the search. "
            "Agent does NOT say 'I'm not able to check availability' "
            "or tell the caller to call the clinic."
        ),
        "success_examples": [
            _ok("[calls availability for multiple types and presents soonest]"),
            _ok("[silent — calls universal_router intent='info_answered']"),
        ],
        "failure_examples": [
            _fail("I'd recommend calling the clinic directly."),
            _fail("I'm unable to check real-time availability from here."),
            _fail("Could you narrow it down to one type?"),
        ],
    })

    # -----------------------------------------------------------------------
    # Group B — Booking signals (baseline)
    # -----------------------------------------------------------------------

    # B1 — explicit book intent after info answer
    tests.append({
        "name": f"{P} B1. Book intent after info answer",
        "chat_history": [
            _m("assistant",
               "Yes, Remedial Massage is available in 45, 60, and 90-minute sessions "
               "with Bartosz, Renee, Rosario, and Ruby. "
               "Is there anything else I can help you with?",
               2),
            _m("user", "I'd like to book please.", 7),
        ],
        "success_condition": (
            "Agent calls universal_router intent='info_answered'. "
            "Tool call only — zero spoken output."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router intent='info_answered']"),
        ],
        "failure_examples": [
            _fail("[calls universal_router intent='confirm_service']"),
            _fail("Great, let me book that for you — which practitioner?"),
        ],
    })

    # B2 — book with named practitioner (Tanya) — checks implied_service lookup from map
    # NOTE: prior agent turn deliberately does NOT name a specific service, so the agent
    # must derive implied_service from the practitioner-to-appointment_type map only.
    tests.append({
        "name": f"{P} B2. Book with Tanya — implied_service from practitioner map",
        "chat_history": [
            _m("assistant",
               "Tanya Ly is one of our specialist practitioners here. "
               "Is there anything else I can help you with?",
               2),
            _m("user", "Great, I'll book in with Tanya.", 7),
        ],
        "success_condition": (
            "Agent calls universal_router intent='info_answered' and includes "
            "practitioner_preference='Tanya Ly' AND implied_service drawn from the "
            "Tanya entry in the practitioner map "
            "('Return appointment - Advanced Lymphatic Drainage'). "
            "Tool call only — zero spoken output."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router intent='info_answered' "
                "practitioner_preference='Tanya Ly' "
                "implied_service='Return appointment - Advanced Lymphatic Drainage']"),
        ],
        "failure_examples": [
            _fail("[calls universal_router intent='info_answered' with no implied_service]"),
            _fail("[calls universal_router intent='info_answered' with implied_service='Craniosacral Therapy']"),
            _fail("Certainly — let me book that."),
        ],
    })

    # -----------------------------------------------------------------------
    # Group S — Blocking signals (baseline)
    # -----------------------------------------------------------------------

    tests.append({
        "name": f"{P} S1. Cancel existing appointment",
        "chat_history": [
            _m("user", "I need to cancel my appointment please.", 3),
        ],
        "success_condition": (
            "Agent calls universal_router intent='cancel_intent'. "
            "Tool call only — zero spoken output."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router intent='cancel_intent']"),
        ],
        "failure_examples": [
            _fail("[calls universal_router intent='info_answered']"),
            _fail("I can help with that — what day is your appointment?"),
        ],
    })

    tests.append({
        "name": f"{P} S2. Wrap-up on goodbye",
        "chat_history": [
            _m("assistant",
               "Deep tissue is next available Saturday at 10 AM. "
               "Is there anything else I can help you with?",
               2),
            _m("user", "No thanks, bye!", 6),
        ],
        "success_condition": (
            "Agent calls universal_router intent='wrap_up'. "
            "'bye' in the message triggers wrap_up even when 'no thanks' precedes it. "
            "Tool call only."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router intent='wrap_up']"),
        ],
        "failure_examples": [
            _fail("[calls universal_router intent='info_answered']"),
            _fail("Goodbye! Take care."),
        ],
    })

    # -----------------------------------------------------------------------
    # Group R — NO HANDLER (baseline)
    # -----------------------------------------------------------------------

    tests.append({
        "name": f"{P} R1. Done phrase — nothing else needed",
        "chat_history": [
            _m("assistant",
               "Totally Well is at Shop 4, 18 Robina Town Centre Drive, Robina. "
               "Is there anything else I can help you with?",
               2),
            _m("user", "No, that's all I needed, thank you.", 7),
        ],
        "success_condition": (
            "Agent calls universal_router intent='info_answered'. "
            "Tool call only — zero spoken output."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router intent='info_answered']"),
        ],
        "failure_examples": [
            _fail("Great, take care!"),
            _fail("[calls universal_router intent='wrap_up']"),
        ],
    })

    tests.append({
        "name": f"{P} R2. Done phrase — that answered my question",
        "chat_history": [
            _m("assistant",
               "Most services are eligible for private health insurance rebates "
               "through HICAPS. Is there anything else I can help you with?",
               2),
            _m("user", "Perfect, that answered my question.", 7),
        ],
        "success_condition": (
            "Agent calls universal_router intent='info_answered'. Tool call only."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router intent='info_answered']"),
        ],
        "failure_examples": [
            _fail("Glad I could help!"),
            _fail("[calls universal_router intent='wrap_up']"),
        ],
    })

    # -----------------------------------------------------------------------
    # Group I — Information questions (baseline)
    # -----------------------------------------------------------------------

    tests.append({
        "name": f"{P} I1. Open service question — what do you offer",
        "chat_history": [
            _m("user", "What kinds of services do you offer?", 3),
        ],
        "success_condition": (
            "Agent lists service_categories in one natural sentence — "
            "does NOT enumerate every appointment variant. "
            "Ends with 'Is there anything else I can help you with?'. "
            "No tool call."
        ),
        "success_examples": [
            _ok("We offer Remedial Massage, Relaxation Massage, Clinical Lymphatic "
                "Drainage, Craniosacral Therapy, and more. "
                "Is there anything else I can help you with?"),
        ],
        "failure_examples": [
            _fail("[calls any tool]"),
            _fail("I don't have that information."),
        ],
    })

    tests.append({
        "name": f"{P} I2. Condition question — back pain",
        "chat_history": [
            _m("user", "I've got back pain — can you help with that?", 3),
        ],
        "success_condition": (
            "Agent answers from the service descriptions, mentioning a relevant "
            "massage or treatment type for back pain (Remedial Massage, Deep Tissue, "
            "or similar). Ends with 'Is there anything else I can help you with?'. "
            "No tool call."
        ),
        "success_examples": [
            _ok("Yes, Remedial Massage is well suited for back pain — it targets "
                "muscle tension and pain. Is there anything else I can help you with?"),
        ],
        "failure_examples": [
            _fail("[calls any tool]"),
            _fail("That's outside what I can help with here."),
        ],
    })

    tests.append({
        "name": f"{P} I3. Health fund / HICAPS",
        "chat_history": [
            _m("user", "Do you take private health insurance?", 3),
        ],
        "success_condition": (
            "Agent says yes, most services are eligible through HICAPS, "
            "and notes that Sports & Deep Tissue services with Bartosz are "
            "not HICAPS-claimable. Ends with closing line. No tool call."
        ),
        "success_examples": [
            _ok("Yes, most services are eligible for private health insurance rebates "
                "through HICAPS. Note that Sports and Deep Tissue services with Bartosz "
                "are not HICAPS-claimable. Is there anything else I can help you with?"),
        ],
        "failure_examples": [
            _fail("[calls any tool]"),
            _fail("I don't have that information."),
        ],
    })

    return tests


# ---------------------------------------------------------------------------
# ElevenLabs API helpers
# ---------------------------------------------------------------------------
import requests  # noqa: E402  (imported here to keep top section clean)


def _hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def _load_prompt() -> str:
    f = CLINIC_DIR / "node_8_information_handler.txt"
    raw = f.read_text(encoding="utf-8-sig")
    marker = "Additional Prompt:"
    idx = raw.find(marker)
    if idx >= 0:
        return raw[idx + len(marker):].strip()
    for i, line in enumerate(raw.splitlines()):
        if line.startswith("##") or line.startswith("# MINI"):
            return "\n".join(raw.splitlines()[i:]).strip()
    return raw.strip()


def create_scaffold_agent(prompt: str) -> Optional[str]:
    payload = {
        "name": f"[Node8 Test] {CLINIC}",
        "conversation_config": {
            "agent": {
                "first_message": "Thanks for calling — how can I help you today?",
                "prompt": {
                    "prompt": prompt,
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
    """Returns {test_id -> test_name} map."""
    id_to_name: Dict[str, str] = {}
    for t in tests:
        payload = {
            "agent_id":          agent_id,
            "name":              t["name"],
            "type":              "llm",
            # success_condition + examples are TOP-LEVEL fields (not inside criteria)
            "success_condition": t["success_condition"],
            "success_examples":  t.get("success_examples", []),
            "failure_examples":  t.get("failure_examples", []),
            # chat_history is top-level (not inside a script wrapper)
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
    """Run all tests and poll for results.  Returns list of result dicts."""
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
        r = requests.get(
            f"{BASE_URL}/test-invocations/{suite_id}", headers=_hdrs()
        )
        if r.status_code != 200:
            print(f"  Poll error: {r.status_code}")
            continue
        data = r.json()
        runs = data.get("test_runs", [])
        pending = [
            x for x in runs
            if x.get("status") not in ("passed", "failed", "error")
        ]
        print(f"    … {len(pending)}/{len(runs)} still running")
        if not pending:
            # Annotate each run with its name from the id_to_name map
            # (match via test_id field on the run if available)
            for run in runs:
                tid = run.get("test_id") or run.get("test_run_id", "")
                run["_name"] = id_to_name.get(tid, run.get("name", tid))
            return runs
    print("  TIMEOUT")
    return []


def print_results(results: List[Dict]) -> None:
    passed = failed = error = 0
    for r in results:
        status  = r.get("status", "unknown")
        name    = r.get("_name") or r.get("name") or r.get("test_run_id", "?")
        # criteria results may live at result.criteria_results
        crit = (
            (r.get("result") or {}).get("criteria_results")
            or r.get("criteria_results")
            or []
        )
        verdict = (crit[0].get("result") or crit[0].get("condition_result", "")
                   ) if crit else ""
        if status == "passed":
            passed += 1
            print(f"  ✓ PASS  {name}")
        elif status == "failed":
            failed += 1
            print(f"  ✗ FAIL  {name}")
            if verdict:
                print(f"         {str(verdict)[:240]}")
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
    ap = argparse.ArgumentParser(
        description=f"Node 8 scaffold tests — {CLINIC}"
    )
    ap.add_argument("--run",        action="store_true",
                    help="Create/patch agent, push tests, run them")
    ap.add_argument("--create",     action="store_true",
                    help="Force create a new scaffold agent (deletes existing)")
    ap.add_argument("--cleanup",    action="store_true",
                    help="Delete the session agent and exit")
    ap.add_argument("--spec-only",  action="store_true",
                    help="Print test names without running")
    ap.add_argument("--keep-agent", action="store_true",
                    help="Don't delete scaffold agent after run")
    ap.add_argument("--agent-id",   help="Use this agent ID instead of session file")
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
