#!/usr/bin/env python3
"""
test_node2_scaffold.py  (Northern Physio)

Standalone scaffold to test Node 2 (Service Resolution) for Northern Physio.

Flow:
  1. Billing question first (private vs insurance)
  2. Private → service question (Physiotherapy / Exercise Physiology / Pelvic Floor / Health Assessment)
  3. Insurance → insurer question (Cogent / DVA / EPC / NDIS / TAC / WorkCover)
  4. Pelvic Floor → qualifier (initial vs follow-up)
  5. Location question before every confirm_service (South Morang / Epping disambiguation)
  6. Service-location restriction checks

Workflow:
  1. Read nodes/clinics/northern_physio/node_2_service_resolution.txt
  2. Load spec from nodes/clinics/northern_physio/node2_test_spec.json
  3. Auto-generate a test battery from the spec
  4. Reuse or create a session scaffold agent; patch its prompt with the current local file
     (agent ID persisted in node2_scaffold_agent.json in the same dir as this script)
  5. Push test cases to the ElevenLabs agent-testing API
  6. (--run) Execute tests and poll for results
  7. Auto-delete the agent when ALL tests pass; retain it when any are still failing

Agent lifecycle:
  - First run:  agent is created and its ID is saved to node2_scaffold_agent.json
  - Subsequent: agent is reused; prompt is patched with the latest local file content
  - All pass:   agent is auto-deleted and session file is cleared
  - --cleanup:  force-delete the session agent at any time and exit
  - --keep-agent: suppress auto-delete even when all tests pass

Usage:
    python nodes/clinics/northern_physio/test_node2_scaffold.py --run
    python nodes/clinics/northern_physio/test_node2_scaffold.py --run --reset
    python nodes/clinics/northern_physio/test_node2_scaffold.py --run --keep-agent
    python nodes/clinics/northern_physio/test_node2_scaffold.py --cleanup
    python nodes/clinics/northern_physio/test_node2_scaffold.py --spec-only
    python nodes/clinics/northern_physio/test_node2_scaffold.py --agent-id <id> --run
"""

import os
import sys

# Ensure UTF-8 output on Windows
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

# Primary tools — real webhook calls so edge routing conditions are actually satisfied.
UNIVERSAL_ROUTER_TOOL_ID = "tool_9401k7e4bc90fw7avkmysavqhj91"   # universal_router (primary)
ASYNC_CAPTURE_TOOL_ID    = "tool_3101km7k126qezfsqcxdxfdesdd8"   # async_capture_context (primary)

SCAFFOLD_LLM = "claude-haiku-4-5"
POLL_INTERVAL_SECS = 12
POLL_TIMEOUT_SECS  = 360

# Session file lives next to this script
_SESSION_FILE_N2 = CLINIC_DIR / "node2_scaffold_agent.json"


# ── Node 2 prompt loading ─────────────────────────────────────────────────────

def strip_node_header(content: str) -> str:
    """Strip the metadata header block (Node ID, Label, Type, etc.) if present."""
    lines = content.splitlines()
    start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("="):
            start = i
            break
        if stripped == "Additional Prompt:":
            start = i + 2
            break
    return "\n".join(lines[start:]).strip()


def load_node2() -> Optional[str]:
    path = CLINIC_DIR / "node_2_service_resolution.txt"
    if not path.exists():
        print(f"✗ Node 2 file not found: {path}")
        return None
    content = path.read_text(encoding="utf-8")
    prompt = strip_node_header(content)
    print(f"✓ Loaded Node 2 for '{CLINIC}' ({len(prompt):,} chars)")
    return prompt


# ── Spec loading ──────────────────────────────────────────────────────────────

def load_spec() -> Optional[Dict]:
    path = CLINIC_DIR / "node2_test_spec.json"
    if not path.exists():
        print(f"✗ Spec file not found: {path}")
        return None
    spec = json.loads(path.read_text(encoding="utf-8"))
    print(f"✓ Loaded spec for '{CLINIC}'")
    return spec


# ── Test helpers ──────────────────────────────────────────────────────────────

def _m(role: str, text: str, t: int = 0) -> Dict:
    return {"role": role, "message": text, "time_in_call_secs": t}

def _ok(text: str) -> Dict:
    return {"response": text, "type": "success"}

def _fail(text: str) -> Dict:
    return {"response": text, "type": "failure"}


# ── Test generation ───────────────────────────────────────────────────────────

