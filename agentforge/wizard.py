"""
Interactive `agent-init init` wizard.

Detects existing agent configs in the cwd and offers to import them, then asks
a short Q&A to bootstrap agent-init.yaml + rules/.
"""
from __future__ import annotations
import logging
import sys
from pathlib import Path
from typing import Optional

from .sources.loader import list_bundles

BUNDLE_DESCRIPTIONS: dict[str, str] = {
    "core":       "Repo discovery + code generation from Jira tickets (recommended)",
    "atlassian":  "Jira (epics/stories/bugs/analytics) + Confluence ADRs",
    "github":     "GitHub PR workflow + GitHub Actions CI",
    "bitbucket":  "Bitbucket PR workflow + Bitbucket Pipelines CI",
    "lang-java":  "Java conventions (Spring/Quarkus) + Java code scaffolding",
    "lang-rust":  "Rust conventions + Rust code scaffolding",
    "lang-go":    "Go conventions + Go code scaffolding",
    "ui-react":   "React/TypeScript conventions + component scaffolding",
    "architect":  "Solution architect agent (PlantUML, ADRs, C4 diagrams)",
}

logger = logging.getLogger(__name__)


def run(cwd: Path) -> int:
    logger.debug("wizard start: cwd=%s", cwd)
    print("agent-init wizard\n")
    print(f"Working in: {cwd}\n")

    # 1. Detect existing configs.
    detected = _detect_existing(cwd)
    logger.debug("wizard detected configs: %s", ", ".join(detected) if detected else "(none)")
    if detected:
        print("Found existing agent configs:")
        for kind, path in detected.items():
            print(f"  • {kind:18}{path}")
        print()
        import_choice = _ask(
            "Import these as the starting point for org defaults?",
            options=["yes", "no"],
            default="yes",
        )
    else:
        import_choice = "no"

    # 2. Project basics.
    name = _ask_text("Project name", default=cwd.name)
    language = _ask_text("Primary language (python, kotlin, typescript, ...)", default="python")
    stack_raw = _ask_text("Stack (comma-separated, e.g. fastapi,postgres)", default="")
    stack = [s.strip() for s in stack_raw.split(",") if s.strip()]
    logger.debug("wizard project meta: name=%s language=%s stack=%s", name, language, ",".join(stack))

    # 3. Org defaults source.
    org_src: Optional[dict] = None
    use_org = _ask("Pull org-wide defaults from a git repo?", options=["yes", "no"], default="no")
    if use_org == "yes":
        url = _ask_text("Git URL (e.g. github.com/acme/sdlc-standards)")
        ref = _ask_text("Ref (branch or tag)", default="main")
        subpath = _ask_text("Subpath inside the repo (blank for root)", default="")
        org_src = {"type": "git", "url": url, "ref": ref}
        if subpath:
            org_src["path"] = subpath
        logger.debug("wizard org source: url=%s ref=%s subpath=%s", url, ref, subpath)

    # 4. Targets.
    targets_raw = _ask(
        "Which targets?",
        options=["both", "claude-code only", "copilot only"],
        default="both",
    )
    targets = {
        "both": ["claude-code", "copilot"],
        "claude-code only": ["claude-code"],
        "copilot only": ["copilot"],
    }[targets_raw]

    # 5. Built-in bundle selection.
    selected_bundles = _select_bundles()
    logger.debug("wizard bundles: %s", ", ".join(selected_bundles) if selected_bundles else "(none)")

    # 6. Write files.
    _write_manifest(cwd, name, language, stack, org_src, targets, selected_bundles)
    _scaffold_rules_tree(cwd / "rules")
    if import_choice == "yes":
        _import_existing(cwd, detected)

    print("\n✓ Initialized.")
    print(f"  manifest: {cwd / 'agent-init.yaml'}")
    print(f"  rules:    {cwd / 'rules'}/")
    print("\nNext: edit rules/, then run `agent-init build`.")
    return 0


