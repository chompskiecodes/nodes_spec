#!/usr/bin/env python3
"""
integrate_node2c_ryde.py
Integrates Node 2C (Complaint Intake) into the Ryde Health agent.

Steps:
  1. Upload DOC 1 (complaint mapping) to ElevenLabs KB -- usage_mode: prompt
  2. Upload DOC 2 (practitioner constraints) to ElevenLabs KB -- usage_mode: prompt
  3. Patch Node 3 from local file (DUE-PRACTITIONER JUSTIFICATION block)
  4. Create Node 2C stub (tools + KB refs + placeholder prompt)
  5. Capture assigned Node 2C ID
  6. Update Node 1 local file (<NODE_2C_ID_TBD> -> real ID)
  7. Add Node 2C outbound edges (booking_self/other, cancel, info_pivot, wrap_up, error, service_change)
  8. Patch Node 2C full prompt body
  9. Patch Node 1

Usage:
  python nodes/ryde_health_practitioner_due/integrate_node2c_ryde.py [--dry-run] [--from-step N]
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent

load_dotenv(REPO_ROOT / ".env")

API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    sys.exit("ERROR: ELEVENLABS_API_KEY not set in .env")

AGENT_ID = "agent_4001knngjghcfwna069y6jjd6f2v"
BASE_URL = "https://api.elevenlabs.io/v1/convai"
KB_URL = f"{BASE_URL}/knowledge-base"
AGENTS_URL = f"{BASE_URL}/agents"

HEADERS = {"xi-api-key": API_KEY, "Content-Type": "application/json"}

# Known Ryde node IDs (confirmed 2026-04-08)
NODE_1   = "node_01kbej4q4sf6dbt7vd9f1e03t1"
NODE_2   = "node_01kbej6wqpf6dbt7vs563vxh94"
NODE_3   = "node_01kbemw1axf6dbt7xryxe7gpd7"
NODE_6A  = "node_01kbenaznwf6dbt7ztc7xphbzq"
NODE_6B  = "node_01kbenbrd5f6dbt80awydptcbe"
NODE_7   = "node_01kbemhx6xf6dbt7wa2hnywer8"
NODE_8   = "node_01kbemmcz6f6dbt7ws7b6zk74p"
NODE_9   = "node_01kbf348egf6dbt86h6b6ej77d"
NODE_11  = "node_01kbgm46v9fvgv43n0m989n3f0"

TOOL_SMART_VOICE_AGENT = "tool_4501k96qzckzemabz9rwppjms6zj"
TOOL_UNIVERSAL_ROUTER  = "tool_9401k7e4bc90fw7avkmysavqhj91"
TOOL_ASYNC_CAPTURE     = "tool_3101km7k126qezfsqcxdxfdesdd8"

DOC1_FILE   = SCRIPT_DIR / "doc1_complaint_mapping.txt"
DOC2_FILE   = SCRIPT_DIR / "doc2_practitioner_constraints.txt"
NODE3_FILE  = REPO_ROOT / "nodes" / "clinics" / "ryde_health" / "node_3_availability_handler.txt"
NODE1_FILE  = REPO_ROOT / "nodes" / "shared" / "node_1_entry_greeting_router.txt"
NODE2C_FILE = SCRIPT_DIR / "node_2c_complaint_intake.txt"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(url: str) -> dict:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def _patch_agent(workflow: dict) -> dict:
    r = requests.patch(f"{AGENTS_URL}/{AGENT_ID}", headers=HEADERS,
                       json={"workflow": workflow}, timeout=30)
    if r.status_code not in (200, 201):
        print(f"  PATCH error {r.status_code}: {r.text[:400]}")
        r.raise_for_status()
    return r.json()


def fetch_agent() -> dict:
    return _get(f"{AGENTS_URL}/{AGENT_ID}")


def fetch_workflow() -> dict:
    return fetch_agent().get("workflow", {})


def parse_node_prompt(path: Path) -> tuple[str, str, bool]:
    """Return (node_id, prompt_text, override_enabled) from a local node txt file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    meta = {}
    for line in lines[:10]:
        for key in ("Node ID", "Override"):
            if line.startswith(f"{key}:"):
                meta[key] = line.split(":", 1)[1].strip()
    node_id = meta.get("Node ID", "").strip()
    override_enabled = meta.get("Override", "").strip().lower() == "enabled"
    sep = "=" * 80
    parts = text.split(sep)
    prompt_text = ""
    full_last = parts[-1] if parts else ""
    marker = "Additional Prompt:"
    if marker in full_last:
        prompt_text = full_last.split(marker, 1)[1].lstrip("\n")
    else:
        prompt_text = full_last.lstrip("\n")
    prompt_text = prompt_text.rstrip()
    if not node_id:
        sys.exit(f"ERROR: Could not parse Node ID from {path}")
    return node_id, prompt_text, override_enabled


