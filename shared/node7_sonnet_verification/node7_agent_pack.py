#!/usr/bin/env python3
"""Blind local-agent probe pack for Node 7 (claude-sonnet-5). No network, no OpenRouter, no ElevenLabs.

build  : runtime prompt (system prompt + node Additional Prompt, EVERY {{dv}} substituted) per DV state, scenarios rendered as
         plain CALLER/AGENT/TOOL RESULT text with NO expected answer, agent-sized chunks, manifest.json with the agent prompts.
judge  : after the agents wrote results/, build judge_input.md (history + expected criterion + produced output) and a judge prompt.
The orchestrating conversation launches the Agent(model="sonnet") runs (a subagent cannot spawn them).

Usage (2026-09-20, Node 7 back on claude-sonnet-5; user rules: NO OpenRouter, NO ElevenLabs test without asking):
  python -X utf8 node7_agent_pack.py build --node-file <node.txt> --out <dir> [--tags a,b] [--ids X,Y] [--chunk 14]
  ... launch one Agent(subagent_type="general-purpose", model="sonnet", run_in_background=true) per manifest entry, using its "agent_prompt" ...
  python -X utf8 node7_agent_pack.py judge --out <dir> [--scenarios <json>]   -> judge_input.md, then ONE separate judge agent writes verdicts.txt
Fidelity notes: every {{dv}} is substituted (an empty-string DV is identical to an unset one); scenarios sharing a DV state share a prompt file;
the simulating agents never see the expected criterion; a local agent at default temperature is OPTIMISTIC — it cannot prove the platform-side entry hand-off.
"""
import argparse, json, os, re, sys, collections
from pathlib import Path

REPO = str(Path(__file__).resolve().parents[3]).replace("\\", "/")  # <repo>/nodes/shared/node7_sonnet_verification/<this file>
BASE_DVS = {
    "caller_phone": "+61412345678", "caller_id": "+61412345678",
    "called_number": "+61299998888", "system__called_number": "+61299998888",
    "session_id": "sess_test_001", "system__conversation_id": "conv_test_001",
    "clinic_name": "Test Physio Clinic",
}
MAXLINE = 1800


def wrap(text):
    out = []
    for line in text.split("\n"):
        while len(line) > MAXLINE:
            cut = line.rfind(" ", 0, MAXLINE)
            cut = cut if cut > 0 else MAXLINE
            out.append(line[:cut]); line = line[cut:].lstrip(" ")
        out.append(line)
    res = "\n".join(out)
    assert re.sub(r"\s+", " ", res) == re.sub(r"\s+", " ", text)
    return res


def subst(text, dvs):
    for k, v in dvs.items():
        text = text.replace("{{" + k + "}}", str(v))
    return re.sub(r"\{\{[a-zA-Z0-9_]+\}\}", "", text)  # every other DV reaches the model empty, as at runtime


def sid(s, i):
    m = re.match(r"([A-Za-z0-9\-\.]+)", s["name"])
    return m.group(1) if m else f"S{i}"


def render_history(hist, dvs):
    lab = {"user": "CALLER", "assistant": "AGENT", "tool": "TOOL RESULT"}
    return "\n".join(f"{lab.get(m['role'], m['role'].upper())}: {subst(m['content'], dvs)}" for m in hist)