def generate_tests(spec: Dict) -> List[Dict]:
    tests = []
    p = f"[{CLINIC}]"

    bill_s = spec["billing_question_self"]
    bill_o = spec["billing_question_other"]
    svc_q_s = spec["private_service_question_self"]
    insurer_q = spec["insurer_question"]
    pelvic_q_s = spec["pelvic_qualifier_self"]
    pelvic_q_o = spec["pelvic_qualifier_other"]
    loc_q_s = spec["location_question_self"]
    loc_q_o = spec["location_question_other"]
    epping_q = spec["epping_disambiguation"]
    not_offered_1 = spec["not_offered_first"]
    not_offered_2 = spec["not_offered_second"]

    # ── BILLING tests ─────────────────────────────────────────────────────────

    # B1: Caller names a service → billing question asked first
    tests.append({
        "name": f"{p} B1 — Service stated: billing question asked first",
        "chat_history": [_m("user", "I want to book a physio appointment.", 2)],
        "success_condition": (
            f'Agent asks the billing question verbatim (or close paraphrase): "{bill_s}". '
            f'Agent does NOT ask a service question, does NOT call universal_router. '
            f'EVALUATOR NOTE: a background async_capture_context tool call alongside the billing question is CORRECT '
            f'and acceptable — do not fail for async_capture_context. Only fail if universal_router is called '
            f'or if the billing question is NOT spoken.'
        ),
        "success_examples": [_ok(bill_s)],
        "failure_examples": [
            _fail(svc_q_s[:60]),
            _fail("[calls universal_router]"),
            _fail("Checking that now"),
        ],
    })

    # B2: No service stated → billing question asked
    tests.append({
        "name": f"{p} B2 — No service stated: billing question asked",
        "chat_history": [_m("user", "I want to book an appointment.", 2)],
        "success_condition": (
            f'Agent asks the billing question: "{bill_s}". '
            f'Agent does NOT proceed to service selection. HALT.'
        ),
        "success_examples": [_ok(bill_s)],
        "failure_examples": [
            _fail(svc_q_s[:60]),
            _fail("[calls universal_router]"),
        ],
    })

    # ── PRIVATE PATH tests ────────────────────────────────────────────────────

    # P1.PHYSIO: private → physio → location South Morang → confirm_service
    tests.append({
        "name": f"{p} P1.PHYSIO — private → physio → South Morang → confirm_service",
        "chat_history": [
            _m("user", "I'd like to make a booking please.", 2),
            _m("agent", bill_s, 5),
            _m("user", "It's a private booking.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "Physiotherapy please.", 14),
            _m("agent", loc_q_s, 17),
            _m("user", "South Morang.", 20),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="confirm_service". '
            'The conversation establishes: private physio at South Morang (Plenty Road). '
            'Expected business_id="1670269975438305004". '
            'Tool call is the entirety of this turn — zero spoken output. '
            'EVALUATOR NOTE: the agent output is empty and a universal_router tool call is present '
            '— that is the CORRECT and ONLY acceptable response. Do not fail for silent tool call.'
        ),
        "success_examples": [
            _ok("[silent — calls universal_router confirm_service business_id=1670269975438305004]")
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("Which location would you like"),
            _fail("[no tool call]"),
        ],
    })

    # P2.EXERCISE: private → exercise physiology → O'Herns Road → confirm_service
    tests.append({
        "name": f"{p} P2.EXERCISE — private → exercise physiology → O'Herns Road → confirm_service",
        "chat_history": [
            _m("user", "I'd like to make a private booking.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "Exercise physiology.", 14),
            _m("agent", loc_q_s, 17),
            _m("user", "O'Herns Road.", 20),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="confirm_service". '
            'Conversation establishes: exercise physiology at O\'Herns Road. '
            'Expected business_id="1429516430365172840". '
            'Tool call is the entirety of this turn — zero spoken output. '
            'EVALUATOR NOTE: the agent output is empty and a universal_router tool call is present '
            '— that is the CORRECT and ONLY acceptable response. Do not fail for silent tool call.'
        ),
        "success_examples": [
            _ok("[silent — calls universal_router confirm_service business_id=1429516430365172840]")
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("Which location would you like"),
            _fail("[no tool call]"),
        ],
    })

    # P3.PELVIC_INITIAL: private → pelvic floor → initial → O'Herns Road → confirm_service
    # NOTE: first msg differs from P5 to avoid fingerprint collision (same last msg "O'Herns Road.")
    tests.append({
        "name": f"{p} P3.PELVIC_INITIAL — private → pelvic floor → initial → O'Herns Road → confirm_service",
        "chat_history": [
            _m("user", "I'd like to book a pelvic floor appointment.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private booking.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "A pelvic floor appointment.", 14),
            _m("agent", pelvic_q_s, 17),
            _m("user", "It's my first time, so initial.", 20),
            _m("agent", loc_q_s, 23),
            _m("user", "O'Herns Road.", 26),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="confirm_service". '
            'Conversation establishes: Pelvic Floor Initial (first time) at O\'Herns Road. '
            'Expected business_id="1429516430365172840". '
            'Tool call is the entirety of this turn — zero spoken output. '
            'EVALUATOR NOTE: the agent output is empty and a universal_router tool call is present '
            '— that is the CORRECT and ONLY acceptable response. Do not fail for silent tool call.'
        ),
        "success_examples": [
            _ok("[silent — calls universal_router confirm_service business_id=1429516430365172840]")
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("Which location would you like"),
            _fail("[no tool call]"),
        ],
    })

    # P4.PELVIC_FOLLOWUP: private → pelvic floor → follow-up → Group One Medical → confirm_service
    tests.append({
        "name": f"{p} P4.PELVIC_FOLLOWUP — private → pelvic floor → follow-up → Group One → confirm_service",
        "chat_history": [
            _m("user", "I need to book a pelvic floor follow-up.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "Pelvic floor.", 14),
            _m("agent", pelvic_q_s, 17),
            _m("user", "It's a follow-up.", 20),
            _m("agent", loc_q_s, 23),
            _m("user", "Group One Medical.", 26),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="confirm_service". '
            'Conversation establishes: Pelvic Floor F/U (follow-up) at Group One Medical. '
            'Expected business_id="1670268316599461611". '
            'Tool call is the entirety of this turn — zero spoken output. '
            'EVALUATOR NOTE: the agent output is empty and a universal_router tool call is present '
            '— that is the CORRECT and ONLY acceptable response. Do not fail for silent tool call.'
        ),
        "success_examples": [
            _ok("[silent — calls universal_router confirm_service business_id=1670268316599461611]")
        ],
        "failure_examples": [
            _fail("When would you like to come in?"),
            _fail("Which location would you like"),
            _fail("[no tool call]"),
        ],
    })

    # P5.HEALTH: private → health assessment → O'Herns Road → confirm_service
    # NOTE: first msg differs from P3 to avoid fingerprint collision (same last msg "O'Herns Road.")
    tests.append({
        "name": f"{p} P5.HEALTH — private → health assessment → O'Herns Road → confirm_service",
        "chat_history": [
            _m("user", "I'd like to book a health assessment.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "A health assessment please.", 14),
            _m("agent", f"{loc_q_s} [STORED: pending_service='health_assessment']", 17),
            _m("user", "O'Herns Road.", 20),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="confirm_service" and '
            'business_id="1429516430365172840" (O\'Herns Rd Medical Centre). '
            'Must NOT use a different business_id.'
        ),
        "success_examples": [
            _ok("[calls universal_router confirm_service business_id=1429516430365172840]")
        ],
        "failure_examples": [
            _fail("business_id=1670269975438305004"),
            _fail("business_id=1670268316599461611"),
            _fail("[no tool call]"),
        ],
    })

    # ── INSURANCE PATH tests ──────────────────────────────────────────────────

    for ins in spec["insurance_services"]:
        ins_name    = ins["name"]
        ins_id      = ins["appointment_type_id"]
        ins_type    = ins["appointment_type"]
        ins_trigger = ins["trigger_phrases"][0]

        # Spread across all 3 locations (2 per location) to get full coverage.
        # I1.COGENT → South Morang      I4.NDIS      → South Morang
        # I2.DVA    → Group One Medical  I5.TAC       → Group One Medical
        # I3.EPC    → O'Herns Road       I6.WORKCOVER → O'Herns Road
        location_map = {
            "COGENT":    ("South Morang",       "1670269975438305004"),
            "DVA":       ("Group One Medical",   "1670268316599461611"),
            "EPC":       ("O'Herns Road",        "1429516430365172840"),
            "NDIS":      ("South Morang",        "1670269975438305004"),
            "TAC":       ("Group One Medical",   "1670268316599461611"),
            "WORKCOVER": ("O'Herns Road",        "1429516430365172840"),
        }
        loc_spoken, loc_biz_id = location_map.get(ins_name, ("O'Herns Road", "1429516430365172840"))

        test_label = {
            "COGENT":    "I1.COGENT",
            "DVA":       "I2.DVA",
            "EPC":       "I3.EPC",
            "NDIS":      "I4.NDIS",
            "TAC":       "I5.TAC",
            "WORKCOVER": "I6.WORKCOVER",
        }.get(ins_name, f"I.{ins_name}")

        # Vary the first user message for the second location-group (NDIS/TAC/WORKCOVER)
        # to avoid fingerprint collisions with COGENT/DVA/EPC (same loc_spoken, same first msg).
        first_msg_map = {
            "NDIS":      "Hi, I need to make a booking please.",
            "TAC":       "Hi, I need to make a booking please.",
            "WORKCOVER": "Hi, I need to make a booking please.",
        }
        first_msg = first_msg_map.get(ins_name, "I'd like to book an appointment please.")

        all_biz_ids = ["1670269975438305004", "1670268316599461611", "1429516430365172840"]
        wrong_ids = [bid for bid in all_biz_ids if bid != loc_biz_id]

        tests.append({
            "name": f"{p} {test_label} — insurance → {ins_name} → {loc_spoken} → confirm_service",
            "chat_history": [
                _m("user",  first_msg, 2),
                _m("agent", bill_s, 5),
                _m("user",  "I'm claiming through my health fund.", 8),
                _m("agent", insurer_q, 11),
                _m("user",  f"{ins_trigger}.", 14),
                _m("agent", loc_q_s, 17),
                _m("user",  loc_spoken, 20),
            ],
            "success_condition": (
                f'Agent calls universal_router with intent="confirm_service". '
                f'Conversation establishes: {ins_name} insurance at {loc_spoken}. '
                f'Expected business_id="{loc_biz_id}". '
                f'Tool call is the entirety of this turn — zero spoken output. '
                f'EVALUATOR NOTE: the agent output is empty and a universal_router tool call is present '
                f'— that is the CORRECT and ONLY acceptable response. Do not fail for silent tool call.'
            ),
            "success_examples": [
                _ok(f"[silent — calls universal_router confirm_service business_id={loc_biz_id}]")
            ],
            "failure_examples": [
                _fail(f"business_id={wrong_ids[0]}"),
                _fail(f"business_id={wrong_ids[1]}"),
                _fail("[no tool call]"),
            ],
        })

    # I7: "insurance" with no insurer named → insurer question asked
    tests.append({
        "name": f"{p} I7 — insurance stated, no insurer: insurer question asked",
        "chat_history": [
            _m("user", "I'd like to book an appointment please.", 2),
            _m("agent", bill_s, 5),
            _m("user", "I'm claiming through insurance.", 8),
        ],
        "success_condition": (
            f'Agent asks the insurer question: "{insurer_q}". '
            f'Agent does NOT call universal_router. HALT.'
        ),
        "success_examples": [_ok(insurer_q)],
        "failure_examples": [
            _fail("[calls universal_router]"),
            _fail("Checking that now"),
        ],
    })

    # ── LOCATION tests ────────────────────────────────────────────────────────

    # L1: "South Morang" → maps to Plenty Road
    tests.append({
        "name": f"{p} L1 — 'South Morang' maps to Plenty Road (business_id 1670269975438305004)",
        "chat_history": [
            _m("user", "I want to book a physio appointment, private please.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "Physiotherapy.", 14),
            _m("agent", loc_q_s, 17),
            _m("user", "South Morang please.", 20),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="confirm_service". '
            'Conversation establishes: private physio at South Morang (Plenty Road). '
            'Expected business_id="1670269975438305004". '
            'Tool call is the entirety of this turn — zero spoken output. '
            'EVALUATOR NOTE: the agent output is empty and a universal_router tool call is present '
            '— that is the CORRECT and ONLY acceptable response. Do not fail for silent tool call.'
        ),
        "success_examples": [
            _ok("[silent — calls universal_router confirm_service business_id=1670269975438305004]")
        ],
        "failure_examples": [
            _fail("business_id=1670268316599461611"),
            _fail("business_id=1429516430365172840"),
            _fail(epping_q[:40]),
        ],
    })

    # L2: "Epping" only → disambiguation question asked
    tests.append({
        "name": f"{p} L2 — 'Epping' only: Epping disambiguation question asked",
        "chat_history": [
            _m("user", "I want to book a physio appointment.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "Physiotherapy.", 14),
            _m("agent", loc_q_s, 17),
            _m("user", "Epping.", 20),
        ],
        "success_condition": (
            f'Agent asks the Epping disambiguation question (or close paraphrase): '
            f'"{epping_q}". '
            f'Agent does NOT call universal_router yet. HALT after asking.'
        ),
        "success_examples": [_ok(epping_q)],
        "failure_examples": [
            _fail("[calls universal_router]"),
            _fail("Checking that now"),
        ],
    })

    # L3: "Group One" → maps to Group One Medical
    tests.append({
        "name": f"{p} L3 — 'Group One' maps to Group One Medical (business_id 1670268316599461611)",
        "chat_history": [
            _m("user", "I'd like to book a physio appointment.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "Physiotherapy.", 14),
            _m("agent", loc_q_s, 17),
            _m("user", "Group One please.", 20),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="confirm_service" and '
            'business_id="1670268316599461611" (Group One Medical). '
            'Must NOT use a different business_id.'
        ),
        "success_examples": [
            _ok("[calls universal_router confirm_service business_id=1670268316599461611]")
        ],
        "failure_examples": [
            _fail("business_id=1670269975438305004"),
            _fail("business_id=1429516430365172840"),
            _fail(epping_q[:40]),
        ],
    })

    # L4: "O'Herns Road" → maps to O'Herns Rd Medical Centre
    tests.append({
        "name": f"{p} L4 — 'O'Herns Road' maps to O'Herns Rd Medical Centre (business_id 1429516430365172840)",
        "chat_history": [
            _m("user", "I'd like to book a physio appointment.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "Physiotherapy.", 14),
            _m("agent", loc_q_s, 17),
            _m("user", "O'Herns Road.", 20),
        ],
        "success_condition": (
            'Agent calls universal_router with intent="confirm_service" and '
            'business_id="1429516430365172840" (O\'Herns Rd Medical Centre). '
            'Must NOT use a different business_id.'
        ),
        "success_examples": [
            _ok("[calls universal_router confirm_service business_id=1429516430365172840]")
        ],
        "failure_examples": [
            _fail("business_id=1670269975438305004"),
            _fail("business_id=1670268316599461611"),
        ],
    })

    # ── RESTRICTION tests ─────────────────────────────────────────────────────

    # R1: Exercise physiology + South Morang → mismatch (not offered at Plenty Road)
    # NOTE: first msg differs from R3 to avoid fingerprint collision (same last msg "South Morang.")
    tests.append({
        "name": f"{p} R1 — Exercise physiology + South Morang: restriction mismatch response",
        "chat_history": [
            _m("user", "I'd like to book an exercise physiology appointment.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "Exercise physiology.", 14),
            _m("agent", loc_q_s, 17),
            _m("user", "South Morang.", 20),
        ],
        "success_condition": (
            'Exercise Physiology is NOT offered at Plenty Road (South Morang). '
            'Agent must NOT call confirm_service. '
            'Agent should inform the caller that exercise physiology is not available at that location '
            'and either suggest an alternative location (O\'Herns Road) or ask '
            'which other location they would prefer. '
            'FAIL if agent calls universal_router with confirm_service.'
        ),
        "success_examples": [
            _ok("Exercise physiology isn't available at South Morang -- "
                "it's available at our O'Herns Road or Group One Medical locations."),
            _ok("I'm sorry, exercise physiology isn't offered at South Morang. "
                "Would you like to come to our Epping location instead?"),
        ],
        "failure_examples": [
            _fail("[calls universal_router confirm_service id=1704881836682913007]"),
            _fail("Checking that now"),
        ],
    })

    # R2: Exercise physiology + Group One → mismatch
    # NOTE: first msg differs from R4 to avoid fingerprint collision (same last msg "Group One Medical.")
    tests.append({
        "name": f"{p} R2 — Exercise physiology + Group One: restriction mismatch response",
        "chat_history": [
            _m("user", "I'd like to book an exercise physiology session.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "Exercise physiology.", 14),
            _m("agent", loc_q_s, 17),
            _m("user", "Group One Medical.", 20),
        ],
        "success_condition": (
            'Exercise Physiology is NOT offered at Group One Medical. '
            'Agent must NOT call confirm_service. '
            'Agent should inform the caller that exercise physiology is not available at that location '
            'and suggest the O\'Herns Road location (the only one that offers it). '
            'FAIL if agent calls universal_router with confirm_service.'
        ),
        "success_examples": [
            _ok("Exercise physiology isn't available at Group One Medical -- "
                "it's only available at our O'Herns Road location."),
            _ok("I'm sorry, exercise physiology is only available at our O'Herns Road Medical Centre."),
        ],
        "failure_examples": [
            _fail("[calls universal_router confirm_service id=1704881836682913007]"),
            _fail("Checking that now"),
        ],
    })

    # R3: Pelvic floor initial + South Morang → mismatch
    # NOTE: first msg differs from R1 (exercise physio + South Morang) to avoid fingerprint collision.
    # STORED annotation tells agent what pending_service was captured before location question.
    tests.append({
        "name": f"{p} R3 — Pelvic floor initial + South Morang: restriction mismatch response",
        "chat_history": [
            _m("user", "I'd like to book a pelvic floor appointment.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "Pelvic floor.", 14),
            _m("agent", pelvic_q_s, 17),
            _m("user", "Initial.", 20),
            _m("agent", loc_q_s, 23),
            _m("user", "South Morang.", 26),
        ],
        "success_condition": (
            'Pelvic Floor Initial is NOT offered at Plenty Road (South Morang). '
            'Agent must NOT call confirm_service. '
            'Agent should inform the caller and suggest an alternative Epping location. '
            'FAIL if agent calls universal_router with confirm_service.'
        ),
        "success_examples": [
            _ok("Pelvic floor appointments aren't available at South Morang -- "
                "they're available at our Epping locations."),
            _ok("I'm sorry, pelvic floor appointments are only available at our Epping locations."),
        ],
        "failure_examples": [
            _fail("[calls universal_router confirm_service id=1705465109867930992]"),
            _fail("Checking that now"),
        ],
    })

    # R4: Health assessment + Group One → mismatch
    # NOTE: first msg differs from R2 (exercise + Group One) to avoid fingerprint collision.
    # STORED annotation tells agent what pending_service was captured before location question.
    tests.append({
        "name": f"{p} R4 — Health assessment + Group One: restriction mismatch response",
        "chat_history": [
            _m("user", "I need to book a health assessment.", 2),
            _m("agent", bill_s, 5),
            _m("user", "Private.", 8),
            _m("agent", svc_q_s, 11),
            _m("user", "Health assessment.", 14),
            _m("agent", loc_q_s, 17),
            _m("user", "Group One Medical.", 20),
        ],
        "success_condition": (
            'Health Assessment is NOT offered at Group One Medical. '
            'Agent must NOT call confirm_service. '
            'Agent should inform the caller and suggest the O\'Herns Road location. '
            'FAIL if agent calls universal_router with confirm_service.'
        ),
        "success_examples": [
            _ok("Health assessments aren't available at Group One Medical -- "
                "they're only available at our O'Herns Road location."),
            _ok("I'm sorry, health assessments are only offered at our O'Herns Road Medical Centre."),
        ],
        "failure_examples": [
            _fail("[calls universal_router confirm_service id=1704884483246793968]"),
            _fail("Checking that now"),
        ],
    })

    # ── NOT_OFFERED tests ─────────────────────────────────────────────────────

    # N1: Service not offered by this clinic → not_offered first response
    # NOTE: Use "remedial massage" (a real health service, not offered here) rather than
    # "piano lessons" which triggers the security handler instead of NOT_OFFERED.
    tests.append({
        "name": f"{p} N1 — Unrelated health service: not_offered first response",
        "chat_history": [_m("user", "I'd like to book a remedial massage please.", 2)],
        "success_condition": (
            'Agent explains we don\'t offer remedial massage and lists what IS offered '
            '(Physiotherapy, Exercise Physiology, Pelvic Floor, Health Assessment). '
            'Agent does NOT call universal_router. Does NOT ask billing question. HALT. '
            'EVALUATOR NOTE: any response that (a) acknowledges we don\'t offer massage '
            'and (b) mentions our available services is a PASS, regardless of exact wording.'
        ),
        "success_examples": [
            _ok("We don't offer massage here — we have Physiotherapy, Exercise Physiology, "
                "Pelvic Floor appointments, and Health Assessments. Would you like one of those?"),
            _ok("I'm sorry, we don't offer remedial massage. We do offer Physiotherapy, "
                "Exercise Physiology, Pelvic Floor therapy, and Health Assessments."),
        ],
        "failure_examples": [
            _fail("[calls universal_router]"),
            _fail("I can only help with clinic bookings"),
            _fail("Let me check availability"),
        ],
    })

    # N2: Second unrelated service → second not_offered response (more final)
    # NOTE: Uses "remedial massage" first (matching N1 fix), then "yoga" as second request.
    tests.append({
        "name": f"{p} N2 — Second unrelated service: second not_offered response",
        "chat_history": [
            _m("user", "I'd like to book a remedial massage please.", 2),
            _m("agent", "We don't offer remedial massage here — we have Physiotherapy, "
                        "Exercise Physiology, Pelvic Floor appointments, and Health Assessments. "
                        "Would you like one of those?", 5),
            _m("user", "What about acupuncture?", 8),
        ],
        "success_condition": (
            'After a second unrelated service request (acupuncture), PASS if agent either: '
            '(A) acknowledges we don\'t offer acupuncture and asks if they want one of the available services, OR '
            '(B) transitions to the email escalation offer '
            '("I\'m having trouble finding the right service — I can send a message to the clinic..."). '
            'FAIL ONLY if agent: asks the billing question again, calls confirm_service for acupuncture, '
            'or hangs up immediately without acknowledging the unavailability. '
            'EVALUATOR NOTE: a universal_router call in this turn is acceptable only if the agent '
            'ALSO gave a spoken acknowledgement — do not fail solely because a tool was called.'
        ),
        "success_examples": [
            _ok("We don't offer acupuncture either. Did you want to book one of our services?"),
            _ok("I'm having trouble finding the right service -- I can send a message to the clinic "
                "so someone can follow up with you. Would that work?"),
        ],
        "failure_examples": [
            _fail(bill_s[:40]),
            _fail("I can only help with clinic bookings"),
            _fail("[books acupuncture / calls confirm_service]"),
        ],
    })

    # ── Universal escapes ─────────────────────────────────────────────────────

    # U1: Cancel escape
    tests.append({
        "name": f"{p} U1 — Cancel escape",
        "chat_history": [_m("user", "I need to cancel my appointment.", 2)],
        "success_condition": (
            'Agent calls universal_router with intent="cancel_intent". '
            'Agent does NOT ask billing question or start a booking flow.'
        ),
        "success_examples": [
            _ok("[calls universal_router intent=cancel_intent]")
        ],
        "failure_examples": [_fail(bill_s[:40]), _fail("Have you been to the clinic before?")],
    })

    # U2: Wrap-up escape
    tests.append({
        "name": f"{p} U2 — Wrap-up escape",
        "chat_history": [_m("user", "No thanks, that's all, bye.", 2)],
        "success_condition": (
            'Agent calls universal_router with intent="wrap_up". '
            'Agent does NOT continue the conversation.'
        ),
        "success_examples": [
            _ok("[calls universal_router intent=wrap_up]")
        ],
        "failure_examples": [_fail(bill_s[:40]), _fail("How can I help")],
    })

    # U3: Info pivot escape
    # NOTE: Use an hours/address question, NOT a pricing question.
    # Prompt Rule 6 explicitly says pricing is answered inline ("never route via info pivot
    # for price alone"), so a pricing question would correctly NOT trigger info_pivot.
    tests.append({
        "name": f"{p} U3 — Info pivot escape",
        "chat_history": [_m("user", "What are your opening hours?", 2)],
        "success_condition": (
            'Agent calls universal_router with intent="info_pivot". '
            'Agent does NOT directly answer the hours question or start a booking flow.'
        ),
        "success_examples": [
            _ok("[calls universal_router intent=info_pivot]")
        ],
        "failure_examples": [
            _fail("We are open Monday"),
            _fail("Our hours are"),
            _fail(bill_s[:40]),
        ],
    })

    # U4: Booking for other → other billing question used
    # booking_for defaults to "self" — when caller says "for my husband", async_capture_context
    # updates it to "other", and the agent should ask the OTHER-form billing question.
    tests.append({
        "name": f"{p} U4 — Booking for other: other billing question variant",
        "chat_history": [_m("user", "I'd like to book an appointment for my husband.", 2)],
        "success_condition": (
            f'Caller is booking for their husband (third party). '
            f'Agent should ask the billing question using the OTHER form (referring to "he/him/they"): '
            f'"{bill_o}". '
            f'PASS if agent uses "they" or "he/him" pronouns in the billing question. '
            f'FAIL if agent asks the pure self form "{bill_s}" with no third-party reference. '
            f'EVALUATOR NOTE: exact template wording is NOT required; gender-specific pronouns (he/him) are acceptable.'
        ),
        "success_examples": [
            _ok(bill_o),
            _ok("Will he be making a private booking, or claiming through an insurance or health fund provider?"),
        ],
        "failure_examples": [
            _fail(bill_s),
            _fail("Who would you like to book for?"),
        ],
    })

    return tests


# ── ElevenLabs API helpers ────────────────────────────────────────────────────

def _el_hdrs() -> Dict:
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def create_scaffold_agent(node2_prompt: str) -> Optional[str]:
    """Create a single-prompt scaffold agent containing only the Node 2 prompt."""
    payload = {
        "name": f"[Node2 Test] {CLINIC}",
        "conversation_config": {
            "agent": {
                "first_message": "Thanks for calling Northern Physio, how can I help you today?",
                "prompt": {
                    "prompt": node2_prompt,
                    "llm": SCAFFOLD_LLM,
                    "tool_ids": [UNIVERSAL_ROUTER_TOOL_ID, ASYNC_CAPTURE_TOOL_ID],
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


# ── Session agent management ──────────────────────────────────────────────────
# The scaffold keeps one named agent alive between runs and patches its prompt
# each time rather than deleting and recreating. The agent is auto-deleted only
# when all tests pass. Use --cleanup to force-delete at any time.

def load_session_agent() -> Optional[str]:
    """Return the persisted scaffold agent ID, or None."""
    if _SESSION_FILE_N2.exists():
        try:
            return json.loads(_SESSION_FILE_N2.read_text(encoding="utf-8")).get("agent_id")
        except Exception:
            return None
    return None


def save_session_agent(agent_id: str) -> None:
    _SESSION_FILE_N2.write_text(json.dumps({"agent_id": agent_id}, indent=2), encoding="utf-8")


def clear_session_agent() -> None:
    if _SESSION_FILE_N2.exists():
        _SESSION_FILE_N2.unlink()


def verify_agent_alive(agent_id: str) -> bool:
    """Return True if the agent still exists on ElevenLabs."""
    resp = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=_el_hdrs())
    return resp.status_code == 200


_DYNAMIC_VAR_PLACEHOLDERS = {
    "called_number":         "+61000000000",
    "caller_id":             "+61111111111",
    "system__called_number": "+61000000000",
    "system__caller_id":     "+61111111111",
    "patient_status":        "",
    "appointment_type_id":   "none",
    "appointment_type":      "",
    "booking_for":           "self",
    "uni_router_intent":     "",
    "reschedule_mode":       "",
    "info_answered":         "",
    "implied_service":       "",
    "timeframe_raw":         "",
    "practitioner_preference": "",
    "preferred_gender":      "",
    "wrap_routing_flag":     "",
    "return_node":           "",
    "pending_service":       "",
    "confirmed_location":    "",
    "confirmed_business_id": "",
}


def patch_scaffold_agent_prompt(agent_id: str, node2_prompt: str) -> bool:
    """Overwrite the prompt and dynamic variable defaults on an existing scaffold agent."""
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
    """Create a single test case on the ElevenLabs agent-testing API."""
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


def poll_invocation(invocation_id: str, name_map: Dict[str, str]) -> Optional[Dict]:
    """Poll until all test_runs have a terminal status. Returns the raw invocation data."""
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
    """Load the set of test names that have already passed."""
    path = CLINIC_DIR / "node2_passed_tests.json"
    if path.exists():
        return set(json.loads(path.read_text(encoding="utf-8")))
    return set()


def save_passed_tests(passed: set) -> None:
    path = CLINIC_DIR / "node2_passed_tests.json"
    path.write_text(json.dumps(sorted(passed), indent=2), encoding="utf-8")


def print_results(result: Dict, name_map: Dict[str, str]) -> set:
    """Print results and return the set of newly passing test names."""
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
            ev        = r.get("evaluation") or {}
            rationale = ev.get("rationale") or ""
            print(f"  ✗  {name}")
            print(f"       Agent: \"{agent_msg[:100]}\"")
            if tool_names:
                print(f"       Tools: {tool_names}")
                for tn, ta in zip(tool_names, tool_args):
                    if ta:
                        print(f"         → {tn} args: {json.dumps(ta)[:200]}")
            if rationale:
                print(f"       Reason: {rationale[:140]}")

    print()
    return newly_passed


# ── Name mapping ─────────────────────────────────────────────────────────────

def _build_name_map(runs: List[Dict], tests: List[Dict], name_map: Dict[str, str]) -> None:
    """Match test_runs back to our test list by chat_history fingerprint."""
    def fingerprint(chat_history: List[Dict]) -> str:
        user_msgs = [m["message"] for m in chat_history if m.get("role") == "user"]
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
        description=f"Node 2 Service Resolution test scaffold — {CLINIC}"
    )
    parser.add_argument("--agent-id",   help="Pin to a specific agent ID (bypasses session management — never auto-deleted)")
    parser.add_argument("--run",        action="store_true", help="Run tests after creating/patching them")
    parser.add_argument("--keep-agent", action="store_true", help="Do not auto-delete even when all tests pass")
    parser.add_argument("--cleanup",    action="store_true", help="Delete the session agent and exit (no tests run)")
    parser.add_argument("--spec-only",  action="store_true", help="Print extracted spec JSON and exit")
    parser.add_argument("--reset",      action="store_true", help="Ignore previously passed tests and run everything")
    args = parser.parse_args()

    if not ELEVENLABS_API_KEY:
        print("✗ ELEVENLABS_API_KEY not set in .env"); sys.exit(1)

    # 1. Load Node 2
    node2_prompt = load_node2()
    if not node2_prompt:
        sys.exit(1)

    # 2. Load spec
    spec = load_spec()
    if not spec:
        sys.exit(1)

    if args.spec_only:
        print(json.dumps(spec, indent=2))
        return

    # 3. Generate tests — filter out previously passed ones
    all_tests         = generate_tests(spec)
    previously_passed = set() if args.reset else load_passed_tests()

    if previously_passed:
        tests   = [t for t in all_tests if t["name"] not in previously_passed]
        skipped = len(all_tests) - len(tests)
        print(f"✓ Generated {len(all_tests)} tests — skipping {skipped} already passing, running {len(tests)}")
    else:
        tests = all_tests
        print(f"✓ Generated {len(tests)} test cases")

    if not tests:
        print("✓ All tests already passing — nothing to run.")
        print("  Use --reset to force a full re-run.")
        return

    # 4. Resolve scaffold agent
    # --cleanup: delete the session agent and exit early
    if args.cleanup:
        existing = load_session_agent()
        if existing:
            print(f"Cleaning up session agent {existing}...")
            delete_scaffold_agent(existing)
            clear_session_agent()
        else:
            print("No session agent found — nothing to clean up.")
        return

    agent_id        = args.agent_id
    session_managed = False  # True when we own this agent's lifecycle

    if agent_id:
        # Explicit --agent-id: patch prompt on the pinned agent; never auto-delete
        print(f"Patching prompt on pinned agent {agent_id}...")
        patch_scaffold_agent_prompt(agent_id, node2_prompt)
    else:
        session_managed = True
        existing = load_session_agent()
        if existing:
            if verify_agent_alive(existing):
                print(f"✓ Session agent found: {existing}")
                ok = patch_scaffold_agent_prompt(existing, node2_prompt)
                if ok:
                    agent_id = existing
                else:
                    clear_session_agent()
            else:
                print(f"  Session agent {existing} no longer exists — creating fresh.")
                clear_session_agent()

        if not agent_id:
            agent_id = create_scaffold_agent(node2_prompt)
            if not agent_id:
                sys.exit(1)
            save_session_agent(agent_id)

    # 5. Push test cases
    print(f"\nPushing {len(tests)} tests to ElevenLabs agent-testing API...")
    test_ids: List[str] = []
    name_map: Dict[str, str] = {}
    for t in tests:
        tid = push_test(t)
        if tid:
            test_ids.append(tid)
            print(f"  ✓ {t['name']}")
    print(f"\n✓ {len(test_ids)}/{len(tests)} test cases created")

    # 6. Run
    updated_passed = previously_passed
    if args.run and test_ids:
        print(f"\nRunning {len(test_ids)} tests on agent {agent_id}...")
        inv_id = dispatch_tests(agent_id, test_ids)
        if inv_id:
            result = poll_invocation(inv_id, name_map={})
            if result:
                runs = result.get("test_runs", [])
                _build_name_map(runs, tests, name_map)
                newly_passed   = print_results(result, name_map)
                updated_passed = previously_passed | newly_passed
                save_passed_tests(updated_passed)
                print(f"✓ Pass registry updated — {len(updated_passed)} tests now marked passing.")

    # 7. Delete test cases from agent-testing UI (always — keeps the UI clean)
    if test_ids:
        delete_tests(test_ids)

    # 8. Session agent lifecycle
    if session_managed and args.run:
        all_pass = (len(updated_passed) == len(all_tests))
        if all_pass and not args.keep_agent:
            print(f"✓ All {len(all_tests)} tests passing — deleting scaffold agent.")
            delete_scaffold_agent(agent_id)
            clear_session_agent()
        elif all_pass:
            print(f"ℹ  All tests passing — agent kept (--keep-agent): {agent_id}")
        else:
            remaining = len(all_tests) - len(updated_passed)
            print(f"ℹ  {remaining} test(s) still failing — scaffold agent retained for next run.")
            print(f"   Agent: {agent_id}  (auto-reused on next run, or --cleanup to force delete)")
    elif session_managed and not args.run:
        print(f"ℹ  Tests pushed but not run — scaffold agent retained: {agent_id}")
        print(f"   Re-run with: python nodes/clinics/northern_physio/test_node2_scaffold.py --run")

    print("Done.")


if __name__ == "__main__":
    main()