def _make_expression_edge(value: str) -> dict:
    return {
        "type": "expression",
        "expression": {
            "type": "eq_operator",
            "left":  {"type": "dynamic_variable", "name": "uni_router_intent"},
            "right": {"type": "string_literal",   "value": value},
        },
    }


def step_banner(n: int, label: str) -> None:
    print()
    print(f"{'=' * 60}")
    print(f"STEP {n}: {label}")
    print(f"{'=' * 60}")


# ---------------------------------------------------------------------------
# Step 1 & 2 — Upload KB documents
# ---------------------------------------------------------------------------

def upload_kb_doc(path: Path, name: str, dry_run: bool) -> str | None:
    """Upload a text file to ElevenLabs KB and return its ID."""
    print(f"  Uploading: {path.name} -> '{name}'")
    if dry_run:
        print("  [DRY RUN] skipping upload, returning placeholder ID")
        return f"kb_dry_run_{path.stem}"

    text = path.read_text(encoding="utf-8")
    r = requests.post(
        KB_URL,
        headers={"xi-api-key": API_KEY},
        files={
            "name": (None, name),
            "file": (path.name, text.encode("utf-8"), "text/plain"),
        },
        timeout=60,
    )
    if r.status_code not in (200, 201):
        print(f"  KB upload FAILED {r.status_code}: {r.text[:400]}")
        return None
    data = r.json()
    kb_id = data.get("id") or data.get("knowledge_base_id") or data.get("document_id")
    print(f"  KB ID: {kb_id}")
    return kb_id


def step_upload_kb(dry_run: bool) -> tuple[str | None, str | None]:
    step_banner(1, "Upload DOC 1 to ElevenLabs KB")
    kb1 = upload_kb_doc(DOC1_FILE, "Ryde Health - DOC 1 Complaint Mapping", dry_run)

    step_banner(2, "Upload DOC 2 to ElevenLabs KB")
    kb2 = upload_kb_doc(DOC2_FILE, "Ryde Health - DOC 2 Practitioner Constraints", dry_run)

    if not dry_run and (not kb1 or not kb2):
        sys.exit("ERROR: KB upload failed. Stopping.")
    return kb1, kb2


# ---------------------------------------------------------------------------
# Step 3 — Patch Node 3
# ---------------------------------------------------------------------------

def step_patch_node3(dry_run: bool) -> None:
    step_banner(3, "Patch Node 3 (DUE-PRACTITIONER JUSTIFICATION block)")
    node_id, prompt_text, override_enabled = parse_node_prompt(NODE3_FILE)
    print(f"  Node: {node_id}  Override: {override_enabled}")
    print(f"  Prompt length: {len(prompt_text)} chars")

    if dry_run:
        print("  [DRY RUN] skipping patch")
        return

    wf = fetch_workflow()
    nodes = wf.get("nodes", {})
    if node_id not in nodes:
        sys.exit(f"ERROR: Node 3 ({node_id}) not found in live agent.")

    updated = copy.deepcopy(nodes[node_id])
    if override_enabled:
        updated.setdefault("conversation_config", {}).setdefault("agent", {})\
               .setdefault("prompt", {})["prompt"] = prompt_text
        updated["additional_prompt"] = ""
    else:
        updated["additional_prompt"] = prompt_text

    result = _patch_agent({**wf, "nodes": {**nodes, node_id: updated}})
    print(f"  OK  agent_id={result.get('agent_id', '?')}")