def build(a):
    node = open(a.node_file, encoding="utf-8-sig").read().replace("\r", "")
    ap = node[node.index("Additional Prompt:"):]
    sysp = open(REPO + "/nodes/shared/system_prompt.txt", encoding="utf-8").read().replace("\r", "")
    sc = json.load(open(a.scenarios, encoding="utf-8"))["scenarios"]
    want_tags = set(a.tags.split(",")) if a.tags else None
    want_ids = set(a.ids.split(",")) if a.ids else None
    sel = []
    for i, s in enumerate(sc):
        s["_id"] = sid(s, i)
        if want_ids or want_tags:
            hit = (want_ids and s["_id"] in want_ids) or (want_tags and want_tags & set(s.get("tags", [])))
            if not hit:
                continue
        sel.append(s)
    out = a.out
    for d in ("prompts", "scenarios", "results"):
        os.makedirs(f"{out}/{d}", exist_ok=True)
    groups = collections.OrderedDict()
    def eff(s):  # effective DV overrides: an empty-string DV is identical to an unset one at runtime, and BASE values are no override
        return {k: v for k, v in (s.get("dvs") or {}).items() if str(v) != BASE_DVS.get(k, "")}
    for s in sel:
        groups.setdefault(json.dumps(eff(s), sort_keys=True), []).append(s)
    manifest, n = [], 0
    for gi, (key, members) in enumerate(groups.items()):
        dvs = dict(BASE_DVS); dvs.update(json.loads(key))
        pf = f"{out}/prompts/prompt_{gi:02d}.txt"
        prompt = wrap(subst(sysp + "\n\n" + ap, dvs))
        open(pf, "w", encoding="utf-8", newline="\n").write(prompt)
        for c in range(0, len(members), a.chunk):
            chunk = members[c:c + a.chunk]
            n += 1
            gid = f"g{n:02d}"
            sf, rf = f"{out}/scenarios/{gid}.txt", f"{out}/results/{gid}.txt"
            body = []
            for s in chunk:
                body.append(f"=== {s['_id']} ===\nConversation so far:\n{render_history(s['history'], dvs)}\n")
            open(sf, "w", encoding="utf-8", newline="\n").write(
                "Each block below is an independent phone conversation. The node must produce its NEXT turn.\n\n" + "\n".join(body))
            ids = [s["_id"] for s in chunk]
            ap_txt = (
                "You are simulating claude-sonnet-5 running as the live ElevenLabs voice-agent node described by a prompt, on a real phone call.\n"
                f"1. Use the Read tool on {pf} and read ALL of it (if a read is truncated, continue with offset/limit until you have read the whole file). "
                "That file is exactly the prompt you receive at runtime.\n"
                f"2. Use the Read tool on {sf}: it holds {len(chunk)} independent conversations ({', '.join(ids)}).\n"
                "3. For EACH conversation decide exactly what you, as that node, would output on your NEXT turn, following the prompt precisely. "
                "Treat every conversation independently — nothing carries over between them. Open no other file.\n"
                "4. Write ONE file with the Write tool to " + rf + " containing, per conversation, exactly:\n"
                "=== <ID> ===\nSPOKEN: <the exact words you speak this turn, or (silent) if you speak nothing>\n"
                "TOOL: <tool name and its exact arguments as you would send them, or (none)>\n"
                "(one TOOL: line per tool call if you make several in the same turn). No commentary, no reasoning, no verdicts.\n"
                f"5. Reply with only: done {len(chunk)}")
            manifest.append({"gid": gid, "prompt": pf, "scenarios": sf, "results": rf, "ids": ids, "agent_prompt": ap_txt})
    json.dump(manifest, open(f"{out}/manifest.json", "w"), indent=1)
    print(f"{len(sel)} scenarios -> {len(manifest)} agent runs in {out}")
    for m in manifest:
        print(m["gid"], m["ids"])


def judge(a):
    sc = {sid(s, i): s for i, s in enumerate(json.load(open(a.scenarios, encoding="utf-8"))["scenarios"])}
    manifest = json.load(open(f"{a.out}/manifest.json"))
    blocks, missing = [], []
    for m in manifest:
        txt = open(m["results"], encoding="utf-8").read() if os.path.exists(m["results"]) else ""
        got = {}
        parts = re.split(r"^=== (.+?) ===\s*$", txt, flags=re.M)
        for j in range(1, len(parts), 2):
            got[parts[j].strip()] = parts[j + 1].strip()
        for i in m["ids"]:
            if i not in got:
                missing.append(i); continue
            s = sc[i]
            dvs = dict(BASE_DVS); dvs.update(s.get("dvs") or {})
            blocks.append(f"### {i} — {s['name']}\nCONVERSATION:\n{render_history(s['history'], dvs)}\n\nEXPECTED (criterion):\n{s['expected_behavior']}\n\nPRODUCED:\n{got[i]}\n")
    open(f"{a.out}/judge_input.md", "w", encoding="utf-8").write("\n".join(blocks))
    print(f"{len(blocks)} scenarios ready for judging; missing results: {missing}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["build", "judge"])
    p.add_argument("--node-file"); p.add_argument("--scenarios", default=REPO + "/nodes/shared/node_7_cancellation_handler_scenarios.json")
    p.add_argument("--out", required=True); p.add_argument("--tags"); p.add_argument("--ids"); p.add_argument("--chunk", type=int, default=9)
    a = p.parse_args()
    build(a) if a.cmd == "build" else judge(a)
