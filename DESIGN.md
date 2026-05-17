# agent-init — Design Doc

A generic CLI that materializes agent configurations (`.claude/`, `.github/`, Cursor rules, etc.) from a **single source-of-truth manifest** describing your SDLC. Author once in your own vocabulary; ship to every coding agent your team uses.

---

## 1. The problem in one paragraph

Every coding agent has its own config surface — Claude Code wants `.claude/{CLAUDE.md, agents/, skills/, commands/, hooks/, settings.json}`, Copilot wants `.github/{copilot-instructions.md, instructions/*.instructions.md, prompts/*.prompt.md, agents/*.agent.md, skills/*/SKILL.md}`, Cursor wants `.cursor/rules/*.mdc`, and so on. The *content* (your code review rules, your test conventions, your release checklist) is 90% the same; only the **shape, filenames, and frontmatter** differ. Today teams either pick one tool and lock in, or hand-maintain three parallel trees that drift.

`agent-init` turns SDLC policy into a build target. You author one manifest; the CLI renders idiomatic configs for each agent.

## 2. Mental model

Three layers, strictly separated:

```
┌─────────────────────────────────────────────────────────────┐
│  SOURCE LAYER     authored by humans / pulled from org      │
│  ──────────────────────────────────────────────────────     │
│  agent-init.yaml          ← project manifest                │
│  rules/*.md               ← human-authored playbooks        │
│  org-defaults/ (git)      ← shared standards                │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  IR (Intermediate Representation)                           │
│  ──────────────────────────────────────────────────────     │
│  Normalized in-memory model:                                │
│    Project { agents[], skills[], commands[],                │
│              hooks[], rules[], memory[], mcpServers[] }     │
│  All adapters consume IR. No adapter sees source files.     │
└─────────────────────────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
│  ADAPTER LAYER   │ │              │ │              │
│  claude-code     │ │  copilot     │ │  cursor      │
│  → .claude/      │ │  → .github/  │ │  → .cursor/  │
└──────────────────┘ └──────────────┘ └──────────────┘
```

The IR is the contract. Adding a new agent target = writing one adapter. Changing where rules come from = writing one source loader. The two never touch each other.

## 3. What goes in the manifest

`agent-init.yaml` is the entry point. It's intentionally small — it points at the rules, names the targets, and sets policy.

```yaml
# agent-init.yaml
version: 1
project:
  name: payments-service
  language: kotlin
  stack: [spring-boot, postgres, kafka]

# Where rules come from. Loaded in order; later sources override earlier.
sources:
  - type: git
    url: github.com/acme/sdlc-standards
    ref: v2.3.1
    path: kotlin-backend/
  - type: local
    path: ./rules/

# Which agent surfaces to generate.
targets:
  - claude-code      # → .claude/
  - copilot          # → .github/
  # - cursor         # → .cursor/

# Optional: cross-cutting policy.
policy:
  secrets:
    block_paths: [".env*", "**/credentials.json"]
  allowed_tools:
    code-reviewer: [Read, Grep, Glob]   # restrict subagent tools
  mcp_servers:
    - name: jira
      command: npx
      args: ["-y", "@atlassian/mcp-jira"]
```

The `sources` section is the interesting bit. Rules can live anywhere — a git repo of org standards, a local folder of playbooks, eventually a registry. They get composed in order, so org defaults set the baseline and per-project files override.

## 4. The SDLC primitives

These are the things the manifest can declare, and the IR carries. Each maps differently per target.

| Primitive | Purpose | Claude Code | Copilot |
|---|---|---|---|
| **memory** | Always-on context | `CLAUDE.md` | `.github/copilot-instructions.md` |
| **rule** | Path-scoped behavior | `.claude/rules/*.md` referenced from `CLAUDE.md` | `.github/instructions/*.instructions.md` with `applyTo` |
| **skill** | Auto-activated workflow | `.claude/skills/<name>/SKILL.md` | `.github/skills/<name>/SKILL.md` (same standard!) |
| **command** | User-triggered slash command | `.claude/commands/<name>.md` | `.github/prompts/<name>.prompt.md` |
| **agent** | Specialist subagent | `.claude/agents/<name>.md` | `.github/agents/<name>.agent.md` |
| **hook** | Deterministic event handler | `.claude/settings.json` → `hooks` + scripts | No native equivalent — emits a GH Actions workflow as fallback |
| **mcp_server** | External tool connector | `.mcp.json` | `.vscode/mcp.json` |

Two important things to know, both verified against current docs:

1. **`SKILL.md` is a shared open standard.** A skill written once works in Claude Code, Copilot CLI, GitHub's coding agent, and likely more. So the `skills/` primitive often passes through identically.
2. **Hooks are Claude-Code-specific.** Copilot has no equivalent for `PreToolUse`/`PostToolUse` shell scripts. The adapter degrades gracefully — it either emits a GitHub Actions workflow that does the equivalent at PR time, or it emits a `policy.md` instruction the agent should self-enforce. You declare the hook once; each adapter decides how to honor it.

## 5. The IR