# ---------------------------------------------------------------------------
# Step 4 — Create Node 2C stub
# ---------------------------------------------------------------------------

def _build_node2c_stub(kb1_id: str, kb2_id: str) -> dict:
    kb_refs = []
    if kb1_id:
        kb_refs.append({"type": "file", "id": kb1_id,
                         "name": "Ryde Health - DOC 1 Complaint Mapping",
                         "usage_mode": "prompt"})
    if kb2_id:
        kb_refs.append({"type": "file", "id": kb2_id,
                         "name": "Ryde Health - DOC 2 Practitioner Constraints",
                         "usage_mode": "prompt"})

    return {
        "label": "2C. Complaint Intake",
        "type": "override_agent",
        "position": {"x": -166.0, "y": -300.0},
        "conversation_config": {
            "turn": {
                "turn_eagerness": None,
                "spelling_patience": None,
                "speculative_turn": False,
            },
            "tts": {},
            "agent": {
                "prompt": {
                    "llm": "claude-haiku-4-5",
                    "built_in_tools": {},
                    "knowledge_base": kb_refs,
                    "custom_llm": None,
                }
            },
        },
        "additional_prompt": "PLACEHOLDER -- full prompt applied in Step 8.",
        "additional_knowledge_base": kb_refs,
        "additional_tool_ids": [
            TOOL_SMART_VOICE_AGENT,
            TOOL_UNIVERSAL_ROUTER,
            TOOL_ASYNC_CAPTURE,
        ],
        "edges": [],
        "edge_order": [],
    }


def step_create_node2c(kb1_id: str, kb2_id: str, dry_run: bool) -> str | None:
    step_banner(4, "Create Node 2C stub in ElevenLabs")
    stub = _build_node2c_stub(kb1_id, kb2_id)
    print(f"  Label: {stub['label']}")
    print(f"  KB refs: {len(stub['additional_knowledge_base'])}")
    print(f"  Tools: {stub['additional_tool_ids']}")

    if dry_run:
        print("  [DRY RUN] skipping node creation, returning placeholder ID")
        return "node_2c_dry_run"

    # Before patch: record existing node IDs
    wf = fetch_workflow()
    nodes_before = set(wf.get("nodes", {}).keys())

    # Use a temporary key; ElevenLabs may reassign
    tmp_key = "node_2c_complaint_intake_tmp"
    new_nodes = {**wf.get("nodes", {}), tmp_key: stub}
    result = _patch_agent({**wf, "nodes": new_nodes})
    print(f"  PATCH accepted. agent_id={result.get('agent_id', '?')}")

    # Re-fetch to find the assigned ID
    time.sleep(1)
    wf2 = fetch_workflow()
    nodes_after = wf2.get("nodes", {})
    new_keys = set(nodes_after.keys()) - nodes_before

    # Prefer the tmp_key if it survived; else find new node by label
    node2c_id = None
    if tmp_key in nodes_after:
        node2c_id = tmp_key
        print(f"  ElevenLabs kept our key: {node2c_id}")
    elif new_keys:
        # Find the new node(s) and match by label
        for k in new_keys:
            if nodes_after[k].get("label") == "2C. Complaint Intake":
                node2c_id = k
                break
        if not node2c_id:
            node2c_id = list(new_keys)[0]
        print(f"  ElevenLabs assigned ID: {node2c_id}")
    else:
        # tmp_key disappeared and no new keys -- ElevenLabs rejected the key;
        # search all nodes for the label
        for k, n in nodes_after.items():
            if n.get("label") == "2C. Complaint Intake":
                node2c_id = k
                print(f"  Found by label: {node2c_id}")
                break

    if not node2c_id:
        sys.exit("ERROR: Could not determine Node 2C ID after creation. Check live agent manually.")

    return node2c_id