def _detect_existing(cwd: Path) -> dict[str, Path]:
    found = {}
    candidates = {
        "CLAUDE.md":              cwd / "CLAUDE.md",
        ".claude/":               cwd / ".claude",
        "copilot-instructions":   cwd / ".github" / "copilot-instructions.md",
        ".github/instructions/":  cwd / ".github" / "instructions",
        ".cursor/rules/":         cwd / ".cursor" / "rules",
    }
    for kind, p in candidates.items():
        if p.exists():
            found[kind] = p
    return found


def _ask(prompt: str, options: list[str], default: str) -> str:
    opts_display = "/".join(f"[{o}]" if o == default else o for o in options)
    while True:
        ans = input(f"{prompt} ({opts_display}): ").strip().lower() or default
        for o in options:
            if ans == o or ans == o.split()[0]:
                return o
        print(f"  please pick one of: {', '.join(options)}")


def _ask_text(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    ans = input(f"{prompt}{suffix}: ").strip()
    return ans or default


def _select_bundles() -> list[str]:
    available = list_bundles()
    if not available:
        return []
    print("\nBuilt-in bundles (SDLC skill library):")
    for b in available:
        desc = BUNDLE_DESCRIPTIONS.get(b, "")
        print(f"  {b:<14} {desc}")
    print()
    raw = _ask_text(
        "Which bundles to include? (comma-separated, or 'none')",
        default="core",
    )
    if raw.lower() in ("none", ""):
        return []
    chosen = [b.strip() for b in raw.split(",") if b.strip()]
    valid = set(available)
    bad = [b for b in chosen if b not in valid]
    if bad:
        print(f"  warning: unknown bundles ignored: {', '.join(bad)}")
    return [b for b in chosen if b in valid]


def _write_manifest(cwd: Path, name: str, lang: str, stack: list[str],
                    org_src: Optional[dict], targets: list[str],
                    bundles: list[str] | None = None) -> None:
    sources = []
    for b in (bundles or []):
        sources.append(f"  - type: builtin\n    bundle: {b}")
    if org_src:
        src_line = f'  - type: git\n    url: {org_src["url"]}\n    ref: {org_src["ref"]}'
        if "path" in org_src:
            src_line += f'\n    path: {org_src["path"]}'
        sources.append(src_line)
    sources.append("  - type: local\n    path: ./rules")

    stack_str = "[" + ", ".join(stack) + "]" if stack else "[]"
    targets_str = "\n".join(f"  - {t}" for t in targets)

    manifest = f"""version: 1
project:
  name: {name}
  language: {lang}
  stack: {stack_str}

# Sources are loaded in order. Earlier = lower priority.
# Project-local rules override org defaults by id/name.
sources:
{chr(10).join(sources)}

targets:
{targets_str}
"""
    (cwd / "agent-init.yaml").write_text(manifest)


def _scaffold_rules_tree(rules_dir: Path) -> None:
    for sub in ("memory", "rules", "skills", "commands", "agents", "hooks"):
        (rules_dir / sub).mkdir(parents=True, exist_ok=True)
    # Seed a memory file so build produces something useful immediately.
    (rules_dir / "memory" / "overview.md").write_text("""---
title: Overview
priority: 10
---
TODO: describe this project — stack, conventions, key directories,
how to run tests, anything an agent should always know.
""")


def _import_existing(cwd: Path, detected: dict[str, Path]) -> None:
    """Copy existing config content into rules/memory/ so it isn't lost."""
    import_dir = cwd / "rules" / "memory"
    if "CLAUDE.md" in detected:
        content = detected["CLAUDE.md"].read_text()
        (import_dir / "imported-from-claude.md").write_text(
            f"---\ntitle: Imported from CLAUDE.md\npriority: 5\n---\n{content}"
        )
        print("  imported CLAUDE.md → rules/memory/imported-from-claude.md")
    if "copilot-instructions" in detected:
        content = detected["copilot-instructions"].read_text()
        (import_dir / "imported-from-copilot.md").write_text(
            f"---\ntitle: Imported from copilot-instructions\npriority: 5\n---\n{content}"
        )
        print("  imported copilot-instructions.md → rules/memory/imported-from-copilot.md")
