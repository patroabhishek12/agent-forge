"""
Merge engine.

Sources are loaded in order. For each primitive type, we apply one of two
policies, with `id`/`name` as the dedup key:

  APPEND   — all instances kept (memory, hooks)
  OVERRIDE — later instances mask earlier ones (rules, skills, commands, agents, mcp_servers)

Provenance is preserved on every survivor and records what it overrode.
"""
from __future__ import annotations
from .ir import Project, MemoryBlock, Hook


def merge_into(target: Project, addition: Project) -> None:
    """Merge `addition` into `target` in place. Call once per source, in order."""

    # APPEND: memory + hooks
    target.memory.extend(addition.memory)
    target.hooks.extend(addition.hooks)

    # OVERRIDE by id/name
    _override(target.rules,    addition.rules,    key=lambda r: r.id)
    _override(target.skills,   addition.skills,   key=lambda s: s.name)
    _override(target.commands, addition.commands, key=lambda c: c.name)
    _override(target.agents,   addition.agents,   key=lambda a: a.name)
    _override(target.mcp_servers, addition.mcp_servers, key=lambda s: s.name)

    # Stack metadata: project name from last source wins; languages/stack union.
    if addition.name and addition.name != "unnamed":
        target.name = addition.name
    if addition.language:
        target.language = addition.language
    for s in addition.stack:
        if s not in target.stack:
            target.stack.append(s)

    # Policy: project policy wins on conflict; otherwise union block_paths.
    for p in addition.policy.block_paths:
        if p not in target.policy.block_paths:
            target.policy.block_paths.append(p)
    target.policy.allowed_tools_per_agent.update(
        addition.policy.allowed_tools_per_agent
    )


def _override(existing: list, incoming: list, key) -> None:
    """In-place override: incoming items replace existing ones with the same key.
    The replacement records the override in its provenance.
    """
    by_key = {key(item): i for i, item in enumerate(existing)}
    for new in incoming:
        k = key(new)
        if k in by_key:
            old = existing[by_key[k]]
            new.provenance.overrode.append(old.provenance.source or "<unknown>")
            existing[by_key[k]] = new
        else:
            by_key[k] = len(existing)
            existing.append(new)