# ---------------------------------------------------------------------------
# Step 6 — Update Node 1 local file
# ---------------------------------------------------------------------------

def step_update_node1_local(node2c_id: str, dry_run: bool) -> None:
    step_banner(6, f"Update Node 1 local file (<NODE_2C_ID_TBD> -> {node2c_id})")
    text = NODE1_FILE.read_text(encoding="utf-8")
    if "<NODE_2C_ID_TBD>" not in text:
        print("  WARNING: <NODE_2C_ID_TBD> not found in Node 1 file -- already replaced?")
        return
    updated = text.replace("<NODE_2C_ID_TBD>", node2c_id)
    if dry_run:
        print("  [DRY RUN] skipping file write")
        return
    NODE1_FILE.write_text(updated, encoding="utf-8")
    print(f"  Replaced in {NODE1_FILE.name}")


# ---------------------------------------------------------------------------
# Step 7 — Add Node 2C outbound edges
# ---------------------------------------------------------------------------

def step_add_edges(node2c_id: str, dry_run: bool) -> None:
    step_banner(7, "Add Node 2C outbound edges")

    new_edges = {
        "edge_2c_to_6a_booking_self": {
            "source": node2c_id,
            "target": NODE_6A,
            "forward_condition": {
                "label": "2C-A. Booking Self",
                **_make_expression_edge("booking_self"),
            },
            "backward_condition": None,
        },
        "edge_2c_to_6b_booking_other": {
            "source": node2c_id,
            "target": NODE_6B,
            "forward_condition": {
                "label": "2C-B. Booking Other",
                **_make_expression_edge("booking_other"),
            },
            "backward_condition": None,
        },
        "edge_2c_to_7_cancel": {
            "source": node2c_id,
            "target": NODE_7,
            "forward_condition": {
                "label": "2C-C. Cancel Intent",
                **_make_expression_edge("cancel_intent"),
            },
            "backward_condition": None,
        },
        "edge_2c_to_8_info_pivot": {
            "source": node2c_id,
            "target": NODE_8,
            "forward_condition": {
                "label": "2C-D. Info Pivot",
                **_make_expression_edge("info_pivot"),
            },
            "backward_condition": {
                "label": "8. Info Answered to Node 2C",
                "type": "expression",
                "expression": {
                    "type": "and_operator",
                    "children": [
                        {
                            "type": "eq_operator",
                            "left":  {"type": "dynamic_variable", "name": "uni_router_intent"},
                            "right": {"type": "string_literal",   "value": "info_answered"},
                        },
                        {
                            "type": "eq_operator",
                            "left":  {"type": "dynamic_variable", "name": "appointment_type_id"},
                            "right": {"type": "string_literal",   "value": "none"},
                        },
                    ],
                },
            },
        },
        "edge_2c_to_9_wrap_up": {
            "source": node2c_id,
            "target": NODE_9,
            "forward_condition": {
                "label": "2C-E. Wrap Up",
                **_make_expression_edge("wrap_up"),
            },
            "backward_condition": None,
        },
        "edge_2c_to_11_error": {
            "source": node2c_id,
            "target": NODE_11,
            "forward_condition": {
                "label": None,
                "type": "llm",
                "condition": (
                    "due_router tool call failed but retry is possible with alternate parameters "
                    "or simplified payload, originating_node was Complaint_Intake"
                ),
            },
            "backward_condition": None,
        },
        "edge_2c_to_2_service_change": {
            "source": node2c_id,
            "target": NODE_2,
            "forward_condition": {
                "label": "2C-F. Service Change",
                **_make_expression_edge("service_change"),
            },
            "backward_condition": None,
        },
    }

    edge_ids = list(new_edges.keys())
    print(f"  Adding {len(edge_ids)} edges: {edge_ids}")

    if dry_run:
        print("  [DRY RUN] skipping edge patch")
        return

    wf = fetch_workflow()
    existing_edges = wf.get("edges", {})
    nodes = wf.get("nodes", {})

    # Merge new edges
    merged_edges = {**existing_edges, **new_edges}

    # Update Node 2C's edge list
    if node2c_id in nodes:
        node2c = copy.deepcopy(nodes[node2c_id])
        node2c["edges"] = edge_ids
        node2c["edge_order"] = edge_ids
        updated_nodes = {**nodes, node2c_id: node2c}
    else:
        print(f"  WARNING: {node2c_id} not found in nodes -- edges added to workflow but node not updated")
        updated_nodes = nodes

    result = _patch_agent({**wf, "edges": merged_edges, "nodes": updated_nodes})
    print(f"  OK  agent_id={result.get('agent_id', '?')}")


