#!/usr/bin/env python3
"""
Antigravity Skill Porter & Optimizer (port_skill.py)
Imports, translates, and optimizes agent skills (from Claude Code, Cursor, etc.)
into native Google Antigravity plugins and skills.
"""

import argparse
import difflib
import json
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Mapping of external LLM tool calls & conventions to Antigravity primitives
TOOL_REPLACEMENTS = [
    (r"\bView\b", "view_file"),
    (r"\bEdit\b", "replace_file_content"),
    (r"\bStrReplace\b", "replace_file_content"),
    (r"\bWrite\b", "write_to_file"),
    (r"\bBash\b", "run_command"),
    (r"\bGrep\b", "grep_search"),
    (r"\bFind\b", "find_by_name"),
    (r"\bLS\b", "list_dir"),
    (r"\bWebSearch\b", "search_web"),
    (r"\bFetch\b", "read_url_content"),
    (r"\bCLAUDE\.md\b", "GEMINI.md"),
    (r"\bCURSOR\.md\b", "AGENTS.md"),
    (r"Claude Code", "Google Antigravity"),
    (r"Claude", "Antigravity"),
]

def sanitize_path_component(name: str) -> str:
    """Ensures a name cannot escape via directory traversal or invalid characters."""
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '-', os.path.basename(name.strip()))
    return cleaned or "unnamed-skill"

def is_safe_subdir(parent: Path, child: Path) -> bool:
    """Verifies that child path is strictly contained within parent directory."""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False

