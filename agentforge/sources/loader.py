"""
Source loader. Reads agent-init.yaml + rule trees and produces a merged Project IR.

Sources are loaded in order; earlier = lower priority. Within a source, the
local-disk convention (memory/, rules/, skills/, ...) is the canonical layout.
Git sources are cloned shallow into ~/.cache/agent-init/ and then loaded as
local sources from that path.
Builtin sources reference bundle directories shipped inside the package under
agent_init/builtin/<bundle>/.
"""
from __future__ import annotations
import hashlib
import os
import re
import subprocess
import logging
from importlib.resources import files as _pkg_files
from pathlib import Path
import yaml

from ..core.ir import (
    Project, MemoryBlock, Rule, Skill, Command, Agent, Hook, MCPServer,
    Policy, _Provenance,
)
from ..core.merge import merge_into
from ..schema import validate as validate_manifest


CACHE_DIR = Path(os.environ.get("AGENT_INIT_CACHE", str(Path.home() / ".cache" / "agent-init")))

logger = logging.getLogger(__name__)


def load(manifest_path: Path, *, skip_validation: bool = False) -> Project:
    logger.debug("load manifest: %s", manifest_path)
    manifest = yaml.safe_load(manifest_path.read_text())
    if not skip_validation:
        validate_manifest(manifest, manifest_path)
    proj_meta = manifest.get("project", {})

    merged = Project(
        name=proj_meta.get("name", "unnamed"),
        language=proj_meta.get("language", ""),
        stack=list(proj_meta.get("stack", [])),
        policy=_load_policy(manifest.get("policy", {})),
    )

    base = manifest_path.parent
    for src in manifest.get("sources", []):
        source_id, root = _resolve_source(src, base)
        logger.debug("load source: %s (path=%s)", source_id, root)
        loaded = _load_local(source_id, root)
        merge_into(merged, loaded)

    # MCP servers can also be declared inline in policy.
    for s in manifest.get("policy", {}).get("mcp_servers", []):
        srv = MCPServer(
            name=s["name"], command=s["command"],
            args=s.get("args", []), env=s.get("env", {}),
            provenance=_Provenance(source="manifest", file=str(manifest_path.name)),
        )
        merge_into(merged, Project(name=merged.name, mcp_servers=[srv]))

    logger.debug(
        "manifest loaded: rules=%d skills=%d commands=%d agents=%d hooks=%d memory=%d mcp=%d",
        len(merged.rules),
        len(merged.skills),
        len(merged.commands),
        len(merged.agents),
        len(merged.hooks),
        len(merged.memory),
        len(merged.mcp_servers),
    )
    return merged


def _resolve_source(src: dict, base: Path) -> tuple[str, Path]:
    t = src["type"]
    logger.debug("resolve source type: %s", t)
    if t == "local":
        path = (base / src["path"]).resolve()
        return f"local:{src['path']}", path
    if t == "git":
        return _resolve_git(src)
    if t == "builtin":
        return _resolve_builtin(src)
    raise ValueError(f"unknown source type: {t}")


def _resolve_builtin(src: dict) -> tuple[str, Path]:
    """Resolve a built-in bundle to its on-disk path inside the installed package."""
    bundle = src["bundle"]
    pkg_root = _pkg_files("agent_init")
    bundle_path = Path(str(pkg_root)) / "builtin" / bundle
    if not bundle_path.exists():
        available = list_bundles()
        raise ValueError(
            f"unknown builtin bundle: {bundle!r}. "
            f"Available: {', '.join(available) or '(none)'}"
        )
    logger.debug("resolved builtin bundle: %s -> %s", bundle, bundle_path)
    return f"builtin:{bundle}", bundle_path


def list_bundles() -> list[str]:
    """Return sorted names of all built-in bundles shipped with the package."""
    builtin_root = Path(str(_pkg_files("agent_init"))) / "builtin"
    if not builtin_root.exists():
        return []
    bundles = sorted(d.name for d in builtin_root.iterdir() if d.is_dir() and not d.name.startswith("_"))
    logger.debug("bundles discovered: %s", ", ".join(bundles) if bundles else "(none)")
    return bundles