# ---------------------------------------------------------------------------
# Step 8 — Patch Node 2C full prompt
# ---------------------------------------------------------------------------

def step_patch_node2c_prompt(node2c_id: str, dry_run: bool) -> None:
    step_banner(8, "Patch Node 2C full prompt body")
    _, prompt_text, override_enabled = parse_node_prompt(NODE2C_FILE)
    print(f"  Override: {override_enabled}  Prompt: {len(prompt_text)} chars")

    if dry_run:
        print("  [DRY RUN] skipping prompt patch")
        print(f"  Prompt preview: {prompt_text[:200]!r}")
        return

    wf = fetch_workflow()
    nodes = wf.get("nodes", {})
    if node2c_id not in nodes:
        sys.exit(f"ERROR: Node 2C ({node2c_id}) not found in live agent.")

    updated = copy.deepcopy(nodes[node2c_id])
    if override_enabled:
        updated.setdefault("conversation_config", {}).setdefault("agent", {})\
               .setdefault("prompt", {})["prompt"] = prompt_text
        updated["additional_prompt"] = ""
    else:
        updated["additional_prompt"] = prompt_text

    result = _patch_agent({**wf, "nodes": {**nodes, node2c_id: updated}})
    print(f"  OK  agent_id={result.get('agent_id', '?')}")

    # Verify
    time.sleep(1)
    wf2 = fetch_workflow()
    node_check = wf2.get("nodes", {}).get(node2c_id, {})
    if override_enabled:
        live_text = (node_check.get("conversation_config", {}).get("agent", {})
                     .get("prompt", {}).get("prompt") or "")
    else:
        live_text = node_check.get("additional_prompt") or ""
    match = live_text[:200].strip() == prompt_text[:200].strip()
    print(f"  Content verified: {match}")
    if not match:
        print(f"  Expected: {prompt_text[:100]!r}")
        print(f"  Got:      {live_text[:100]!r}")


# ---------------------------------------------------------------------------
# Step 9 — Patch Node 1
# ---------------------------------------------------------------------------

