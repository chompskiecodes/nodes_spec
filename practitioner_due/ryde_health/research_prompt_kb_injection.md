# Research Task: ElevenLabs Conversational AI — Knowledge Base Injection Behavior

## Context
We're building an ElevenLabs Conversational AI agent for a physiotherapy clinic.
One node needs access to two reference documents:

- **DOC 1**: complaint → service-category mapping table (~3.5 KB plain text, ~60 entries)
- **DOC 2**: practitioner focus / avoid lists (~2.5 KB plain text, ~30 practitioners)

Total combined size ≈ 6 KB / ~1500 tokens.

These are looked up on **every turn** of the conversation by the LLM (claude-haiku-4-5)
to: (a) classify the caller's complaint into one or more service categories,
and (b) decide which practitioners to surface or skip.

Both documents are static — they only change when a clinician is added or a focus
list is edited.

## The Question We Need Answered

For an ElevenLabs agent prompt, what is the **most token-efficient** and
**most reliable** way to make these two documents available to the LLM at every turn?

Specifically, compare these three options and tell us which is best, with a
clear explanation backed by the actual ElevenLabs documentation / observed behavior:

### Option A — Inline in the system prompt
Paste DOC 1 and DOC 2 directly into the agent's prompt (or override prompt for
this node). The LLM sees them as part of the system message every turn.

### Option B — ElevenLabs Knowledge Base, RAG **disabled** (small KB / "always inject")
Upload DOC 1 and DOC 2 as documents to the agent's Knowledge Base. Configure
the agent so RAG retrieval is **disabled** / not used (or configure the docs
to always be injected).

Our suspicion: for small knowledge bases, ElevenLabs injects the entire
document(s) into the system prompt verbatim every turn anyway, so token cost
is identical to Option A — but with the upside that the docs are editable
in the ElevenLabs dashboard without re-patching the agent prompt.

### Option C — ElevenLabs Knowledge Base, RAG **enabled**
Upload DOC 1 and DOC 2 as KB documents and let the RAG retriever pull
relevant chunks per turn based on the caller's message.

Our concern: RAG-chunked retrieval may miss the practitioner row we need
(complaint mapping is one-shot lookup, not semantic search) and break the
classification logic. Also unclear how chunking handles a tabular layout.

## What We Need From Your Research

1. **Confirm or refute Option B's assumption**: For an ElevenLabs Conversational
   AI agent with a small Knowledge Base (under ~10 KB total), are KB documents
   injected verbatim into the system prompt on every turn, or always retrieved
   via RAG? Cite the ElevenLabs documentation or settings that control this.

2. **Token cost comparison**: For each option, what is the approximate token
   overhead per turn (assume ~1500 input tokens for the documents themselves)?
   Are there hidden costs (KB metadata, retrieval API calls, etc.)?

3. **Reliability**: For complaint-to-category lookup (where missing a single row
   = wrong routing decision), which option gives the most deterministic behavior?

4. **Recommended option**: Pick A, B, or C, and explain why for *this* use case
   (small static lookup tables, every-turn access, deterministic routing required).

5. **Editability tradeoff**: If A and B have identical token cost, are there
   any practical reasons to still prefer A (inline)? E.g., version control,
   patch automation, prompt-as-code workflows?

## Output Format

A short markdown document (under 800 words) with:
- One-paragraph TL;DR recommendation (Option A / B / C and why)
- Bullet table comparing the three options on: token cost per turn, retrieval
  reliability, editability, vendor lock-in
- Citations / links to the ElevenLabs documentation pages that back each claim

## Sources to Check
- ElevenLabs Conversational AI documentation: knowledge base, RAG, agent prompts
- ElevenLabs API reference for agent configuration
- Any community / forum discussion of small-KB behavior
- The ElevenLabs dashboard agent settings UI screenshots if relevant

Do not speculate — if a claim isn't backed by documentation or a clearly
reproducible test, mark it as "uncertain" and explain what would need to be
tested to confirm it.