def _resolve_git(src: dict) -> tuple[str, Path]:
    """Clone (or reuse cached clone of) a git source. Shallow, by ref."""
    url = src["url"]
    ref = src.get("ref", "main")
    subpath = src.get("path", "")

    key = hashlib.sha256(f"{url}@{ref}".encode()).hexdigest()[:16]
    repo_dir = CACHE_DIR / "repos" / key

    if not repo_dir.exists():
        logger.debug("cloning git source: %s@%s", url, ref)
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        clone_url = url if url.startswith(("http", "git@")) else f"https://{url}"
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", ref, clone_url, str(repo_dir)],
            check=True, capture_output=True,
        )
    else:
        logger.debug("using cached git source: %s@%s", url, ref)

    source_id = f"git:{url}@{ref}"
    return source_id, repo_dir / subpath


def _load_local(source_id: str, root: Path) -> Project:
    """Walk a rules/ directory and produce a single-source Project."""
    p = Project(name="unnamed")
    if not root.exists():
        return p

    logger.debug("load local source: %s", root)

    def prov(file: Path) -> _Provenance:
        return _Provenance(source=source_id, file=str(file.relative_to(root)))

    mem_dir = root / "memory"
    if mem_dir.exists():
        for path in sorted(mem_dir.glob("*.md")):
            fm, body = _split_frontmatter(path.read_text())
            p.memory.append(MemoryBlock(
                title=fm.get("title", path.stem),
                body=body,
                priority=int(fm.get("priority", 0)),
                provenance=prov(path),
            ))

    rules_dir = root / "rules"
    if rules_dir.exists():
        for path in sorted(rules_dir.glob("*.md")):
            fm, body = _split_frontmatter(path.read_text())
            p.rules.append(Rule(
                id=fm.get("id", path.stem),
                description=fm.get("description", ""),
                apply_to=fm.get("apply_to", []),
                body=body,
                exclude_agents=fm.get("exclude_agents", []),
                provenance=prov(path),
            ))

    skills_dir = root / "skills"
    if skills_dir.exists():
        for sdir in sorted(d for d in skills_dir.iterdir() if d.is_dir()):
            skill_md = sdir / "SKILL.md"
            if not skill_md.exists():
                continue
            fm, body = _split_frontmatter(skill_md.read_text())
            resources = {
                f.name: f.read_text()
                for f in sdir.iterdir()
                if f.is_file() and f.name != "SKILL.md"
            }
            p.skills.append(Skill(
                name=fm.get("name", sdir.name),
                description=fm.get("description", ""),
                body=body,
                resources=resources,
                provenance=prov(skill_md),
            ))

    cmd_dir = root / "commands"
    if cmd_dir.exists():
        for path in sorted(cmd_dir.glob("*.md")):
            fm, body = _split_frontmatter(path.read_text())
            p.commands.append(Command(
                name=fm.get("name", path.stem),
                description=fm.get("description", ""),
                body=body,
                provenance=prov(path),
            ))

    agt_dir = root / "agents"
    if agt_dir.exists():
        for path in sorted(agt_dir.glob("*.md")):
            fm, body = _split_frontmatter(path.read_text())
            p.agents.append(Agent(
                name=fm.get("name", path.stem),
                description=fm.get("description", ""),
                body=body,
                tools=fm.get("tools", []),
                model=fm.get("model"),
                provenance=prov(path),
            ))

    hooks_yaml = root / "hooks" / "hooks.yaml"
    if hooks_yaml.exists():
        hooks_def = yaml.safe_load(hooks_yaml.read_text()) or {}
        for h in hooks_def.get("hooks", []):
            script_path = h["script"]
            script_body = (root / "hooks" / script_path).read_text()
            p.hooks.append(Hook(
                event=h["event"],
                matcher=h.get("matcher", {}),
                script_path=script_path,
                script_body=script_body,
                fallback=h.get("fallback", "instruction"),
                provenance=prov(hooks_yaml),
            ))

    mcp_yaml = root / "mcp.yaml"
    if mcp_yaml.exists():
        mcp_def = yaml.safe_load(mcp_yaml.read_text()) or {}
        for s in mcp_def.get("mcp_servers", []):
            p.mcp_servers.append(MCPServer(
                name=s["name"],
                command=s["command"],
                args=s.get("args", []),
                env=s.get("env", {}),
                provenance=prov(mcp_yaml),
            ))

    return p


def _load_policy(d: dict) -> Policy:
    return Policy(
        block_paths=d.get("secrets", {}).get("block_paths", []),
        allowed_tools_per_agent=d.get("allowed_tools", {}),
    )


_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def _split_frontmatter(text: str) -> tuple[dict, str]:
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)