```python
# src/core/ir.py — sketched, not full
@dataclass
class Project:
    name: str
    language: str
    stack: list[str]
    memory: list[MemoryBlock]      # always-on context
    rules: list[Rule]              # path-scoped
    skills: list[Skill]            # auto-activated
    commands: list[Command]        # /slash-invoked
    agents: list[Agent]            # subagent specialists
    hooks: list[Hook]              # event scripts
    mcp_servers: list[MCPServer]
    policy: Policy

@dataclass
class Rule:
    id: str
    description: str
    apply_to: list[str]            # glob patterns, e.g. ["**/*.test.ts"]
    body: str                      # markdown body
    exclude_agents: list[str]      # adapters can honor or ignore

@dataclass
class Skill:
    name: str
    description: str               # critical — triggers the skill
    body: str
    resources: dict[str, bytes]    # scripts, templates, examples

@dataclass
class Agent:
    name: str
    description: str
    tools: list[str]               # e.g. ["Read", "Grep", "Glob"]
    model: str | None
    body: str

@dataclass
class Hook:
    event: str                     # PreToolUse | PostToolUse | Stop | SessionStart
    matcher: dict                  # e.g. {"tool": "Edit", "path_glob": "**/*.py"}
    script_path: str               # relative to package
    script_body: str               # so we can write it out
    fallback: str                  # "github-action" | "instruction" | "skip"
```

Adapters consume this; sources produce it.

## 6. Adapter contract

```python
# src/core/adapter.py
class Adapter(Protocol):
    name: str                                       # "claude-code"
    target_dir: str                                 # ".claude"

    def render(self, project: Project, out: Path) -> RenderReport:
        """Materialize the IR into the target's config layout."""

    def validate(self, out: Path) -> list[ValidationError]:
        """Read back the rendered tree and confirm it's valid."""
```

Each adapter is ~200 lines. It walks the IR, emits files with the right frontmatter, and reports what it dropped (e.g. "copilot does not support hooks; emitted GHA workflow instead").

## 7. Lifecycle / commands

```
agent-init init           # create agent-init.yaml + rules/ skeleton, interactive
agent-init pull           # fetch source repos (git, registry) into cache
agent-init build          # render all targets; idempotent
agent-init diff           # show what would change without writing
agent-init validate       # lint manifest + rendered output
agent-init eject <target> # stop generating, commit rendered tree as-is
```

`build` is the workhorse. It should be deterministic — same manifest, same output, every time — so it's safe to put in CI as a check (`agent-init build && git diff --exit-code`).

## 8. Safety and the things that bite

A few non-obvious gotchas baked into the design:

**Frontmatter drift.** Claude Code subagents use a different YAML frontmatter shape than Copilot `.agent.md` files. Don't try to share frontmatter — the IR holds canonical fields, each adapter renders its own.

**Path-scoped rules don't work everywhere.** Path-scoped Copilot instructions work in VS Code Chat, the cloud agent, and code review, but **not** in Copilot Chat on GitHub.com. The adapter should warn when a rule has `apply_to` set if the user has the GH.com Chat target enabled.

**Code review reads the base branch.** Copilot's code review agent reads `copilot-instructions.md` from the PR's base branch, not the feature branch. That means if your CI runs `agent-init build` on a feature branch and the file changes, code review on that PR uses the *old* instructions. Document this clearly; it's not a bug.

**Hooks run shell.** Anything in `hooks/` executes on the developer's machine with their permissions. The manifest should declare allowed commands and the CLI should refuse to write hook scripts that contain `curl | sh`-style patterns unless explicitly waived.

**Generated files vs. committed files.** Two valid modes:
- *Generated*: `.claude/` and `.github/` are in `.gitignore`; `agent-init build` runs as part of dev setup or via a git hook. Pros: one source of truth. Cons: contributors who don't run the CLI get nothing.
- *Committed*: render output is committed; CI checks `agent-init build` produces no diff. Pros: zero-config for contributors. Cons: noisier PRs.

Default to **committed + CI check**. That's the lower-friction mode for teams.

## 9. Shipping plan

A pragmatic v0 → v1 → v2:

**v0 (one weekend)** — Python CLI, single adapter (`claude-code`), single source type (`local`). Manifest supports `memory`, `rules`, `skills`. No agents, no hooks, no MCP. Just prove the IR holds up.

**v1 (one month)** — Add `copilot` adapter, `agents`, `commands`, `hooks` (with GHA fallback for Copilot), `mcp_servers`. Add `git` source. Add `agent-init diff` and a JSON-schema-validated manifest.

**v2 (later)** — Cursor + Windsurf adapters. Org-level source via a private registry. A `agent-init lint` that checks the rules themselves for quality (length, conflicts, missing examples). Telemetry hooks so you can see which skills actually fire in production.

## 10. What this isn't

- It's not a runtime. Once `build` completes, the CLI is out of the picture; each agent reads its own files normally.
- It's not opinionated about your SDLC. The primitives are generic; the *content* is yours.
- It's not a policy enforcer. Hooks can enforce things at the agent boundary, but real enforcement still belongs in CI.
