#!/usr/bin/env python3
"""
patch_node2c_edges_ryde.py — restore Node 2C (Complaint Intake)'s outbound edges.

Successor to the original `patch_node2c_edges_ryde.py` (applied 2026-04-10, deleted in the
2026-07-15 retirement cleanup). Confirmed live via GET on 2026-09-09 that Node 2C
(node_2c_complaint_intake_tmp) has its inbound edge from Node 1 but ZERO outbound edges —
consistent with the documented 2026-04-15 incident where a batch_patch run without
--no-strict-edges wiped edges for nodes outside the patched folder, 5 days after these were
first applied.

Restores exactly the edge set documented in node_2c_complaint_intake.txt's header comment:
  edge_node2c_service_pivot     N2C -> N2   FWD: change_service
  edge_node2c_booking_self      N2C -> N6a  FWD: booking_self
  edge_node2c_booking_other     N2C -> N6b  FWD: booking_other
  edge_node2c_cancel_intent     N2C -> N7   FWD: cancel_intent
  edge_node2c_info_pivot        N2C -> N8   FWD: info_pivot
                                             BWD: info_answered AND caller_complaint != "none"
  edge_node2c_wrap_up           N2C -> N9   FWD: wrap_up
  edge_node2c_error_recovery    N2C -> N11  FWD: LLM (smart_voice_agent unrecoverable failure)
                                             BWD: LLM (smart_voice_agent retry possible)

Also re-applies the accompanying Node 2 -> Node 8 backward-condition tightening (documented in
the same file's Note) so a caller who arrived via 2C and pivots through Node 8 returns to 2C
rather than bouncing back into standard Node 2 service resolution:
  edge_new_node2_info_pivot (N2 -> N8) BWD: was info_answered AND appointment_type_id == "none"
                                        now  info_answered AND appointment_type_id == "none"
                                             AND caller_complaint == "none"

Deliberately does NOT touch additional_tool_ids on Node 2C. due_router (tool_6401k18fpvbrfcsv7d63p967n3vz)
is a test/demo tool (see smart_voice_agent_config.py DUE_ROUTER_*_CONSTANT — called_number and
conversation_id are hardcoded to fake test values, not the real caller's data) and must never be
wired to a node that takes real calls.

Usage:
  python nodes/practitioner_due/ryde_health/patch_node2c_edges_ryde.py [--dry-run]
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    sys.exit("ERROR: ELEVENLABS_API_KEY not set in .env")

AGENT_ID = "agent_4001knngjghcfwna069y6jjd6f2v"
AGENTS_URL = "https://api.elevenlabs.io/v1/convai/agents"
HEADERS = {"xi-api-key": API_KEY, "Content-Type": "application/json"}

NODE_2   = "node_01kbej6wqpf6dbt7vs563vxh94"
NODE_2C  = "node_2c_complaint_intake_tmp"
NODE_6A  = "node_01kbenaznwf6dbt7ztc7xphbzq"
NODE_6B  = "node_01kbenbrd5f6dbt80awydptcbe"
NODE_7   = "node_01kbemhx6xf6dbt7wa2hnywer8"
NODE_8   = "node_01kbemmcz6f6dbt7ws7b6zk74p"
NODE_9   = "node_01kbf348egf6dbt86h6b6ej77d"
NODE_11  = "node_01kbgm46v9fvgv43n0m989n3f0"

EXISTING_N2_N8_EDGE_ID = "edge_new_node2_info_pivot"


def _eq(var: str, value: str) -> dict:
    return {"type": "eq_operator", "left": {"type": "dynamic_variable", "name": var},
            "right": {"type": "string_literal", "value": value}}


def _neq(var: str, value: str) -> dict:
    return {"type": "neq_operator", "left": {"type": "dynamic_variable", "name": var},
            "right": {"type": "string_literal", "value": value}}


def _and(*children: dict) -> dict:
    return {"type": "and_operator", "children": list(children)}


def _expr(label: str, expression: dict) -> dict:
    return {"label": label, "type": "expression", "expression": expression}


def _llm(label: str | None, condition: str) -> dict:
    return {"label": label, "type": "llm", "condition": condition}


NEW_EDGES: dict[str, dict] = {
    "edge_node2c_service_pivot": {
        "source": NODE_2C, "target": NODE_2,
        "forward_condition": _expr("2C. Service Pivot", _eq("uni_router_intent", "change_service")),
        "backward_condition": None,
    },
    "edge_node2c_booking_self": {
        "source": NODE_2C, "target": NODE_6A,
        "forward_condition": _expr("2C. Booking Self", _eq("uni_router_intent", "booking_self")),
        "backward_condition": None,
    },
    "edge_node2c_booking_other": {
        "source": NODE_2C, "target": NODE_6B,
        "forward_condition": _expr("2C. Booking Other", _eq("uni_router_intent", "booking_other")),
        "backward_condition": None,
    },
    "edge_node2c_cancel_intent": {
        "source": NODE_2C, "target": NODE_7,
        "forward_condition": _expr("2C. Cancel Intent", _eq("uni_router_intent", "cancel_intent")),
        "backward_condition": None,
    },
    "edge_node2c_info_pivot": {
        "source": NODE_2C, "target": NODE_8,
        "forward_condition": _expr("2C. Info Pivot", _eq("uni_router_intent", "info_pivot")),
        "backward_condition": _expr(
            "8. Info Answered to Node 2C",
            _and(_eq("uni_router_intent", "info_answered"), _neq("caller_complaint", "none")),
        ),
    },
    "edge_node2c_wrap_up": {
        "source": NODE_2C, "target": NODE_9,
        "forward_condition": _expr("2C. Wrap Up", _eq("uni_router_intent", "wrap_up")),
        "backward_condition": None,
    },
    "edge_node2c_error_recovery": {
        "source": NODE_2C, "target": NODE_11,
        "forward_condition": _llm(
            None,
            "smart_voice_agent tool with intent='availability' failed/returned error/unrecoverable "
            "(system failures, database errors, or unexpected responses that cannot be handled "
            "within this node), originating_node was Complaint_Intake",
        ),
        "backward_condition": _llm(
            "11→2C. Retry Availability",
            "smart_voice_agent tool with intent='availability' failed but retry is possible with "
            "alternate parameters or simplified payload, originating_node was Complaint_Intake",
        ),
    },
}


def fetch_workflow() -> dict:
    r = requests.get(f"{AGENTS_URL}/{AGENT_ID}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json().get("workflow", {})


def patch_workflow(workflow: dict) -> dict:
    r = requests.patch(f"{AGENTS_URL}/{AGENT_ID}", headers=HEADERS, json={"workflow": workflow}, timeout=30)
    if r.status_code not in (200, 201):
        print(f"PATCH FAILED {r.status_code}: {r.text[:500]}")
        r.raise_for_status()
    return r.json()


def trigger_deployment() -> None:
    get_resp = requests.get(f"{AGENTS_URL}/{AGENT_ID}", headers=HEADERS, timeout=30)
    get_resp.raise_for_status()
    main_branch_id = get_resp.json().get("main_branch_id")
    if not main_branch_id:
        print("  WARNING: no main_branch_id found — skipping deploy trigger.")
        return
    payload = {"deployment_request": {"requests": [
        {"branch_id": main_branch_id, "deployment_strategy": {"type": "percentage", "traffic_percentage": 100}}
    ]}}
    resp = requests.post(f"{AGENTS_URL}/{AGENT_ID}/deployments", headers=HEADERS, json=payload, timeout=30)
    if resp.status_code in (200, 201):
        print("  Deployment triggered — agent is now live.")
    else:
        print(f"  DEPLOY FAILED {resp.status_code}: {resp.text[:300]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("Fetching live workflow...")
    wf = fetch_workflow()
    nodes = wf.get("nodes", {})
    edges = wf.get("edges", {})

    missing = [nid for nid in (NODE_2, NODE_2C, NODE_6A, NODE_6B, NODE_7, NODE_8, NODE_9, NODE_11) if nid not in nodes]
    if missing:
        sys.exit(f"ERROR: expected node id(s) not found in live agent: {missing}")
    if EXISTING_N2_N8_EDGE_ID not in edges:
        sys.exit(f"ERROR: expected existing edge {EXISTING_N2_N8_EDGE_ID!r} not found — topology has changed, aborting.")

    print(f"Node 2C found: {nodes[NODE_2C].get('label')}")
    print(f"Existing outbound edges from Node 2C: {sum(1 for e in edges.values() if e.get('source') == NODE_2C)}")

    print("\nEdges to add:")
    for eid, e in NEW_EDGES.items():
        print(f"  {eid}  {e['source']} -> {e['target']}")

    n2_n8 = edges[EXISTING_N2_N8_EDGE_ID]
    old_bwd = n2_n8.get("backward_condition")
    new_bwd = _expr(
        "8. Info Answered to Node 2",
        _and(_eq("uni_router_intent", "info_answered"), _eq("appointment_type_id", "none"), _eq("caller_complaint", "none")),
    )
    print(f"\nEdge to tighten: {EXISTING_N2_N8_EDGE_ID}")
    print(f"  OLD backward_condition: {json.dumps(old_bwd)}")
    print(f"  NEW backward_condition: {json.dumps(new_bwd)}")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return

    new_edges = {**edges, **NEW_EDGES}
    new_edges[EXISTING_N2_N8_EDGE_ID] = {**n2_n8, "backward_condition": new_bwd}

    print("\nPatching workflow...")
    result = patch_workflow({**wf, "edges": new_edges})
    print(f"  OK  agent_id={result.get('agent_id', '?')}")

    time.sleep(1)
    print("\nTriggering deployment...")
    trigger_deployment()

    print("\nVerifying...")
    wf2 = fetch_workflow()
    edges2 = wf2.get("edges", {})
    outbound = [k for k, v in edges2.items() if v.get("source") == NODE_2C]
    print(f"  Node 2C outbound edges now: {len(outbound)} -> {outbound}")
    print(f"  {EXISTING_N2_N8_EDGE_ID} backward_condition now: {json.dumps(edges2.get(EXISTING_N2_N8_EDGE_ID, {}).get('backward_condition'))}")


if __name__ == "__main__":
    main()