def copy_support_tree(src_dir: Path, target_dir: Path):
    """Copies auxiliary/support files (scripts, resources, references) from src to target."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for item in src_dir.iterdir():
        if item.name.lower() in ("skill.md",):
            continue
        dst = target_dir / item.name
        if item.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)

def extract_frontmatter(content: str) -> Tuple[Dict[str, str], str]:
    """Parses YAML frontmatter from a markdown file."""
    meta = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            body = parts[2]
            for line in raw_yaml.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip().strip("\"'")
    return meta, body

def serialize_frontmatter(meta: Dict[str, str], body: str) -> str:
    """Builds markdown content with formatted YAML frontmatter."""
    fm_lines = ["---"]
    for k, v in meta.items():
        fm_lines.append(f'{k}: "{v}"' if any(c in v for c in ":#[]{}") else f"{k}: {v}")
    fm_lines.append("---")
    return "\n".join(fm_lines) + "\n" + body.lstrip("\r\n")

def optimize_for_antigravity(raw_content: str, metadata: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
    """Applies AST-level and regex semantic transformations to optimize for Antigravity."""
    updated_content = raw_content

    for pattern, replacement in TOOL_REPLACEMENTS:
        updated_content = re.sub(pattern, replacement, updated_content)

    # Subagent array parallelization
    subagent_pattern = r"(\bdispatch\s+subagent\b|\brun\s+subagent\b)"
    updated_content = re.sub(
        subagent_pattern,
        "invoke parallel subagents using invoke_subagent with Subagents array",
        updated_content,
        flags=re.IGNORECASE
    )

    # Artifact generation hint
    if "artifact" not in updated_content.lower() and ("generate" in updated_content.lower() or "report" in updated_content.lower()):
        artifact_block = (
            "\n\n## Antigravity Artifacts\n"
            "When generating comprehensive deliverables, code solutions, or multi-step plans, "
            "write them as interactive artifacts in the artifact directory with valid ArtifactMetadata.\n"
        )
        updated_content += artifact_block

    updated_meta, updated_body = extract_frontmatter(updated_content)
    if "name" in metadata and "name" not in updated_meta:
        updated_meta["name"] = metadata["name"]
    if "description" in metadata and "description" not in updated_meta:
        updated_meta["description"] = metadata["description"]

    final_doc = serialize_frontmatter(updated_meta, updated_body)
    return final_doc, updated_meta

def show_diff(original: str, optimized: str):
    """Prints a unified diff between the source skill and the optimized version."""
    orig_lines = original.splitlines(keepends=True)
    opt_lines = optimized.splitlines(keepends=True)
    diff = list(difflib.unified_diff(orig_lines, opt_lines, fromfile="Original (Source)", tofile="Optimized (Antigravity)"))

    if not diff:
        print("[*] No syntax modifications needed. The skill structure is already valid.")
        return

    print("=" * 60)
    print("DIFF: Optimizations applied for Google Antigravity")
    print("=" * 60)
    sys.stdout.reconfigure(encoding="utf-8")
    for line in diff:
        sys.stdout.write(line)
    print("=" * 60)

def resolve_source(source_arg: str) -> Tuple[str, Optional[Path], Dict[str, str]]:
    """Fetches skill content from local directory, file, or remote GitHub URL."""
    auxiliary_files = {}

    # 1. GitHub URL
    if source_arg.startswith("http://") or source_arg.startswith("https://"):
        url = source_arg
        if "github.com" in url:
            if "/blob/" in url:
                url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            elif "/tree/" in url:
                raw_base = url.replace("github.com", "raw.githubusercontent.com").replace("/tree/", "/")
                url = f"{raw_base.rstrip('/')}/SKILL.md"
            elif not url.endswith("/SKILL.md") and not url.endswith("/skill.md"):
                url = f"{url.rstrip('/')}/main/SKILL.md".replace("github.com", "raw.githubusercontent.com")

        print(f"[*] Downloading skill from: {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-Skill-Porter"})
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
        return content, None, auxiliary_files

    # 2. Local Path
    local_path = Path(os.path.expanduser(source_arg)).resolve()
    if not local_path.exists():
        raise FileNotFoundError(f"Local source path does not exist: {local_path}")

    if local_path.is_file():
        content = local_path.read_text(encoding="utf-8")
        return content, local_path.parent, auxiliary_files

    # Local Directory
    skill_file = local_path / "SKILL.md"
    if not skill_file.exists():
        skill_file = local_path / "skill.md"

    if not skill_file.exists():
        raise FileNotFoundError(f"No SKILL.md found in directory: {local_path}")

    content = skill_file.read_text(encoding="utf-8")

    # Capture auxiliary files
    for root, _, files in os.walk(local_path):
        for file in files:
            full_p = Path(root) / file
            if full_p == skill_file:
                continue
            rel_p = full_p.relative_to(local_path)
            try:
                auxiliary_files[str(rel_p)] = full_p.read_text(encoding="utf-8")
            except Exception:
                pass

    return content, local_path, auxiliary_files

def install_skill(
    skill_name: str,
    optimized_content: str,
    description: str,
    auxiliary_files: Dict[str, str],
    global_install: bool = True,
    workspace_install: bool = False,
    workspace_root: Optional[Path] = None,
    custom_dest: Optional[Path] = None
) -> List[str]:
    """Installs the optimized skill into Antigravity plugin and skill directories."""
    installed_paths = []
    user_home = Path(os.path.expanduser("~"))
    safe_name = sanitize_path_component(skill_name)

    # 1. Custom Destination
    if custom_dest:
        dest_root = Path(os.path.expanduser(str(custom_dest)))
        dest_skill_dir = dest_root / safe_name
        dest_skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = dest_skill_dir / "SKILL.md"
        skill_file.write_text(optimized_content, encoding="utf-8")
        installed_paths.append(str(skill_file))
        for rel_path, fcontent in auxiliary_files.items():
            dest_f = dest_skill_dir / rel_path
            dest_f.parent.mkdir(parents=True, exist_ok=True)
            dest_f.write_text(fcontent, encoding="utf-8")
            installed_paths.append(str(dest_f))

    # 2. Global Plugin and Skill Paths
    if global_install and not custom_dest:
        config_dir = user_home / ".gemini" / "config"
        plugin_dir = config_dir / "plugins" / safe_name
        plugin_skill_dir = plugin_dir / "skills" / safe_name
        global_skill_dir = config_dir / "skills" / safe_name

        plugin_skill_dir.mkdir(parents=True, exist_ok=True)
        global_skill_dir.mkdir(parents=True, exist_ok=True)

        # plugin.json
        manifest = {
            "name": safe_name,
            "description": description
        }
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        installed_paths.append(str(plugin_dir / "plugin.json"))

        # SKILL.md
        (plugin_skill_dir / "SKILL.md").write_text(optimized_content, encoding="utf-8")
        installed_paths.append(str(plugin_skill_dir / "SKILL.md"))

        (global_skill_dir / "SKILL.md").write_text(optimized_content, encoding="utf-8")
        installed_paths.append(str(global_skill_dir / "SKILL.md"))

        # Auxiliary files
        for rel_path, fcontent in auxiliary_files.items():
            dest_plugin = plugin_skill_dir / rel_path
            dest_global = global_skill_dir / rel_path
            dest_plugin.parent.mkdir(parents=True, exist_ok=True)
            dest_global.parent.mkdir(parents=True, exist_ok=True)
            dest_plugin.write_text(fcontent, encoding="utf-8")
            dest_global.write_text(fcontent, encoding="utf-8")
            installed_paths.append(str(dest_plugin))

    # 3. Workspace Install
    if workspace_install:
        root = workspace_root or Path.cwd()
        ws_skill_dir = root / ".agents" / "skills" / safe_name
        ws_skill_dir.mkdir(parents=True, exist_ok=True)
        (ws_skill_dir / "SKILL.md").write_text(optimized_content, encoding="utf-8")
        installed_paths.append(str(ws_skill_dir / "SKILL.md"))
        for rel_path, fcontent in auxiliary_files.items():
            dest_ws = ws_skill_dir / rel_path
            dest_ws.parent.mkdir(parents=True, exist_ok=True)
            dest_ws.write_text(fcontent, encoding="utf-8")
            installed_paths.append(str(dest_ws))

    return installed_paths

def port_plugin_repo(
    repo_path: Path,
    dry_run: bool = False,
    workspace: bool = False,
    no_global: bool = False,
    custom_dest: Optional[Path] = None
):
    """Ports a repository containing multiple skills into an Antigravity plugin and skills."""
    claude_plugin_json = repo_path / ".claude-plugin" / "plugin.json"
    plugin_name = repo_path.name
    plugin_desc = f"Antigravity plugin ported from {repo_path.name}"

    if claude_plugin_json.exists():
        try:
            data = json.loads(claude_plugin_json.read_text(encoding="utf-8"))
            plugin_name = data.get("name", plugin_name)
            plugin_desc = data.get("description", plugin_desc)
        except Exception:
            pass

    plugin_name = sanitize_path_component(plugin_name)

    for pattern, replacement in TOOL_REPLACEMENTS:
        plugin_desc = re.sub(pattern, replacement, plugin_desc)

    skills_dir = repo_path / "skills"
    skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
    print(f"[+] Found multi-skill plugin repository: '{plugin_name}' with {len(skill_dirs)} skills.")

    user_home = Path(os.path.expanduser("~"))
    plugins_root = user_home / ".gemini" / "config" / "plugins"
    plugin_dir = plugins_root / plugin_name
    global_skills_dir = user_home / ".gemini" / "config" / "skills"

    if not is_safe_subdir(plugins_root, plugin_dir):
        raise ValueError(f"Dangerous plugin directory traversal detected: {plugin_dir}")

    if not dry_run and not no_global and not custom_dest:
        plugin_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "name": plugin_name,
            "description": plugin_desc
        }
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    all_installed = []
    for sdir in sorted(skill_dirs):
        skill_file = sdir / "SKILL.md"
        if not skill_file.exists():
            skill_file = sdir / "skill.md"
        if not skill_file.exists():
            continue

        content = skill_file.read_text(encoding="utf-8")
        meta, body = extract_frontmatter(content)
        if "name" not in meta:
            meta["name"] = sdir.name

        opt_content, opt_meta = optimize_for_antigravity(content, meta)
        sname = sanitize_path_component(opt_meta["name"])
        print(f"  [+] Optimized skill: {sname}")

        if not dry_run:
            if custom_dest:
                target_custom = custom_dest / sname
                copy_support_tree(sdir, target_custom)
                (target_custom / "SKILL.md").write_text(opt_content, encoding="utf-8")
                all_installed.append(str(target_custom / "SKILL.md"))

            if not no_global and not custom_dest:
                # Install into plugin
                target_plugin_skill = plugin_dir / "skills" / sname
                copy_support_tree(sdir, target_plugin_skill)
                (target_plugin_skill / "SKILL.md").write_text(opt_content, encoding="utf-8")
                all_installed.append(str(target_plugin_skill / "SKILL.md"))

                # Install into global skills root
                target_global = global_skills_dir / sname
                copy_support_tree(sdir, target_global)
                (target_global / "SKILL.md").write_text(opt_content, encoding="utf-8")
                all_installed.append(str(target_global / "SKILL.md"))

            if workspace:
                target_ws = Path.cwd() / ".agents" / "skills" / sname
                copy_support_tree(sdir, target_ws)
                (target_ws / "SKILL.md").write_text(opt_content, encoding="utf-8")
                all_installed.append(str(target_ws / "SKILL.md"))

    if dry_run:
        print(f"\n[+] Dry run complete for {len(skill_dirs)} skills in '{plugin_name}'. No files written.")
    else:
        print(f"\n[V] Successfully installed Antigravity skills from '{plugin_name}' ({len(all_installed)} items):")
        for p in all_installed[:10]:
            print(f"  - {p}")
        if len(all_installed) > 10:
            print(f"  ... and {len(all_installed) - 10} more.")

def main():
    parser = argparse.ArgumentParser(description="Antigravity Skill Porter & Optimizer")
    parser.add_argument("source", nargs="?", default=None, help="Source path (directory, SKILL.md, or GitHub repo URL)")
    parser.add_argument("--source", dest="source_opt", help="Source path (directory, SKILL.md, or GitHub repo URL)")
    parser.add_argument("--dest", help="Custom destination directory for installed skills")
    parser.add_argument("--name", help="Override skill name")
    parser.add_argument("--dry-run", action="store_true", help="Preview optimizations and diff without installing")
    parser.add_argument("--workspace", action="store_true", help="Install into current workspace (.agents/skills/) only")
    parser.add_argument("--no-global", action="store_true", help="Do not install into global ~/.gemini/config")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt for remote source installations")
    args = parser.parse_args()

    source = args.source_opt or args.source
    if not source:
        parser.print_help()
        sys.exit(1)

    print(f"[*] Reading source: {source}")
    custom_dest = Path(os.path.expanduser(args.dest)) if args.dest else None

    # When --workspace is specified, install strictly into the workspace (not globally)
    skip_global = args.no_global or args.workspace

    # Check for multi-skill local directory
    if Path(source).is_dir() and (Path(source) / "skills").is_dir():
        port_plugin_repo(
            Path(source),
            dry_run=args.dry_run,
            workspace=args.workspace,
            no_global=skip_global,
            custom_dest=custom_dest
        )
        return

    # Check for whole GitHub repo (without specific tree path)
    if ("github.com" in source) and ("/tree/" not in source) and ("/blob/" not in source):
        import tempfile, subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"[*] Cloning repository to inspect structure: {source}...")
            res = subprocess.run(["git", "clone", "--depth=1", source, tmpdir], capture_output=True, text=True)
            if res.returncode == 0 and (Path(tmpdir) / "skills").is_dir():
                port_plugin_repo(
                    Path(tmpdir),
                    dry_run=args.dry_run,
                    workspace=args.workspace,
                    no_global=skip_global,
                    custom_dest=custom_dest
                )
                return

    try:
        raw_content, local_base, aux_files = resolve_source(source)
    except Exception as e:
        print(f"[-] Error reading source: {e}", file=sys.stderr)
        sys.exit(1)

    metadata, body = extract_frontmatter(raw_content)
    if args.name:
        metadata["name"] = args.name

    print(f"[+] Optimizing skill '{metadata.get('name', 'unnamed')}' for Antigravity...")
    optimized_doc, updated_metadata = optimize_for_antigravity(raw_content, metadata)

    show_diff(raw_content, optimized_doc)

    if args.dry_run:
        print("[+] Dry run complete. No files written.")
        return

    # Remote safety confirmation
    is_remote = source.startswith("http://") or source.startswith("https://") or ("github.com" in source)
    if is_remote and not args.yes:
        if not sys.stdin.isatty():
            print("[!] Security notice: Remote source installation requires confirmation. Pass --yes to confirm.", file=sys.stderr)
            sys.exit(1)
        try:
            confirm = input(f"[*] Install downloaded skill '{updated_metadata.get('name')}'? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("[-] Installation aborted by user.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n[-] Installation aborted.")
            return

    skill_name = updated_metadata.get("name", "unnamed-skill")
    desc = updated_metadata.get("description", "Antigravity skill")
    print(f"[+] Installing skill '{skill_name}'...")
    installed = install_skill(
        skill_name=skill_name,
        optimized_content=optimized_doc,
        description=desc,
        auxiliary_files=aux_files,
        global_install=not skip_global,
        workspace_install=args.workspace,
        workspace_root=Path.cwd(),
        custom_dest=custom_dest
    )

    print("\n[V] Successfully installed Antigravity Skill & Plugin:")
    for path in installed:
        print(f"  - {path}")
    print("\n[+] Done! You can now invoke this skill in Antigravity.")

if __name__ == "__main__":
    main()
