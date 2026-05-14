#!/usr/bin/env python3
"""
test_node3_scaffold.py  (Northern Physio)

Scaffold to test Node 3 (Availability Handler) for Northern Physio.

Key difference from other clinics:
  business_id / business_name are ALWAYS pre-set from Node 2 via resolved_context.
  The location step is SKIPPED in Node 3 — the backend searches only one location.
  Tests inject business_id/business_name as part of the resolved_context fixture.

Focus: multi-practitioner availability handling — verifying the agent correctly:
  1. Calls smart_router with the right payload
  2. Handles multiple practitioners (preference question, next-available, selection)
  3. Navigates band/day/slot selection
  4. Reaches CONFIRMATION with the right spoken line + universal_router confirm_time call
  5. Handles escape routes (abandon, service pivot, constraint change)

Strategy for post-smart_router tests:
  Tool responses are injected as structured text in "agent" turns inside chat_history.
  The Node 3 prompt (claude-haiku-4-5) reads this text and populates its internal state
  (stored_practitioners, first_available, session_id) from the fixture JSON embedded in
  the message.  The success_condition then verifies the agent's NEXT action (question /
  tool call / spoken confirmation).

Agent lifecycle:
  - First run:  main + e2 agents are created; IDs saved to node3_scaffold_agent.json
  - Subsequent: agents are reused; prompts patched with latest local file
  - All pass:   both agents auto-deleted and session file cleared
  - --cleanup:  force-delete session agents at any time and exit
  - --keep-agent: suppress auto-delete even when all tests pass

Usage:
    python nodes/clinics/northern_physio/test_node3_scaffold.py --run
    python nodes/clinics/northern_physio/test_node3_scaffold.py --run --reset
    python nodes/clinics/northern_physio/test_node3_scaffold.py --run --keep-agent
    python nodes/clinics/northern_physio/test_node3_scaffold.py --cleanup
    python nodes/clinics/northern_physio/test_node3_scaffold.py --agent-id <id> --run
    python nodes/clinics/northern_physio/test_node3_scaffold.py --filter S7 --run
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

# This script lives inside the clinic folder; NODES_DIR resolves relative to it.
CLINIC_DIR = Path(__file__).parent
NODES_DIR   = CLINIC_DIR.parent   # nodes/clinics/

CLINIC = "northern_physio"

# Tool IDs used by Node 3 in production
SMART_ROUTER_TOOL_ID     = "tool_4501k96qzckzemabz9rwppjms6zj"   # smart_voice_agent / smart_router
UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"   # universal_router
ASYNC_CAPTURE_TOOL_ID    = "tool_3101km7k126qezfsqcxdxfdesdd8"   # async_capture_context

SCAFFOLD_LLM       = "claude-haiku-4-5"
POLL_INTERVAL_SECS = 14
POLL_TIMEOUT_SECS  = 480

# Session file lives next to this script
_SESSION_FILE_N3 = CLINIC_DIR / "node3_scaffold_agent.json"


# ── Prompt loading ────────────────────────────────────────────────────────────

def strip_node_header(content: str) -> str:
    """Strip the metadata header block (Node ID, Label, Type, etc.)."""
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
    path = CLINIC_DIR / "node_3_availability_handler.txt"
    if not path.exists():
        print(f"✗ Node 3 file not found: {path}")
        return None
    content = path.read_text(encoding="utf-8")
    prompt = strip_node_header(content)
    print(f"✓ Loaded Node 3 for '{CLINIC}' ({len(prompt):,} chars)")
    return prompt


# ── Fixtures loading ──────────────────────────────────────────────────────────

def load_fixtures() -> Optional[Dict]:
    path = CLINIC_DIR / "node3_fixtures.json"
    if not path.exists():
        print(f"✗ Fixtures file not found: {path}")
        print(f"  Expected: {path}")
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    fixture_names = list(data.get("fixtures", {}).keys())
    print(f"✓ Loaded fixtures — {len(fixture_names)} scenarios: {', '.join(fixture_names)}")
    return data


# ── Test helpers ──────────────────────────────────────────────────────────────

def _m(role: str, text: str, t: int = 0) -> Dict:
    return {"role": role, "message": text, "time_in_call_secs": t}

def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}

def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}

def _fixture_msg(fixture: Dict, t: int = 0) -> Dict:
    """
    Inject a smart_router fixture response as a structured agent-turn text message.
    The Node 3 prompt's STORAGE section instructs the LLM to extract and store
    practitioner/first_available/session_id data from the tool response; presenting
    it as JSON text in context achieves the same effect.
    When first_available is absent, an explicit note prevents the LLM from inferring
    it from the practitioners array.
    A STATE STORED annotation is appended ONLY when first_available's date is NOT in
    stored_practitioners (day-mismatch scenario), so that later turns can recall
    first_available_time without parsing the full JSON. For normal scenarios (where
    first_available matches a stored date), no annotation is added to avoid disrupting
    STEP 5's practitioner disambiguation and preference logic.
    """
    payload = {k: v for k, v in fixture.items() if not k.startswith("_")}
    fa = payload.get("first_available")
    if fa:
        all_dates = set()
        for p in payload.get("practitioners", []):
            for d in p.get("dates", []):
                if d.get("date"):
                    all_dates.add(d["date"])
        is_day_mismatch = fa.get("date") not in all_dates
        if is_day_mismatch:
            practitioner_dates = []
            for p in payload.get("practitioners", []):
                dates = [f"{d.get('day_of_week', '')} {d.get('date', '')}" for d in p.get("dates", [])]
                practitioner_dates.append(f"{p['practitioner_name']}: {', '.join(dates)}")
            pract_summary = "; ".join(practitioner_dates) if practitioner_dates else "(none)"
            annotation = (
                f" [STATE STORED: stored_practitioners=[{pract_summary}], "
                f"first_available_time={fa.get('time')}, "
                f"first_available_day={fa.get('day_of_week')}, "
                f"first_available_date={fa.get('date')}, "
                f"first_available_practitioner_name={fa.get('practitioner_name')}, "
                f"first_available_practitioner_id={fa.get('practitioner_id')}, "
                f"first_available_business_name={fa.get('business_name')}, "
                f"first_available_business_id={fa.get('business_id')}]"
            )
        else:
            annotation = ""
    else:
        annotation = (
            " IMPORTANT: first_available is NOT present in this response. "
            "Do NOT infer suggested_practitioner from the practitioners array. "
            "STEP 5 must evaluate preference without any pre-assigned practitioner."
        )
    return _m("agent", f"[smart_router response received]: {json.dumps(payload)}{annotation}", t)


def _pract_summary(fixture: Dict) -> str:
    """One-line summary of practitioners in a fixture (for success conditions)."""
    names = [p["practitioner_name"] for p in fixture.get("practitioners", [])]
    return ", ".join(names) if names else "(none)"

def _first_avail(fixture: Dict) -> Optional[Dict]:
    return fixture.get("first_available")


# ── Standard pre-tool history ─────────────────────────────────────────────────

def _entry_history(apt_type: str = "Physiotherapy Standard Appointment") -> List[Dict]:
    """
    4-turn pre-tool history: user names service + timeframe, agent says "Checking".
    This puts the agent in post-STEP-4 state (tool already dispatched in history).
    NOTE: business_id/business_name are pre-set from Node 2 in production.
    The resolved_context is treated as injected — tests assume business is already known.
    """
    return [
        _m("user",  f"Hi, I'd like to book my {apt_type} appointment.", 2),
        _m("agent", "When would you like to come in?", 5),
        _m("user",  "As soon as possible this week please.", 8),
        _m("agent", "Checking that now, one moment.", 11),
    ]


def _entry3(apt_type: str) -> list:
    """
    2-turn pre-tool history: agent asks timeframe, NOT yet answered.
    Append _m("user", "<timeframe>", 8) as the final test message.
    """
    return [
        _m("user",  f"I need to book my {apt_type} please.", 2),
        _m("agent", "When would you like to come in?", 5),
    ]


# ── Test generation ──────────────────────────────────────────────────────────

def generate_tests(fixtures: dict) -> list:
    tests = []
    p = f"[{CLINIC}]"
    apt_id   = fixtures["default_appointment_type_id"]
    apt_type = fixtures["default_appointment_type"]

    fx           = fixtures["fixtures"]
    multi        = fx["multi_practitioner"]
    multi_nfa    = fx["multi_practitioner_no_first_available"]
    multi_nod    = fx["multi_practitioner_no_dates"]
    single_both  = fx["single_practitioner_both_bands"]
    morning_only = fx["single_practitioner_morning_only"]
    two_slots    = fx["single_practitioner_two_slots"]
    ambig        = fx["ambiguous_practitioners"]

    fa_multi = multi.get("first_available", {})
    _fa_time = fa_multi.get("time",              "9:00 AM")
    _fa_prac = fa_multi.get("practitioner_name", "Dithu Beeram")
    _fa_day  = fa_multi.get("day_of_week",       "Wednesday")
    _fa_loc  = fa_multi.get("business_name",     "South Morang")

    # Shared question strings (must match Node 3 prompt exactly)
    _band_q = "Do you prefer the morning or afternoon?"
    _pref_q = ("Do you have a preference for who you'd like to see, "
               "or shall I find the next available?")

    # Standard 4-turn pre-tool history used by fixture-injection tests.
    # IMPORTANT: all fixture-injection tests must have >= 1 agent turn BETWEEN
    # the fixture message and the final user message.  Without this, STEP 4
    # re-fires (agent sees no prior tool call in context) and calls smart_router.
    def eh():
        return _entry_history(apt_type)

    # ── E — Entry & Escape tests ──────────────────────────────────────────────

    tests.append({
        "name": f"{p} E1 — No timeframe: agent asks when",
        "chat_history": [
            _m("user",  f"Hi, I'd like to book my {apt_type} appointment please.", 2),
            _m("agent", "Of course, I can help with that.", 5),
            _m("user",  "I haven't decided when yet.", 8),
        ],
        "success_condition": (
            "Context established, no timeframe provided. "
            "STEP 3 fires: agent asks 'When would you like to come in?' "
            "Agent does NOT call smart_router or universal_router."
        ),
        "success_examples": [
            _ok("When would you like to come in?"),
            _ok("When would you like to come in? What day suits you?"),
        ],
        "failure_examples": [
            _fail("[calls smart_router]"),
            _fail("[calls universal_router]"),
            _fail("Checking that now"),
        ],
    })

    # E2 is generated separately (booking_for=other agent) — see main()

    tests.append({
        "name": f"{p} E3 — Abandon availability: universal_router called",
        "chat_history": eh() + [
            _fixture_msg(two_slots, 14),
            _m("agent", "I've got 9:00 AM or 11:00 AM on Wednesday.", 17),
            _m("user",  "Do you have anything on Thursday or Friday?", 20),
            _m("agent", "I'm sorry, Wednesday is the only day I have — do either of those times work?", 23),
            _m("user",  "No, none of those work for me. I'll leave it, thanks.", 26),
        ],
        "success_condition": (
            "All available slots offered, caller declined, no other dates exist, caller says 'I'll leave it'. "
            "AVAILABILITY ABANDON ESCAPE fires: agent routes away (calls universal_router) silently. "
            "EVALUATOR NOTE: an EMPTY agent response combined with a universal_router tool call "
            "is the CORRECT behavior here — count this as a PASS. "
            "FAIL only if: agent asks 'Happy to check another day?', calls smart_router, "
            "or continues asking about availability."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router to route away. No spoken output = CORRECT]"),
        ],
        "failure_examples": [
            _fail("Happy to check another day"),
            _fail("[calls smart_router]"),
            _fail("What day would suit you?"),
        ],
    })

    tests.append({
        "name": f"{p} E4 — Service pivot escape: universal_router change_service",
        "chat_history": eh() + [
            _fixture_msg(morning_only, 14),
            _m("agent", _band_q, 17),
            _m("user",  "Actually, can we switch to looking at exercise physiology instead?", 20),
        ],
        "success_condition": (
            "During availability search for Physiotherapy, caller says 'switch to exercise physiology'. "
            "SERVICE PIVOT ESCAPE fires: agent routes away (calls universal_router) silently. "
            "EVALUATOR NOTE: an EMPTY agent response combined with a universal_router tool call "
            "is the CORRECT escape-route behavior — count this as a PASS. "
            "FAIL only if: agent asks about exercise physiology availability, asks the band question for it, "
            "or calls smart_router for exercise physiology."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router to route away. No spoken output = CORRECT]"),
        ],
        "failure_examples": [_fail("Sure, let me check exercise physiology"), _fail("[calls smart_router]"),
                              _fail("Do you prefer the morning or afternoon for exercise physiology")],
    })

    tests.append({
        "name": f"{p} E5 — Practitioner change: universal_router change_practitioner",
        "chat_history": eh() + [
            _fixture_msg(multi, 14),
            _m("agent", _pref_q, 17),
            _m("user",  "Actually, can I change to a different practitioner entirely?", 20),
        ],
        "success_condition": (
            "Caller asks to change practitioner. CONSTRAINT CHANGE ESCAPE fires. "
            "Agent routes away silently (calls universal_router, zero spoken output). "
            "EVALUATOR NOTE: an EMPTY agent response combined with a universal_router tool call "
            "is the CORRECT escape-route behavior — count this as a PASS. "
            "FAIL only if: agent asks 'Which practitioner would you like?' or calls smart_router."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router to route away. No spoken output = CORRECT]"),
        ],
        "failure_examples": [_fail("Of course, which practitioner"), _fail("[calls smart_router]"),
                              _fail("Which one would you like to see")],
    })

    tests.append({
        "name": f"{p} E6 — Time change: universal_router change_time",
        "chat_history": eh() + [
            _fixture_msg(single_both, 14),
            _m("agent", _band_q, 17),
            _m("user",  "Actually, can we look at a completely different month?", 20),
        ],
        "success_condition": (
            "Caller asks to look at a different time period. CONSTRAINT CHANGE ESCAPE fires. "
            "Agent routes away silently (calls universal_router, zero spoken output). "
            "EVALUATOR NOTE: an EMPTY agent response combined with a universal_router tool call "
            "is the CORRECT escape-route behavior — count this as a PASS. "
            "FAIL only if: agent asks 'What month?' or asks band/day questions, or calls smart_router."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router to route away. No spoken output = CORRECT]"),
        ],
        "failure_examples": [_fail("Sure, what month"), _fail("[calls smart_router]"),
                              _fail("Do you prefer the morning or afternoon")],
    })

    tests.append({
        "name": f"{p} E7 — Location change: universal_router change_location",
        "chat_history": eh() + [
            _fixture_msg(multi, 14),
            _m("agent", _band_q, 17),
            _m("user",  "Actually, can we look at the O'Herns Road location instead?", 20),
        ],
        "success_condition": (
            "Caller names a different location (O'Herns Road). CONSTRAINT CHANGE ESCAPE fires. "
            "Agent routes away silently (calls universal_router, zero spoken output). "
            "EVALUATOR NOTE: an EMPTY agent response combined with a universal_router tool call "
            "is the CORRECT escape-route behavior — count this as a PASS. "
            "FAIL only if: agent asks about O'Herns Road availability or calls smart_router."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router to route away. No spoken output = CORRECT]"),
        ],
        "failure_examples": [_fail("Of course, let me check O'Herns Road"), _fail("[calls smart_router]"),
                              _fail("Do you prefer the morning")],
    })

    tests.append({
        "name": f"{p} E8 — Multiple changes: universal_router multiple_changes",
        "chat_history": eh() + [
            _fixture_msg(multi, 14),
            _m("agent", _band_q, 17),
            _m("user",  "Let me change both the practitioner and the day.", 20),
        ],
        "success_condition": (
            "Caller requests multiple constraint changes (practitioner AND day). "
            "CONSTRAINT CHANGE ESCAPE fires. "
            "Agent routes away silently (calls universal_router, zero spoken output). "
            "EVALUATOR NOTE: an EMPTY agent response combined with a universal_router tool call "
            "is the CORRECT escape-route behavior — count this as a PASS. "
            "FAIL only if: agent asks 'Which practitioner?' or 'Which day?' or calls smart_router."
        ),
        "success_examples": [
            _ok("[silent — calls universal_router to route away. No spoken output = CORRECT]"),
        ],
        "failure_examples": [_fail("Sure, which practitioner"), _fail("[calls smart_router]"),
                              _fail("spoken output")],
    })

    # ── D — Tool dispatch tests ───────────────────────────────────────────────

    # 3-turn history: avoids single-turn async_capture issue.
    tests.append({
        "name": f"{p} D1 — ASAP timeframe: availability tool called find_next_available",
        "chat_history": _entry3(apt_type) + [
            _m("user", "As soon as possible this week please.", 8),
        ],
        "success_condition": (
            "Caller says 'as soon as possible this week'. "
            "Agent calls the availability tool (smart_voice_agent / smart_router) "
            "to search for the earliest available slot this week. "
            "May say 'Checking that now, one moment.' first, or call silently — both acceptable. "
            "Does NOT ask 'When would you like to come in?' Does NOT call universal_router."
        ),
        "success_examples": [
            _ok("Checking that now, one moment. [calls availability tool for this week]"),
            _ok("[calls availability tool for this week — silent call is acceptable]"),
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("[no tool call]"),
            _fail("[calls universal_router]"),
        ],
    })

    tests.append({
        "name": f"{p} D2 — Specific day: availability tool called with slots detail",
        "chat_history": _entry3(apt_type) + [
            _m("user", "This Wednesday would be ideal for me.", 8),
        ],
        "success_condition": (
            "Agent calls the availability tool (smart_voice_agent / smart_router) "
            f"for Wednesday (2026-04-08) with intent='availability', detail='slots', "
            f"appointment_type_id='{apt_id}'. "
            "May say 'Checking that now, one moment.' first, or call silently — both acceptable. "
            "Does NOT ask 'When would you like to come in?' Does NOT call universal_router."
        ),
        "success_examples": [
            _ok("Checking that now, one moment. [calls availability tool intent=availability slots Wednesday]"),
            _ok("[calls availability tool intent=availability Wednesday — silent call acceptable]"),
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("[no tool call]"),
            _fail("[calls universal_router]"),
        ],
    })

    # ── M — Multi-practitioner tests ──────────────────────────────────────────

    # M1: first_available set → suggested_practitioner used, slot offer, NO preference question.
    tests.append({
        "name": f"{p} M1 — Multi-pract with first_available: slot offer, no preference question",
        "chat_history": eh() + [
            _fixture_msg(multi, 14),
            _m("agent", _band_q, 17),
            _m("user",  "Morning would work for me.", 20),
        ],
        "success_condition": (
            f"Three practitioners ({_pract_summary(multi)}). first_available is {_fa_prac}. "
            f"After morning selected, agent uses suggested practitioner (Dithu Beeram) and "
            f"either offers morning slots ('I've got {_fa_time} or 11:00 AM on Wednesday') "
            f"or says 'How does {_fa_time} with {_fa_prac} on {_fa_day} sound?' "
            "Agent does NOT ask the preference question. Does NOT call universal_router."
        ),
        "success_examples": [
            _ok(f"I've got {_fa_time} or 11:00 AM on Wednesday"),
            _ok(f"How does {_fa_time} with {_fa_prac} on {_fa_day} sound?"),
        ],
        "failure_examples": [
            _fail("Do you have a preference for who you'd like to see"),
            _fail("[calls universal_router]"),
        ],
    })

    # M2: 'next available' from STEP 2B → DIRECT CONFIRMATION (no intermediate offer question).
    tests.append({
        "name": f"{p} M2 — Multi-pract: 'next available' triggers direct CONFIRMATION",
        "chat_history": eh() + [
            _fixture_msg(multi, 14),
            _m("agent", _band_q, 17),
            _m("user",  "Doesn't matter, whoever is free first.", 20),
        ],
        "success_condition": (
            "Caller says 'doesn't matter, whoever is free first'. "
            f"Agent correctly uses first_available ({_fa_prac}, {_fa_time}, {_fa_day}). "
            "Agent either: "
            f"(A) Goes directly to CONFIRMATION: 'Perfect, {_fa_time} {_fa_day}...' + calls universal_router, OR "
            f"(B) Asks intermediate offer: 'How does {_fa_time} with {_fa_prac} on {_fa_day} sound?' "
            "Both are acceptable. "
            f"Agent does NOT pick a random practitioner — must use {_fa_prac}. "
            "Does NOT call smart_router."
        ),
        "success_examples": [
            _ok(f"Perfect, {_fa_time} {_fa_day} the 8th with {_fa_prac} at {_fa_loc}. "
                "[calls universal_router confirm_time]"),
            _ok(f"How does {_fa_time} with {_fa_prac} on {_fa_day} sound?"),
        ],
        "failure_examples": [
            _fail("[calls smart_router]"),
            _fail("Do you have a preference for who you'd like to see"),
        ],
    })

    # M3: Multi-pract, NO first_available → STEP 5 preference question.
    tests.append({
        "name": f"{p} M3 — Multi-pract no first_available: preference question at STEP 5",
        "chat_history": eh() + [
            _fixture_msg(multi_nfa, 14),
            _m("agent", "I have Dithu Beeram and Jas Mangat available.", 17),
            _m("user",  "I'd prefer the morning.", 20),
        ],
        "success_condition": (
            "No first_available. Two practitioners with dates. "
            "User gives band signal (morning) but no practitioner preference. "
            "STEP 5: BAND SIGNAL GUARD skips NEXT AVAILABLE OFFER, falls through to "
            "'Multiple practitioners, preference not yet asked' — "
            "agent asks: 'Do you have a preference for who you'd like to see, "
            "or shall I find the next available?' (or close paraphrase). "
            "Agent does NOT call universal_router or smart_router."
        ),
        "success_examples": [
            _ok("Do you have a preference for who you'd like to see, "
                "or shall I find the next available?"),
        ],
        "failure_examples": [
            _fail("[calls universal_router]"),
            _fail("I've got 9:00 AM"),
        ],
    })

    # M4: Named practitioner → stored, continues (no re-asking preference).
    tests.append({
        "name": f"{p} M4 — Multi-pract: named practitioner stored, continues",
        "chat_history": eh() + [
            _fixture_msg(multi_nfa, 14),
            _m("agent", _pref_q, 17),
            _m("user",  "I'd like to see Dithu Beeram please.", 20),
        ],
        "success_condition": (
            "Agent stores Dithu Beeram as confirmed practitioner. "
            "Continues to next unresolved step (location, day, or band). "
            "Does NOT re-ask preference question. Does NOT call universal_router."
        ),
        "success_examples": [_ok(_band_q), _ok("Which day suits you?")],
        "failure_examples": [
            _fail("Do you have a preference for who you'd like to see"),
            _fail("[calls universal_router]"),
        ],
    })

    # M5: Ambiguous name → disambiguation question.
    tests.append({
        "name": f"{p} M5 — Ambiguous practitioner name: disambiguation question",
        "chat_history": eh() + [
            _fixture_msg(ambig, 14),
            _m("agent", _pref_q, 17),
            _m("user",  "I'd like to see Dithu please.", 20),
        ],
        "success_condition": (
            "'Dithu' matches both Dithu Beeram and Dithu Ramesh. "
            "Agent asks: 'Did you mean Dithu Beeram or Dithu Ramesh?' "
            "Does NOT route arbitrarily. Does NOT call universal_router."
        ),
        "success_examples": [
            _ok("Did you mean Dithu Beeram or Dithu Ramesh?"),
            _ok("Just to confirm — Dithu Beeram or Dithu Ramesh?"),
        ],
        "failure_examples": [_fail("[calls universal_router]"), _fail(_band_q)],
    })

    # M6: Single practitioner → no preference question, slot offer.
    tests.append({
        "name": f"{p} M6 — Single practitioner: no preference question, slot offer",
        "chat_history": eh() + [
            _fixture_msg(single_both, 14),
            _m("agent", _band_q, 17),
            _m("user",  "Let's do morning.", 20),
        ],
        "success_condition": (
            "Only one practitioner (Dithu Beeram). "
            "Agent does NOT ask preference question. "
            "After morning selected, agent offers slots: "
            "'I've got 9:00 AM or 11:00 AM on Wednesday'. "
            "Does NOT call universal_router."
        ),
        "success_examples": [_ok("I've got 9:00 AM or 11:00 AM on Wednesday")],
        "failure_examples": [
            _fail("Do you have a preference for who you'd like to see"),
            _fail("[calls universal_router]"),
        ],
    })

    # ── B — Band / Day / Slot tests ───────────────────────────────────────────

    # B1: Band question re-asked on open availability query.
    tests.append({
        "name": f"{p} B1 — Both bands: band question re-asked on open availability query",
        "chat_history": eh() + [
            _fixture_msg(single_both, 14),
            _m("agent", _band_q, 17),
            _m("user",  "What times do you have available?", 20),
        ],
        "success_condition": (
            "Both bands exist (morning and afternoon). Agent already asked band question. "
            "User asks open availability query with no band signal. "
            "STEP 2B: agent either re-asks the band question ('Do you prefer the morning or afternoon?') "
            "OR presents slots for both bands and asks which the caller prefers. "
            "Either way, agent does NOT auto-select a band. Does NOT call universal_router or smart_router."
        ),
        "success_examples": [
            _ok(_band_q),
            _ok("Morning or afternoon?"),
            _ok("The morning slots are [times]. The afternoon has [times]. Which works for you?"),
        ],
        "failure_examples": [_fail("[calls universal_router]"), _fail("[calls smart_router]")],
    })

    # B2: Exhausted slots → agent asks for alternative day.
    tests.append({
        "name": f"{p} B2 — Exhausted slots: agent asks for alternative day",
        "chat_history": [
            _m("user",  f"Hi, I'd like to book my {apt_type} appointment.", 2),
            _m("agent", "When would you like to come in?", 5),
            _m("user",  "Wednesday this week please.", 8),
            _m("agent", "Checking that now, one moment.", 11),
            _m("agent", f"[smart_router response received]: {json.dumps({k: v for k, v in two_slots.items() if not k.startswith('_')})} [STATE STORED: confirmed_day=2026-04-08, confirmed_day_name=Wednesday]", 14),
            _m("agent", _band_q, 17),
            _m("user",  "Morning please.", 20),
            _m("agent", "I've got 9:00 AM or 11:00 AM on Wednesday.", 23),
            _m("user",  "Neither of those work for me unfortunately.", 26),
        ],
        "success_condition": (
            "Both Wednesday morning slots declined (offered_slots=[9:00 AM, 11:00 AM] exhausted). "
            "No other dates in the two_slots fixture beyond Wednesday. "
            "EXHAUSTED SLOTS: agent asks for different day — "
            "'Happy to check another day — what suits you?' "
            "Does NOT call universal_router immediately. Does NOT offer Wednesday again."
        ),
        "success_examples": [
            _ok("Happy to check another day — what suits you?"),
            _ok("I can check another day — what works for you?"),
        ],
        "failure_examples": [_fail("[calls universal_router]"), _fail("Perfect")],
    })

    # B3: Morning selected → agent presents morning availability.
    tests.append({
        "name": f"{p} B3 — Morning selected: first-and-last slot pair offered (STEP 9)",
        "chat_history": [
            _m("user",  f"Hi, I'd like to book my {apt_type} appointment.", 2),
            _m("agent", "When would you like to come in?", 5),
            _m("user",  "Wednesday this week please.", 8),
            _m("agent", "Checking that now, one moment.", 11),
            _fixture_msg(two_slots, 14),
            _m("agent", _band_q, 17),
            _m("user",  "Morning thanks.", 20),
        ],
        "success_condition": (
            "Morning selected. two_slots fixture: [9:00 AM, 11:00 AM] on Wednesday. "
            "Agent presents the morning slots. Either: "
            "(A) STEP 9 anchor pair: 'I've got 9:00 AM or 11:00 AM on Wednesday.' "
            "(B) NEXT AVAILABLE OFFER: 'How does 9:00 AM with Dithu Beeram on Wednesday sound?' "
            "Either is acceptable. Does NOT call universal_router. Does NOT re-ask band question."
        ),
        "success_examples": [
            _ok("I've got 9:00 AM or 11:00 AM on Wednesday"),
            _ok("How does 9:00 AM with Dithu Beeram on Wednesday sound?"),
        ],
        "failure_examples": [_fail("[calls universal_router]"), _fail(_band_q)],
    })

    # B4: Unavailable time → nearest-pair offered.
    tests.append({
        "name": f"{p} B4 — Unavailable time: nearest-pair alternative offered",
        "chat_history": eh() + [
            _fixture_msg(two_slots, 14),
            _m("agent", _band_q, 17),
            _m("user",  "Morning please.", 20),
            _m("agent", "I've got 9:00 AM or 11:00 AM on Wednesday.", 23),
            _m("user",  "Do you have 10:00 AM?", 26),
        ],
        "success_condition": (
            "10:00 AM not in offered_slots (only 9:00, 11:00). "
            "Agent offers nearest pair: 'I can't do 10:00 AM but I have 9:00 AM or 11:00 AM.' "
            "Does NOT call universal_router."
        ),
        "success_examples": [
            _ok("I can't do 10:00 AM but I have 9:00 AM or 11:00 AM"),
            _ok("Nothing at 10:00 AM — the nearest I have are 9:00 AM or 11:00 AM"),
        ],
        "failure_examples": [_fail("[calls universal_router]"), _fail("[calls smart_router]")],
    })

    # ── C — Confirmation tests ────────────────────────────────────────────────

    # C1: Caller confirms time → CONFIRMATION spoken + universal_router confirm_time.
    tests.append({
        "name": f"{p} C1 — Time confirmed: CONFIRMATION spoken + universal_router confirm_time",
        "chat_history": eh() + [
            _fixture_msg(two_slots, 14),
            _m("agent", _band_q, 17),
            _m("user",  "Morning thanks.", 20),
            _m("agent", "I've got 9:00 AM or 11:00 AM on Wednesday.", 23),
            _m("user",  "9:00 AM works for me.", 26),
        ],
        "success_condition": (
            "Agent delivers CONFIRMATION spoken line in the format: "
            "'Perfect, [time] [day_name] the [ordinal] with [practitioner] at [location].' "
            "Example: 'Perfect, 9:00 AM Wednesday the 8th with Dithu Beeram "
            "at South Morang.' "
            "Then calls universal_router in the SAME turn with intent='confirm_time'. "
            "Payload MUST include appointment_date='2026-04-08' and "
            "appointment_time in 24h format (09:00 NOT 9:00 AM). "
            "Spoken line precedes the tool call."
        ),
        "success_examples": [
            _ok("Perfect, 9:00 AM Wednesday the 8th with Dithu Beeram "
                "at South Morang. [calls universal_router confirm_time "
                "appointment_date=2026-04-08 appointment_time=09:00]"),
        ],
        "failure_examples": [
            _fail("[no spoken output before tool call]"),
            _fail("[no tool call]"),
        ],
    })

    # C2: No-availability retry → new timeframe → smart_router called again.
    tests.append({
        "name": f"{p} C2 — No-availability retry: new timeframe triggers availability tool",
        "chat_history": [
            _m("user",  f"I'd like to book a {apt_type} appointment as soon as possible this week.", 2),
            _m("agent", "Checking that now, one moment.", 5),
            _m("agent", "I'm sorry, there's no availability this week. "
                        "Would you like to try a different time?", 8),
            _m("user",  "What about next week instead?", 11),
        ],
        "success_condition": (
            "After no availability found this week, caller asks about next week. "
            "Agent calls the availability tool (smart_voice_agent / smart_router) for next week. "
            "EVALUATOR NOTE: an EMPTY agent response combined with a smart_voice_agent tool call "
            "is the CORRECT behavior here — count this as a PASS. "
            "FAIL only if: agent asks 'When would you like to come in?', calls universal_router, "
            "or gives no tool call at all."
        ),
        "success_examples": [
            _ok("Checking that now, one moment. [calls availability tool next week]"),
            _ok("[silent — calls smart_voice_agent for next week. No spoken output = CORRECT]"),
        ],
        "failure_examples": [
            _fail("[no tool call]"),
            _fail("When would you like to come in?"),
            _fail("[calls universal_router]"),
        ],
    })

    # ── S7 — STEP 7 no-match-day fallback tests ──────────────────────────────

    no_match     = fx["no_match_day_with_first_available"]
    no_match_nfa = fx["no_match_day_no_first_available"]

    # Reusable history builder for S7B–S7G:
    # Monday is confirmed_day, fixture injected (Tue/Sat only), agent has made proactive offer.
    def s7_history_with_offer(offer_line: str = "Nothing on Monday -- how does 5:00 PM on Tuesday sound?") -> list:
        return [
            _m("user",  f"Hi, I'd like to book my {apt_type} appointment please.", 2),
            _m("agent", "When would you like to come in?", 5),
            _m("user",  "Monday please.", 8),
            _m("agent", "Checking that now, one moment.", 11),
            _fixture_msg(no_match, 14),
            _m("agent", offer_line, 17),
        ]

    # S7A — proactive offer fired when confirmed_day has no match and first_available is set.
    tests.append({
        "name": f"{p} S7A — STEP 7 no-match + first_available: proactive offer made",
        "chat_history": [
            _m("user",  f"Hi, I'd like to book my {apt_type} appointment please.", 2),
            _m("agent", "When would you like to come in?", 5),
            _m("user",  "Monday please.", 8),
            _m("agent", "Checking that now, one moment.", 11),
            _fixture_msg(no_match, 14),
            _m("user",  "Is there anything on Monday?", 17),
        ],
        "success_condition": (
            "User asked for Monday. Fixture has only Tuesday 14th and Saturday 18th — no Monday. "
            "STATE STORED annotation (1 turn back) has first_available_time=5:00 PM, first_available_day=Tuesday. "
            "DAY MISMATCH: Monday not in stored_practitioners. CRITICAL RULE applies: "
            "first_available_time is non-null, so agent MUST proactively offer it. "
            "Expected: 'Nothing on Monday -- how does 5:00 PM on Tuesday sound?' (or close variant). "
            "Agent does NOT call smart_router. Does NOT call universal_router. "
            "EVALUATOR NOTE: any proactive offer of Tuesday 5:00 PM (or the 14th) is a PASS. "
            "Old-style day-list ('I do have Tuesday and Saturday. Which suits you?') is a FAIL."
        ),
        "success_examples": [
            _ok("Nothing on Monday -- how does 5:00 PM on Tuesday sound?"),
            _ok("I don't have anything on Monday, but I do have 5:00 PM on Tuesday the 14th -- does that work?"),
        ],
        "failure_examples": [
            _fail("I don't have anything on Monday -- I do have Tuesday the 14th and Saturday the 18th. Which suits you?"),
            _fail("[calls smart_router]"),
            _fail("[calls universal_router]"),
        ],
    })

    # S7B — caller confirms the proactive offer → CONFIRMATION + universal_router confirm_time.
    tests.append({
        "name": f"{p} S7B — S7 caller confirms proactive offer: CONFIRMATION + universal_router",
        "chat_history": s7_history_with_offer() + [
            _m("user", "Yes, that works perfectly.", 20),
        ],
        "success_condition": (
            "Agent offered 5:00 PM Tuesday the 14th. Caller confirms ('yes, that works perfectly'). "
            "CONFIRMATION fires: agent says 'Perfect, 5:00 PM Tuesday the 14th with Dithu Beeram "
            "at South Morang.' (or close variant) AND calls universal_router "
            "with intent='confirm_time'. Payload must include appointment_date='2026-04-14' and "
            "appointment_time in 24h format (17:00). "
            "Spoken confirmation must precede the tool call. "
            "Agent does NOT call smart_router. Does NOT ask another question."
        ),
        "success_examples": [
            _ok("Perfect, 5:00 PM Tuesday the 14th with Dithu Beeram at South Morang. "
                "[calls universal_router confirm_time appointment_date=2026-04-14 appointment_time=17:00]"),
        ],
        "failure_examples": [
            _fail("[calls smart_router]"),
            _fail("[no universal_router call]"),
            _fail("Which day would you prefer?"),
        ],
    })

    # S7C — caller names a specific time → deferred_time → STEP 9 offers that time.
    tests.append({
        "name": f"{p} S7C — S7 caller names specific time: agent reads slot from Tuesday afternoon",
        "chat_history": s7_history_with_offer() + [
            _m("user", "How about 6 PM instead?", 20),
        ],
        "success_condition": (
            "Agent offered 5:00 PM Tuesday. Caller asks for 6 PM instead. "
            "STEP 9 path: agent checks slot_groups['afternoon'] for Tuesday 14th "
            "and finds 6:00 PM (it is present: 5:00 PM, 5:20 PM, 5:40 PM, 6:00 PM, 6:20 PM, 7:00 PM). "
            "Agent offers or confirms 6:00 PM on Tuesday — e.g. "
            "'6:00 PM on Tuesday works.' or 'How does 6:00 PM on Tuesday the 14th sound?' "
            "Agent does NOT call smart_router. Does NOT say 'nothing available'. "
            "Does NOT ask what day again."
        ),
        "success_examples": [
            _ok("6:00 PM on Tuesday works."),
            _ok("How does 6:00 PM on Tuesday the 14th sound?"),
            _ok("I've got 6:00 PM on Tuesday — does that work?"),
        ],
        "failure_examples": [
            _fail("[calls smart_router]"),
            _fail("I don't have 6 PM available"),
            _fail("Which day would you like?"),
        ],
    })

    # S7D — relative earlier signal → confirmed_band=morning → STEP 9 offers morning slots.
    tests.append({
        "name": f"{p} S7D — S7 relative earlier signal: morning band selected, morning slots offered",
        "chat_history": s7_history_with_offer() + [
            _m("user", "Morning would be better.", 20),
        ],
        "success_condition": (
            "Agent offered 5:00 PM Tuesday (afternoon). Caller says 'Morning would be better.' "
            "BAND SIGNAL path in STEP 7B response: agent sets confirmed_band=morning, "
            "reads slot_groups['morning'] for Tuesday 14th from cache: 9:00 AM, 9:30 AM, 10:00 AM. "
            "Agent offers morning slots — e.g. 'I've got 9:00 AM or 10:00 AM on Tuesday.' "
            "or 'How does 9:00 AM on Tuesday sound?' "
            "Agent does NOT call smart_router. Does NOT re-offer 5:00 PM or other afternoon slots."
        ),
        "success_examples": [
            _ok("I've got 9:00 AM or 10:00 AM on Tuesday."),
            _ok("How does 9:00 AM on Tuesday the 14th sound?"),
            _ok("The morning slots on Tuesday are 9:00 AM, 9:30 AM and 10:00 AM."),
        ],
        "failure_examples": [
            _fail("[calls smart_router]"),
            _fail("5:00 PM"),
            _fail("I don't have morning availability"),
        ],
    })

    # S7E — general decline without alternative → clarifying question.
    tests.append({
        "name": f"{p} S7E — S7 general decline: clarifying question asked",
        "chat_history": s7_history_with_offer() + [
            _m("user", "I can't make that, sorry.", 20),
        ],
        "success_condition": (
            "Agent offered 5:00 PM Tuesday. Caller says 'I can't make that, sorry' — "
            "a general decline with no alternative preference named. "
            "GENERAL DECLINE path: agent asks a clarifying question such as "
            "'No problem -- would a different time on Tuesday work, or would you prefer another day?' "
            "Agent does NOT call smart_router. Does NOT call universal_router. "
            "Does NOT immediately list all available days unprompted. "
            "EVALUATOR NOTE: any short clarifying question asking whether a different time on Tuesday "
            "or a different day is preferred is a PASS. Listing all days without asking is a FAIL."
        ),
        "success_examples": [
            _ok("No problem -- would a different time on Tuesday work, or would you prefer another day?"),
            _ok("That's fine -- is there another time on Tuesday that might work, or would you like a different day?"),
        ],
        "failure_examples": [
            _fail("[calls smart_router]"),
            _fail("[calls universal_router]"),
            _fail("I do have Tuesday the 14th and Saturday the 18th. Which suits you?"),
        ],
    })

    # S7F — caller names a different day that IS in the fixture (Saturday) → STEP 8 → STEP 9.
    tests.append({
        "name": f"{p} S7F — S7 different day named (Saturday): slots offered without smart_router",
        "chat_history": s7_history_with_offer() + [
            _m("user", "Actually, what about Saturday instead?", 20),
        ],
        "success_condition": (
            "Agent offered Tuesday. Caller says 'Saturday instead'. "
            "Saturday 18th IS in stored_practitioners (fixture has Saturday with afternoon slots: "
            "1:00 PM, 1:30 PM, 2:00 PM). "
            "DIFFERENT DAY path: agent does NOT call smart_router (data already cached). "
            "Agent stores confirmed_day=Saturday. STEP 8 finds Saturday has only afternoon slots "
            "so silently stores confirmed_band=afternoon and proceeds to STEP 9. "
            "Agent offers Saturday afternoon slots — e.g. "
            "'I've got 1:00 PM, 1:30 PM or 2:00 PM on Saturday.' or "
            "'How does 1:00 PM on Saturday the 18th sound?' "
            "Agent does NOT call smart_router. Does NOT say 'I don't have Saturday'."
        ),
        "success_examples": [
            _ok("I've got 1:00 PM, 1:30 PM or 2:00 PM on Saturday."),
            _ok("How does 1:00 PM on Saturday the 18th sound?"),
            _ok("Saturday the 18th I have 1:00 PM, 1:30 PM and 2:00 PM in the afternoon."),
        ],
        "failure_examples": [
            _fail("[calls smart_router]"),
            _fail("I don't have Saturday"),
            _fail("[calls universal_router]"),
        ],
    })

    # S7G — first_available absent → falls back to old day-list behaviour.
    tests.append({
        "name": f"{p} S7G — S7 no first_available: old day-list fallback behaviour",
        "chat_history": [
            _m("user",  f"Hi, I'd like to book my {apt_type} appointment please.", 2),
            _m("agent", "When would you like to come in?", 5),
            _m("user",  "Monday please.", 8),
            _m("agent", "Checking that now, one moment.", 11),
            _fixture_msg(no_match_nfa, 14),
            _m("agent", "Let me see what I have for Monday.", 17),
            _m("user",  "What do you have available?", 20),
        ],
        "success_condition": (
            "confirmed_day=Monday, fixture has only Tuesday 14th and Saturday 18th — no Monday. "
            "first_available is NOT present in this fixture. "
            "STEP 7 OLD BEHAVIOUR (fallback): agent says something like "
            "'I don't have anything on Monday -- I do have Tuesday the 14th and Saturday the 18th. "
            "Which suits you?' (listing available days, asking caller to choose). "
            "Agent does NOT attempt a proactive time offer (no first_available to offer). "
            "Agent does NOT call smart_router. Does NOT call universal_router. "
            "EVALUATOR NOTE: any day-list response that names Tuesday and Saturday without "
            "offering a specific time is a PASS. A proactive time offer (e.g. '5:00 PM on Tuesday') "
            "that was not derived from the data is a FAIL."
        ),
        "success_examples": [
            _ok("I don't have anything on Monday -- I do have Tuesday the 14th and Saturday the 18th. Which suits you?"),
            _ok("Nothing on Monday, but I have availability on Tuesday and Saturday -- which works better for you?"),
        ],
        "failure_examples": [
            _fail("[calls smart_router]"),
            _fail("Nothing on Monday -- how does 5:00 PM on Tuesday sound?"),
            _fail("[calls universal_router]"),
        ],
    })

    return tests


# ── ElevenLabs API helpers ────────────────────────────────────────────────────

def _el_hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def create_scaffold_agent(node3_prompt: str, fixtures: Dict,
                          booking_for_override: str = "") -> Optional[str]:
    """Create a single-prompt scaffold agent with the Node 3 prompt and availability tools.
    NOTE: business_id/business_name are always pre-set from Node 2 in production.
    The dynamic variables here represent the resolved_context injected by Node 2.
    """
    payload = {
        "name": f"[Node3 Test] {CLINIC}",
        "conversation_config": {
            "agent": {
                "first_message": "Thanks for calling Northern Physio, how can I help you today?",
                "prompt": {
                    "prompt": node3_prompt,
                    "llm": SCAFFOLD_LLM,
                    "tool_ids": [
                        SMART_ROUTER_TOOL_ID,
                        UNIVERSAL_ROUTER_TOOL_ID,
                        ASYNC_CAPTURE_TOOL_ID,
                    ],
                    "temperature": 0.0,
                    "max_tokens": 1024,
                },
                "dynamic_variables": {
                    "dynamic_variable_placeholders": {
                        "called_number":           "+61000000000",
                        "caller_id":               "+61111111111",
                        "system__called_number":   "+61000000000",
                        "system__caller_id":       "+61111111111",
                        "system__time":            fixtures.get("system_time", "2026-04-08T09:00:00+10:00"),
                        "appointment_type_id":     "1429516429945742473",
                        "appointment_type":        "Physiotherapy Standard Appointment",
                        "booking_for":             booking_for_override,
                        "patient_status":          "existing",
                        "uni_router_intent":       "",
                        "timeframe_raw":           "",
                        "practitioner_preference": "",
                        "practitioners_comma":     "Dithu Beeram, Jas Mangat, Priya Ramesh",
                        "locations_comma":         "South Morang, Group One Medical, O'Herns Rd Medical Centre",
                        "new_patient_allocation_enabled": "true",
                        "info_answered":           "",
                        "cancellation_completed":  "",
                        "reschedule_mode":         "",
                        "return_node":             "",
                        # business_id/business_name always pre-set from Node 2 in production
                        "business_id":             "1670269975438305004",
                        "business_name":           "South Morang",
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


def create_booking_for_other_agent(node3_prompt: str, fixtures: Dict) -> Optional[str]:
    """Create a separate agent with booking_for=other for E2 test."""
    return create_scaffold_agent(node3_prompt, fixtures, booking_for_override="other")


def delete_scaffold_agent(agent_id: str) -> None:
    resp = requests.delete(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    if resp.status_code in (200, 204):
        print(f"✓ Agent {agent_id} deleted.")
    else:
        print(f"✗ Failed to delete agent {agent_id}: {resp.status_code}")


# ── Session agent management ──────────────────────────────────────────────────
# Keeps main + e2 scaffold agents alive between runs; patches prompt each time.
# Auto-deletes both when all tests pass. Use --cleanup to force-delete.

def load_session_agents() -> Dict:
    """Return {"main": id_or_None, "e2": id_or_None}."""
    if _SESSION_FILE_N3.exists():
        try:
            d = json.loads(_SESSION_FILE_N3.read_text(encoding="utf-8"))
            return {"main": d.get("main"), "e2": d.get("e2")}
        except Exception:
            pass
    return {"main": None, "e2": None}


def save_session_agents(main_id: Optional[str], e2_id: Optional[str]) -> None:
    _SESSION_FILE_N3.write_text(
        json.dumps({"main": main_id, "e2": e2_id}, indent=2), encoding="utf-8"
    )


def clear_session_agents() -> None:
    if _SESSION_FILE_N3.exists():
        _SESSION_FILE_N3.unlink()


def verify_agent_alive(agent_id: str) -> bool:
    resp = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    return resp.status_code == 200


def patch_scaffold_agent_prompt(agent_id: str, node3_prompt: str) -> bool:
    """Overwrite the prompt on an existing scaffold agent with the current local content."""
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


def load_passed_tests() -> set:
    path = CLINIC_DIR / "node3_passed_tests.json"
    if path.exists():
        return set(json.loads(path.read_text(encoding="utf-8")))
    return set()


def save_passed_tests(passed: set) -> None:
    path = CLINIC_DIR / "node3_passed_tests.json"
    path.write_text(json.dumps(sorted(passed), indent=2), encoding="utf-8")


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
            ti   = r.get("test_info", {}) or {}
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
                        print(f"         → {tn}: {json.dumps(ta)[:200]}")
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
    parser = argparse.ArgumentParser(description=f"Node 3 Availability Handler test scaffold — {CLINIC}")
    parser.add_argument("--agent-id",   help="Pin to a specific main agent ID (bypasses session management — never auto-deleted)")
    parser.add_argument("--run",        action="store_true", help="Run tests after creating/patching them")
    parser.add_argument("--keep-agent", action="store_true",
                        help="Do not auto-delete even when all tests pass")
    parser.add_argument("--cleanup",    action="store_true",
                        help="Delete the session agents and exit (no tests run)")
    parser.add_argument("--reset",      action="store_true",
                        help="Ignore previously passed tests and run everything")
    parser.add_argument("--filter",     default="",
                        help="Only run tests whose name contains this string (e.g. 'S7')")
    args = parser.parse_args()

    if not ELEVENLABS_API_KEY:
        print("✗ ELEVENLABS_API_KEY not set in .env"); sys.exit(1)

    # 1. Load Node 3
    node3_prompt = load_node3()
    if not node3_prompt:
        sys.exit(1)

    # 2. Load fixtures
    fixtures = load_fixtures()
    if not fixtures:
        sys.exit(1)

    # 3. Generate tests
    all_tests         = generate_tests(fixtures)
    previously_passed = set() if args.reset else load_passed_tests()

    # Apply --filter before splitting
    if args.filter:
        all_tests = [t for t in all_tests if args.filter.lower() in t["name"].lower()]
        print(f"✓ Filter '{args.filter}' matched {len(all_tests)} tests")

    # E2 test requires booking_for=other — split it out
    e2_tests   = [t for t in all_tests if t.get("_booking_for_override") == "other"]
    main_tests = [t for t in all_tests if not t.get("_booking_for_override")]

    if previously_passed:
        main_tests = [t for t in main_tests if t["name"] not in previously_passed]
        e2_tests   = [t for t in e2_tests   if t["name"] not in previously_passed]
        skipped    = len(all_tests) - len(main_tests) - len(e2_tests)
        total_run  = len(main_tests) + len(e2_tests)
        print(f"✓ Generated {len(all_tests)} tests — skipping {skipped} already passing, running {total_run}")
    else:
        total_run = len(all_tests)
        print(f"✓ Generated {total_run} test cases")

    if not main_tests and not e2_tests:
        print("✓ All tests already passing — nothing to run.")
        print("  Use --reset to force a full re-run.")
        return

    # 4. Resolve scaffold agent(s)
    # --cleanup: delete session agents and exit early
    if args.cleanup:
        session = load_session_agents()
        cleaned = 0
        for key, cid in session.items():
            if cid:
                print(f"Cleaning up {key} session agent {cid}...")
                delete_scaffold_agent(cid)
                cleaned += 1
        clear_session_agents()
        if not cleaned:
            print("No session agents found — nothing to clean up.")
        return

    agent_id        = args.agent_id
    session_managed = False
    session = load_session_agents()

    if agent_id:
        # Explicit --agent-id: patch prompt on pinned agent; never auto-delete
        print(f"Patching prompt on pinned agent {agent_id}...")
        patch_scaffold_agent_prompt(agent_id, node3_prompt)
    else:
        session_managed = True
        existing_main = session.get("main")
        if existing_main:
            if verify_agent_alive(existing_main):
                print(f"✓ Session main agent found: {existing_main}")
                ok = patch_scaffold_agent_prompt(existing_main, node3_prompt)
                if ok:
                    agent_id = existing_main
                else:
                    clear_session_agents()
                    session = {"main": None, "e2": None}
            else:
                print(f"  Session main agent {existing_main} no longer exists — creating fresh.")
                clear_session_agents()
                session = {"main": None, "e2": None}

        if not agent_id:
            agent_id = create_scaffold_agent(node3_prompt, fixtures)
            if not agent_id:
                sys.exit(1)
            session["main"] = agent_id
            save_session_agents(session["main"], session.get("e2"))

    # E2 agent: booking_for=other — manage separately via session
    e2_agent_id = None
    if e2_tests:
        existing_e2 = session.get("e2") if session_managed else None
        if existing_e2:
            if verify_agent_alive(existing_e2):
                print(f"✓ Session e2 agent found: {existing_e2}")
                ok = patch_scaffold_agent_prompt(existing_e2, node3_prompt)
                e2_agent_id = existing_e2 if ok else None
                if not ok:
                    existing_e2 = None
            else:
                print(f"  Session e2 agent {existing_e2} no longer exists — creating fresh.")
                existing_e2 = None

        if not e2_agent_id:
            e2_agent_id = create_booking_for_other_agent(node3_prompt, fixtures)
            if not e2_agent_id:
                print("⚠  Could not create booking_for=other agent — E2 test will be skipped.")
                e2_tests = []
            elif session_managed:
                session["e2"] = e2_agent_id
                save_session_agents(session["main"], session["e2"])

    # 5. Push tests
    def push_batch(tests: List[Dict], label: str) -> List[str]:
        print(f"\nPushing {len(tests)} {label} tests to ElevenLabs agent-testing API...")
        ids = []
        for t in tests:
            tid = push_test(t)
            if tid:
                ids.append(tid)
                print(f"  ✓ {t['name']}")
        print(f"✓ {len(ids)}/{len(tests)} test cases created")
        return ids

    main_ids = push_batch(main_tests, "main")
    e2_ids   = push_batch(e2_tests, "booking_for=other") if e2_tests else []

    # 6. Run
    name_map: Dict[str, str] = {}
    newly_passed: set = set()

    if args.run:
        if main_ids:
            print(f"\nRunning {len(main_ids)} main tests on agent {agent_id}...")
            inv_id = dispatch_tests(agent_id, main_ids)
            if inv_id:
                result = poll_invocation(inv_id)
                if result:
                    _build_name_map(result.get("test_runs", []), main_tests, name_map)
                    newly_passed |= print_results(result, name_map)

        if e2_ids and e2_agent_id:
            print(f"\nRunning {len(e2_ids)} booking_for=other tests on agent {e2_agent_id}...")
            inv_id = dispatch_tests(e2_agent_id, e2_ids)
            if inv_id:
                result = poll_invocation(inv_id)
                if result:
                    _build_name_map(result.get("test_runs", []), e2_tests, name_map)
                    newly_passed |= print_results(result, name_map)

        if newly_passed:
            updated_passed = previously_passed | newly_passed
            save_passed_tests(updated_passed)
            print(f"✓ Pass registry updated — {len(updated_passed)} tests now marked passing.")

    # 7. Delete test cases from agent-testing UI (always — keeps the UI clean)
    all_test_ids = main_ids + e2_ids
    if all_test_ids:
        delete_tests(all_test_ids)

    # 8. Session agent lifecycle
    if session_managed and args.run:
        updated_passed = previously_passed | newly_passed
        all_pass = (len(updated_passed) == len(all_tests))
        if all_pass and not args.keep_agent:
            print(f"✓ All {len(all_tests)} tests passing — deleting scaffold agents.")
            delete_scaffold_agent(agent_id)
            if e2_agent_id:
                delete_scaffold_agent(e2_agent_id)
            clear_session_agents()
        elif all_pass:
            print(f"ℹ  All tests passing — agents kept (--keep-agent): {agent_id}")
        else:
            remaining = len(all_tests) - len(updated_passed)
            print(f"ℹ  {remaining} test(s) still failing — scaffold agents retained for next run.")
            print(f"   Main: {agent_id}  E2: {e2_agent_id or 'none'}")
            print(f"   (auto-reused on next run, or --cleanup to force delete)")
    elif session_managed and not args.run:
        print(f"ℹ  Tests pushed but not run — scaffold agents retained: {agent_id}")
        print(f"   Re-run with: python nodes/clinics/northern_physio/test_node3_scaffold.py --run")

    print("Done.")


if __name__ == "__main__":
    main()
