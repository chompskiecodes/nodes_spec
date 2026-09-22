# Retired — Gemini-era Node 7b (Rescheduler)

**Retired 2026-09-22.** This is the production file for Node 7b (Rescheduler) as it ran on
`gemini-2.5-flash` with `Override: Disabled`, before being replaced fleet-wide by the
`claude-haiku-4-5` EXIT GATE redesign documented in
`docs/node7b-haiku-optimization-design.md`.

Kept for historical reference only — **do not restore, patch, or treat as current**.

## Why this file exists

The Haiku redesign (`nodes/shared/node_7b_rescheduler_haiku.txt` at the time) was built,
scenario-verified (58/58 on the existing battery), and documented as
"BUILT AND SCENARIO-VERIFIED, NOT PATCHED LIVE" as of 2026-09-08. Sometime between then and
2026-09-22, a session promoted and patched it live fleet-wide (32 of 33 clinics confirmed
running it via `scripts/verify_live_agent.py`) but never completed the git-side promotion: the
canonical `nodes/shared/node_7b_rescheduler.txt` was left on the old Gemini content, and the
`_haiku` staging file was never removed. This meant every fresh checkout's `nodes/shared/`
directory disagreed with what was actually live, and a future "sync gitlink to origin/main" or
a naive fleet-wide `fast_patch.py` run risked silently reverting the whole fleet back to this
Gemini version — undoing the fix.

Reconciled 2026-09-22: `node_7b_rescheduler_haiku.txt`'s content was promoted to replace
`nodes/shared/node_7b_rescheduler.txt` (Label corrected to drop the "Haiku draft — DEV ONLY"
marker), the `_haiku` staging file was deleted, and this old Gemini file was archived here
instead of left live at its old path. See `docs/node7b-haiku-optimization-design.md` for the
full design rationale and `nodes/PROMPT_PATTERNS.md`/CLAUDE.md's Node LLM map for the corrected
LLM assignment.

`nodes/clinics/plantar_fascia_clinic/node_7b_rescheduler.txt` (a documented per-clinic
Friday-only fork of this node) was re-forked onto the new Haiku base in the same session — its
Gemini-era version is not separately archived here since the fork's own NOTE header already
documents its lineage.
