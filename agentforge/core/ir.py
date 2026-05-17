"""
Intermediate Representation (IR).

Sources produce a Project. Adapters consume a Project.
Neither sees the other's format. This is the entire point of the design.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


HookEvent = Literal["PreToolUse", "PostToolUse", "Stop", "SessionStart"]
FallbackStrategy = Literal["github-action", "instruction", "skip"]


@dataclass
class _Provenance:
    """Where this element came from. Used for diagnostics + override reporting."""
    source: str = ""           # e.g. "org-defaults@v2.3.1" or "local:./rules"
    file: str = ""             # path inside the source
    overrode: list[str] = field(default_factory=list)  # sources this masked


@dataclass
class MemoryBlock:
    """Always-on context loaded into every session."""
    title: str
    body: str
    priority: int = 0
    provenance: _Provenance = field(default_factory=_Provenance)


@dataclass
class Rule:
    """Path-scoped behavior."""
    id: str
    description: str
    apply_to: list[str] = field(default_factory=list)
    body: str = ""
    exclude_agents: list[str] = field(default_factory=list)
    provenance: _Provenance = field(default_factory=_Provenance)


@dataclass
class Skill:
    """Auto-activated workflow. Description is what triggers it — write it carefully."""
    name: str
    description: str
    body: str
    resources: dict[str, str] = field(default_factory=dict)
    provenance: _Provenance = field(default_factory=_Provenance)


@dataclass
class Command:
    """User-triggered: /command-name."""
    name: str
    description: str
    body: str
    provenance: _Provenance = field(default_factory=_Provenance)


@dataclass
class Agent:
    """Specialist subagent."""
    name: str
    description: str
    body: str
    tools: list[str] = field(default_factory=list)
    model: str | None = None
    provenance: _Provenance = field(default_factory=_Provenance)


@dataclass
class Hook:
    """Event-triggered script. Claude Code native; falls back per-adapter elsewhere."""
    event: HookEvent
    matcher: dict = field(default_factory=dict)
    script_path: str = ""
    script_body: str = ""
    fallback: FallbackStrategy = "instruction"
    provenance: _Provenance = field(default_factory=_Provenance)


@dataclass
class MCPServer:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    provenance: _Provenance = field(default_factory=_Provenance)


@dataclass
class Policy:
    block_paths: list[str] = field(default_factory=list)
    allowed_tools_per_agent: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Project:
    name: str
    language: str = ""
    stack: list[str] = field(default_factory=list)
    memory: list[MemoryBlock] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    commands: list[Command] = field(default_factory=list)
    agents: list[Agent] = field(default_factory=list)
    hooks: list[Hook] = field(default_factory=list)
    mcp_servers: list[MCPServer] = field(default_factory=list)
    policy: Policy = field(default_factory=Policy)


@dataclass
class RenderReport:
    """What an adapter did. Surfaced to the user so they know what got dropped."""
    target: str
    files_written: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
