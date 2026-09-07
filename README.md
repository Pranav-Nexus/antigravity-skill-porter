# 🚀 Antigravity Skill Porter & Optimizer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/)
[![Google Antigravity](https://img.shields.io/badge/Antigravity-Compatible-4285F4.svg)](https://antigravity.google)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange.svg)](http://makeapullrequest.com)
[![GitHub Stars](https://img.shields.io/github/stars/Pranav-Nexus/antigravity-skill-porter?style=social)](https://github.com/Pranav-Nexus/antigravity-skill-porter)

> **Bridge the AI Agent Ecosystem:** The ultimate transpiler and optimizer that imports, converts, and elevates agent skills from **Claude Code**, **Cursor**, and **OpenAI** into high-performance, native **Google Antigravity (AGY)** plugins and multi-agent workflows.

---

## 💡 Why This Exists

The AI agent community is experiencing rapid innovation, with developers publishing thousands of open-standard `SKILL.md` workflows for Claude Code and Cursor.

However, running external skills inside Google Antigravity naively creates severe friction:
- ❌ **Tool Hallucinations**: External skills hardcode Claude-specific tools (`Bash`, `Glob`, `Read`, `Edit`, `StrReplaceEditor`) which fail or cause confusion in Antigravity.
- ❌ **Context Blindness**: They search for `CLAUDE.md`, ignoring Antigravity's `GEMINI.md`, `AGENTS.md`, and hierarchical `.agents/rules/`.
- ❌ **Single-Agent Bottlenecks**: Claude skills are serialized for linear chat loops. They fail to tap Antigravity's native parallel subagent dispatch (`invoke_subagent`) with non-blocking **Reactive Wakeup**.
- ❌ **Missing Packaging**: They lack `plugin.json` manifests, preventing toggling and management via Antigravity's UI.

**`antigravity-skill-porter` solves this in one command.** It deterministically maps tools, synthesizes plugin manifests, injects multi-agent parallelism, and delivers ready-to-run Antigravity plugins.

---

## ✨ Features

- 🌐 **Direct Ingestion from Any Source**:
  - Ingest directly from GitHub URLs: `https://github.com/owner/repo`
  - Ingest specific subfolders/trees: `https://github.com/owner/repo/tree/main/skills/sub-skill`
  - Ingest multi-skill plugin bundles automatically (e.g. `slavingia/skills`)
  - Ingest local directories or standalone `SKILL.md` files
- 🔄 **Deterministic Tool Translation**:
  | Legacy Claude Tool / File | Antigravity Native Equivalent |
  | :--- | :--- |
  | `CLAUDE.md`, `claude.md` | `GEMINI.md`, `AGENTS.md` |
  | `Bash` | `run_command` |
  | `Read` / `cat` | `view_file` |
  | `Glob` | `find_by_name` |
  | `Grep` | `grep_search` |
  | `Edit` / `StrReplaceEditor` | `replace_file_content` |
  | `Write` | `write_to_file` |
- ⚡ **Multi-Agent & Subagent Up-Leveling**:
  - Detects parallelizable steps and injects Antigravity's `invoke_subagent` batch arrays with Reactive Wakeup mechanics.
- 📦 **Dual Packaging**:
  - Automatically generates `plugin.json` manifests.
  - Installs to both Global Plugins (`~/.gemini/config/plugins/<name>/`) and Global Skills (`~/.gemini/config/skills/<name>/`).
  - Supports `--workspace` installation for project-specific `.agents/skills/`.
- 🔍 **Interactive Diff & Dry-Run Mode**:
  - Run `--dry-run` to inspect a unified diff before any files are written to disk.

---

## ⚡ Quickstart

### 1. Run via CLI (Python 3.8+)

Clone the repository and port any skill instantly:

```bash
git clone https://github.com/Pranav-Nexus/antigravity-skill-porter.git
cd antigravity-skill-porter

# 1. Preview changes with dry-run
python port_skill.py https://github.com/aiwithremy/claude-skills-llm-council --dry-run

# 2. Port and install globally into Antigravity
python port_skill.py https://github.com/aiwithremy/claude-skills-llm-council

# 3. Port a multi-skill plugin repository
python port_skill.py https://github.com/slavingia/skills
```

### 2. Install as an Antigravity Native Skill

You can also use this tool **directly inside Antigravity as a skill**:

1. Copy this folder into `~/.gemini/config/plugins/skill-porter/`
2. In any Antigravity chat, simply ask:
   > *"Import and optimize this skill for Antigravity: https://github.com/owner/repo"*

---

## 🧪 Tested & Verified Examples

Included in the [`examples/`](./examples) directory are pre-ported, verified skills:
1. **`llm-council`**: Karpathy-style 5-advisor council with blind peer review, converted from Claude Code to Antigravity parallel subagents (`invoke_subagent`).
2. **`frontend-design`**: Anthropic's official frontend design craft skill, optimized for Antigravity with modern web guidance and visual inspection hooks.
3. **`minimalist-entrepreneur`**: Sahil Lavingia's full 10-skill business suite, converted from `.claude-plugin` into a unified Antigravity plugin bundle.

---

## 🤝 Contributing & Community

Contributions, issues, and feature requests are welcome!
- Have a skill you want pre-ported? Open an Issue or submit a PR into `examples/`.
- Want to add support for new agent platforms? Check out [`references/translation_rules.md`](./references/translation_rules.md).

If this tool saved you time or improved your Antigravity workflows, **please drop a star ⭐ on GitHub!** It helps other agentic developers discover the project.

---

## 📄 License

MIT © [Pranav-Nexus](https://github.com/Pranav-Nexus)
