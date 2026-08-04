# Retired — Qwen-era Node 6a/6b

**Retired 2026-08-04.** These are the production files for Node 6a (name collection — self
booking) and Node 6b (name collection — other booking) as they ran on `qwen35-397b-a17b` with
`Override: Enabled`, before being replaced fleet-wide by a `claude-haiku-4-5` +
`Override: Disabled` redesign.

Kept for historical reference only — **do not restore, patch, or treat as current**:

| File | What it was |
|---|---|
| `node_6a_name_collection_self.txt` | The shared/default Qwen node 6a — 318 lines, 14 BLOCKING SIGNALs, `Override: Enabled` (fully self-contained, duplicating filler/security/dead-air/financial/info-pivot/leave-message/contact-clinic logic that the Haiku replacement now inherits from `nodes/shared/system_prompt.txt` for free). |
| `node_6b_name_collection_other.txt` | The shared/default Qwen node 6b — 276 lines, 12 BLOCKING SIGNALs, same architecture. |
| `node_6a_name_collection_self_scenarios.json` / `node_6b_name_collection_other_scenarios.json` | The scenario batteries these were self-audited against on OpenRouter (`scripts/node_audit_openrouter.py`) — the pass/fail *requirements* they test were carried forward into the new node's scenario files (co-located with the current `nodes/shared/node_6a_name_collection_self.txt`), reworded where the mechanism changed (e.g. an inherited system-prompt block instead of a node-local Qwen SIGNAL). These old files are the pre-migration baseline, not a live target. |
| `mri_first_node_6a_name_collection_self.txt` / `mri_first_node_6b_name_collection_other.txt` | MRI First's per-clinic override of the above — its only real customization was routing plain pricing questions to `info_pivot` (Node 8) instead of the shared default's billing-callback offer, with an explicit "pricing is answered by Node 8" note. Retired rather than migrated because the new Haiku default already behaves this way (see the "deliberate behavior change #2" note in `.claude/rules/node6-haiku-slim-design.md`) — the override became redundant, not obsolete; MRI First now falls through to the shared default automatically (no per-clinic node_6a/6b file present). |
| `mri_first_node_6a_name_collection_self_scenarios.json` / `mri_first_node_6b_name_collection_other_scenarios.json` | MRI First's small (13-line) per-clinic scenario stub, orphaned alongside its parent file. |

**Why the replacement happened, and what changed:** see `.claude/rules/node6-haiku-slim-design.md`
for the full design rationale, research citations, the mapping of which Qwen signals moved to
the shared system prompt vs. stayed node-specific vs. were dropped as pure Qwen-compensation
scaffolding, and the self-audit results (60/60 scenario probes, 100%) that cleared this for
promotion.

**`.claude/rules/qwen-prompt-patterns.md`** (the Qwen-specific prompting rules these files were
written against) is still current for `qwen35-397b-a17b`-family models — it now applies only to
Node 11 (error recovery), the one remaining Qwen node in the fleet.

If a genuine regression is ever traced back to the new Haiku node 6a/6b that these old files
would have handled correctly, that's the signal to actually read this folder again — not before.
