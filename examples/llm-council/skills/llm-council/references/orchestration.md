# Antigravity Subagent Orchestration Guide

Antigravity features native first-class subagent orchestration via the `invoke_subagent` tool. This document explains how the LLM Council dispatches and coordinates parallel advisors and reviewers.

---

## 1. Parallel Subagent Dispatch via `invoke_subagent`

In Antigravity, multiple subagents can be launched simultaneously in a single tool call by passing an array of configurations to `invoke_subagent`.

### Schema Example: Round 1 (Convene the Council)
```json
{
  "Subagents": [
    {
      "TypeName": "self",
      "Role": "Council Contrarian",
      "Prompt": "You are The Contrarian on an LLM Council. Focus on downside risk, failure modes, and hidden pitfalls...\n\nQuestion: [framed question]",
      "Model": "inherit",
      "Workspace": "inherit"
    },
    {
      "TypeName": "self",
      "Role": "Council First Principles",
      "Prompt": "You are The First Principles Thinker on an LLM Council. Strip assumptions and redefine the core dilemma...\n\nQuestion: [framed question]",
      "Model": "inherit",
      "Workspace": "inherit"
    },
    {
      "TypeName": "self",
      "Role": "Council Expansionist",
      "Prompt": "You are The Expansionist on an LLM Council. Focus on asymmetric upside, compounding scale, and adjacent opportunities...\n\nQuestion: [framed question]",
      "Model": "inherit",
      "Workspace": "inherit"
    },
    {
      "TypeName": "self",
      "Role": "Council Outsider",
      "Prompt": "You are The Outsider on an LLM Council. Respond with zero domain baggage. Spot the curse of knowledge...\n\nQuestion: [framed question]",
      "Model": "inherit",
      "Workspace": "inherit"
    },
    {
      "TypeName": "self",
      "Role": "Council Executor",
      "Prompt": "You are The Executor on an LLM Council. Focus on day-1 feasibility, operational hurdles, and the immediate next step...\n\nQuestion: [framed question]",
      "Model": "inherit",
      "Workspace": "inherit"
    }
  ]
}
```

---

## 2. Reactive Wakeup Mechanics

- **No Polling Required**: Antigravity resumes execution automatically when subagents complete their tasks and report back.
- Once `invoke_subagent` is called, the primary agent does not need to poll task status in a loop. Simply stop calling tools to conclude the turn, and Antigravity will deliver the incoming messages when available.

---

## 3. Blind Peer-Review Round

When all 5 advisor responses arrive:
1. Map each response to a randomized letter (`Response A`, `Response B`, `Response C`, `Response D`, `Response E`).
2. Anonymize the authors completely so reviewers evaluate the reasoning, not the persona.
3. Dispatch 5 reviewer subagents in parallel using `invoke_subagent`.
4. Each reviewer answers:
   - Which response is the strongest and why?
   - Which response has the most critical blind spot?
   - What did all five responses completely miss?

---

## 4. Chairman Synthesis

The primary agent (or a dedicated chairman subagent) compiles:
1. The original framed question and workspace context.
2. All 5 advisor responses.
3. All 5 blind peer reviews.
4. Generates the final Council Verdict directly in chat and saves a clean Markdown artifact (`council_verdict.md`) in the conversation artifacts directory.