def step_patch_node1(dry_run: bool) -> None:
    step_banner(9, "Patch Node 1 (IMMEDIATE CAPTURE #4 + complaint_intake edge)")
    node_id, prompt_text, override_enabled = parse_node_prompt(NODE1_FILE)
    print(f"  Node: {node_id}  Override: {override_enabled}")
    print(f"  Prompt: {len(prompt_text)} chars")

    if "<NODE_2C_ID_TBD>" in prompt_text:
        sys.exit("ERROR: Node 1 file still has <NODE_2C_ID_TBD> -- run Step 6 first.")

    if dry_run:
        print("  [DRY RUN] skipping patch")
        return

    wf = fetch_workflow()
    nodes = wf.get("nodes", {})
    if node_id not in nodes:
        sys.exit(f"ERROR: Node 1 ({node_id}) not found in live agent.")

    updated = copy.deepcopy(nodes[node_id])
    if override_enabled:
        updated.setdefault("conversation_config", {}).setdefault("agent", {})\
               .setdefault("prompt", {})["prompt"] = prompt_text
        updated["additional_prompt"] = ""
    else:
        updated["additional_prompt"] = prompt_text

    # Add edge_new_node1_complaint_intake to Node 1's edge list if not present
    existing_edge_order = updated.get("edge_order", [])
    existing_edges_field = updated.get("edges", [])
    new_edge_id = "edge_new_node1_complaint_intake"
    if new_edge_id not in existing_edge_order:
        updated["edge_order"] = existing_edge_order + [new_edge_id]
    if new_edge_id not in existing_edges_field:
        updated["edges"] = list(existing_edges_field) + [new_edge_id]

    result = _patch_agent({**wf, "nodes": {**nodes, node_id: updated}})
    print(f"  OK  agent_id={result.get('agent_id', '?')}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Integrate Node 2C into Ryde Health agent.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be done without calling ElevenLabs APIs.")
    parser.add_argument("--from-step", type=int, default=1, metavar="N",
                        help="Resume from step N. Requires --kb1-id and --kb2-id for steps >= 4, "
                             "--node2c-id for steps >= 7.")
    parser.add_argument("--kb1-id", default=None, help="Existing KB doc ID for DOC 1 (skip upload).")
    parser.add_argument("--kb2-id", default=None, help="Existing KB doc ID for DOC 2 (skip upload).")
    parser.add_argument("--node2c-id", default=None, help="Existing Node 2C ID (skip creation).")
    args = parser.parse_args()

    dry = args.dry_run
    start = args.from_step

    print("=" * 60)
    print("Ryde Health -- Node 2C Integration Script")
    print(f"Agent: {AGENT_ID}")
    print(f"Dry run: {dry}")
    print(f"Starting from step: {start}")
    print("=" * 60)

    kb1_id = args.kb1_id
    kb2_id = args.kb2_id
    node2c_id = args.node2c_id

    # Steps 1 & 2
    if start <= 2:
        if args.kb1_id or args.kb2_id:
            print(f"\nUsing provided KB IDs: DOC1={kb1_id} DOC2={kb2_id}")
        else:
            kb1_id, kb2_id = step_upload_kb(dry)
    else:
        if not kb1_id or not kb2_id:
            print("WARNING: --from-step >= 3 but no KB IDs provided. KB refs will be empty.")

    # Step 3
    if start <= 3:
        step_patch_node3(dry)

    # Step 4 (create Node 2C)
    if start <= 4:
        if node2c_id and start > 4:
            print(f"\nUsing provided node2c-id: {node2c_id}")
        else:
            node2c_id = step_create_node2c(kb1_id or "", kb2_id or "", dry)
            print(f"\n  Node 2C ID: {node2c_id}")
            print("  (Save this ID in case you need to resume.)")

    # Step 5 (just report)
    if start <= 5:
        step_banner(5, f"Node 2C ID confirmed: {node2c_id}")
        print(f"  ID: {node2c_id}")

    if not node2c_id:
        sys.exit("ERROR: No Node 2C ID available. Use --node2c-id to provide one.")

    # Step 6
    if start <= 6:
        step_update_node1_local(node2c_id, dry)

    # Step 7
    if start <= 7:
        step_add_edges(node2c_id, dry)

    # Step 8
    if start <= 8:
        step_patch_node2c_prompt(node2c_id, dry)

    # Step 9
    if start <= 9:
        step_patch_node1(dry)

    print()
    print("=" * 60)
    print("Integration complete.")
    print(f"Node 2C ID: {node2c_id}")
    print()
    print("NEXT STEPS (manual -- ElevenLabs dashboard):")
    print("  1. Open the Ryde Health agent Knowledge Base.")
    print("  2. Find 'Ryde Health - DOC 1 Complaint Mapping' and 'Ryde Health - DOC 2 Practitioner Constraints'.")
    print("  3. Confirm each has 'Prompt' mode enabled (verbatim injection every turn).")
    print("     If usage_mode='prompt' was accepted via API this is already set.")
    print("  4. Open Node 2C in the workflow editor and verify edges are wired correctly.")
    print("  5. Place a test call or run the Node 2C scaffold test when ready.")
    print("=" * 60)


if __name__ == "__main__":
    main()
