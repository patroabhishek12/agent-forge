# agent-init

Generate `.claude/` and `.github/` agent configs for an entire SDLC from one source-of-truth manifest. Org defaults layer with per-project overrides; provenance is tracked. Ships with a **built-in SDLC skills library** covering Jira, Confluence, GitHub, Bitbucket, and language-specific code generation — ready to use out of the box.

```bash
pip install agent-init

agent-init init           # interactive wizard — detects existing configs, selects bundles
agent-init list-bundles   # show all available built-in SDLC bundles
agent-init build          # render targets idempotently
agent-init diff --check   # CI gate: exit 1 if output is stale
agent-init validate       # schema-check the manifest
```

---

## Logging

The CLI emits DEBUG logs by default to make it easy to trace what it is doing.
Logs follow a standard format:

```
YYYY-MM-DDTHH:MM:SS±ZZZZ LEVEL module: message
```

Examples include source resolution, manifest loading, render targets, and diff
decisions.

---

## What it does

Every coding agent has its own config surface. Claude Code wants `.claude/{CLAUDE.md, agents/, skills/, commands/, hooks/, settings.json}`; Copilot wants `.github/{copilot-instructions.md, instructions/*.instructions.md, prompts/*.prompt.md, agents/*.agent.md, skills/*/SKILL.md}`. The *content* — your code review rules, your test conventions, your release checklist — is 90% the same; only the shape, filenames, and frontmatter differ.

`agent-init` turns SDLC policy into a build target. You author one manifest; the CLI renders idiomatic configs for each agent. It also ships a **built-in stdlib of SDLC skills** covering the full feature lifecycle: requirement ingestion → epic/story generation → code scaffolding → PR creation → CI pipelines → architecture documentation.

---

## How it works

Three strictly separated layers:

```
SOURCES              →    IR (Project)           →    ADAPTERS
local, git, builtin       memory, rules,              claude-code → .claude/
                          skills, commands,            copilot     → .github/
                          agents, hooks,
                          mcp_servers
```

The IR is the contract. Sources produce a `Project`; adapters consume it. Neither sees the other's format.

### Source types

| Type | Description |
|------|-------------|
| `local` | Directory on disk (`./rules/`) |
| `git` | Shallow-cloned, ref-pinned remote repo |
| `builtin` | Named bundle from the built-in SDLC library (ships with the package) |

### Sources merge in declared order

```yaml
sources:
  - type: builtin
    bundle: core          # lowest priority — stdlib baseline

  - type: builtin
    bundle: atlassian     # Jira + Confluence skills

  - type: git
    url: github.com/acme/sdlc-standards
    ref: v2.3.1

  - type: local
    path: ./rules         # highest priority — project overrides
```

Earlier source = lower priority. Project-local rules override org defaults by `id`/`name`.

| Primitive | Merge policy |
|-----------|--------------|
| `memory` | Append — all blocks render, sorted by `priority` |
| `hooks` | Append — multiple per event are valid |
| `rules` | Override by `id` |
| `skills` | Override by `name` |
| `commands` | Override by `name` |
| `agents` | Override by `name` |
| `mcp_servers` | Override by `name` |

Run `agent-init build --show-provenance` to see which source each surviving element came from and what it overrode.

---

## Built-in SDLC bundle library

The stdlib ships **9 opt-in bundles**, selectable during `agent-init init` or declared directly in the manifest. Each bundle brings skills, rules, agents, and MCP server declarations appropriate for its domain.

```
agent-init list-bundles
```

```
  architect      Solution architect agent (PlantUML, ADRs, C4 diagrams)
  atlassian      Jira (epics/stories/bugs/analytics) + Confluence ADRs
  bitbucket      Bitbucket PR workflow + Bitbucket Pipelines CI
  core           Repo discovery + code generation from Jira tickets
  github         GitHub PR workflow + GitHub Actions CI
  lang-go        Go conventions + Go code scaffolding
  lang-java      Java conventions (Spring/Quarkus) + Java code scaffolding
  lang-rust      Rust conventions + Rust code scaffolding
  ui-react       React/TypeScript conventions + component scaffolding
```

### `core` — Repo discovery and ticket-driven codegen

| Skill | Trigger phrases | What it does |
|-------|----------------|--------------|
| `discover-repo` | "map the repo", "index the project", "fill the knowledge base" | Walks the source tree, detects mono/polyrepo topology, enumerates services, writes `repo-index.yaml` to `.claude/knowledge/` |
| `codegen-from-ticket` | "implement this story", "start on PROJ-123", paste a Jira URL | Reads the ticket, matches to the right service via `repo-index.yaml`, selects language conventions, plans the implementation, scaffolds code + test stubs |

### `atlassian` — Full Jira + Confluence lifecycle

Requires: `JIRA_BASE_URL`, `JIRA_API_TOKEN`, `JIRA_USER_EMAIL`, `CONFLUENCE_BASE_URL`, `CONFLUENCE_API_TOKEN`, `CONFLUENCE_USER_EMAIL`.

MCP servers registered automatically: `jira`, `confluence`.

| Skill | Trigger phrases | What it does |
|-------|----------------|--------------|
| `jira-epic-generator` | "create Jira tickets from this requirement", "generate epics and stories", "break down this feature" | Reads a requirements doc or Confluence page; decomposes into Epics → Stories → Subtasks; creates them in Jira with acceptance criteria and story points |
| `jira-bug-tracer` | "trace this bug", "show me the lifecycle of PROJ-NNN" | Fetches bug + all linked issues, reads changelog for status history, searches for related bugs, produces a full timeline and root-cause summary |
| `jira-analytics` | "sprint analytics", "epic progress report", "stakeholder summary" | Aggregates epic completion, sprint velocity, bug health (by severity/component), cycle time; renders a stakeholder view or detailed engineering table; optionally publishes to Confluence |
| `confluence-adr` | "write an ADR", "document this architecture decision", "publish a decision record" | Sequences ADR numbers, generates PlantUML diagrams (C4Context/Container or sequence), composes the ADR page, creates/updates the Confluence page, links back to the Jira Epic |

### `github` — PR workflow and CI

Requires: `GITHUB_TOKEN`.

MCP servers registered automatically: `github`.

| Skill | Trigger phrases | What it does |
|-------|----------------|--------------|
| `github-pr-workflow` | "open a PR", "create a pull request", "submit this for review" | Stages commits (Conventional Commits format), pushes the branch, composes a structured PR description with Jira refs, creates the PR via MCP |
| `github-actions-ci` | "add CI", "set up GitHub Actions", "create a workflow" | Detects language and build tool, generates an idiomatic `.github/workflows/<name>-ci.yml`, handles secrets wiring |

### `bitbucket` — PR workflow and Pipelines

Requires: `BITBUCKET_URL`, `BITBUCKET_USERNAME`, `BITBUCKET_APP_PASSWORD`.

MCP servers registered automatically: `bitbucket`.

| Skill | Trigger phrases | What it does |
|-------|----------------|--------------|
| `bitbucket-pr-workflow` | "open a PR on Bitbucket", "push my changes and raise a PR" | Same flow as the GitHub skill; uses Bitbucket smart-commit syntax to auto-transition Jira issues |
| `bitbucket-pipelines-ci` | "add Bitbucket Pipelines", "create a bitbucket-pipelines.yml" | Generates a `bitbucket-pipelines.yml` with build, test, and deploy steps adapted to the detected stack |

### `lang-java` — Java code conventions and scaffolding

Always-on rule applied to `**/*.java`:
- Spring/Quarkus layering enforced: `controller → service → repository → model/dto`
- Naming, line length, `Optional<T>`, records, OpenAPI annotations
- Testing: JUnit 5 + Mockito, `@SpringBootTest` integration tests, 80% coverage target
- Error handling: `@ControllerAdvice` + problem-detail JSON

Skill `java-codegen` — triggered by "scaffold a Java service", "generate a Spring controller", "add a repository for \<entity\>":
generates Entity → Repository → Service → Controller → DTOs → test stub, bottom-up.

### `lang-rust` — Rust code conventions and scaffolding

Always-on rule applied to `**/*.rs`:
- Hexagonal layout: `domain/ ports/ adapters/ api/`
- Error handling with `thiserror`, no `.unwrap()` in library code
- Tokio async runtime, sync domain layer, `mockall` for port mocking
- `rustfmt` + `clippy -D warnings` enforced

Skill `rust-codegen` — triggered by "scaffold a Rust service", "add an axum handler":
generates domain struct → port trait → adapter (sqlx) → axum handler → unit test module.

### `lang-go` — Go code conventions and scaffolding

Always-on rule applied to `**/*.go`:
- Standard Go layout: `cmd/ internal/{domain,port,adapter,config}/ pkg/`
- Error wrapping with `fmt.Errorf("…: %w", err)`, no silent `_`
- `context.Context` as first param on all I/O functions
- `golangci-lint`, table-driven tests, `gomock` or `mockery`

Skill `go-codegen` — triggered by "scaffold a Go service", "add a handler", "create a repository interface":
generates domain type → port interface → postgres adapter (pgx) → HTTP handler → test file.

### `ui-react` — React/TypeScript conventions and scaffolding

Always-on rule applied to `**/*.tsx`, `**/*.ts`:
- Feature-slice structure: `features/<feature>/{components,hooks,api}/`
- React Query for server state, Zustand for client state, no manual fetch in components
- Strict TypeScript — no `any`, `satisfies` operator, named exports for shared components
- Vitest + React Testing Library, Playwright for E2E, 75% coverage target on `features/`

Skill `react-codegen` — triggered by "create a React component", "scaffold a feature", "build the UI for this story":
generates types → API layer (React Query) → component → test; registers route if it's a page.

### `architect` — Solution architect agent

Specialist subagent invoked by "design the architecture", "create an ADR", "draw a system diagram":
- Reads Jira Epics and Confluence pages for context
- Analyses architectural concerns (communication, storage, deployment, auth, observability) with trade-off tables
- Generates PlantUML C4 Context, C4 Container, and sequence diagrams
- Publishes ADRs to Confluence via the `confluence-adr` skill
- Offers to create Jira infrastructure stories from the design

---

## Manifest reference

```yaml
version: 1

project:
  name: payments-service
  language: kotlin
  stack: [spring-boot, postgres, kafka]

sources:
  # Built-in SDLC bundles (lowest priority, baseline)
  - type: builtin
    bundle: core

  - type: builtin
    bundle: atlassian

  - type: builtin
    bundle: lang-java

  # Org-wide standards from a git repo
  - type: git
    url: github.com/acme/sdlc-standards
    ref: v2.3.1
    path: kotlin-backend/     # optional subpath

  # Project-local overrides (highest priority)
  - type: local
    path: ./rules

targets:
  - claude-code   # → .claude/
  - copilot       # → .github/

policy:
  secrets:
    block_paths: [".env*", "**/credentials.json"]
  allowed_tools:
    code-reviewer: [Read, Grep, Glob]   # restrict subagent tools
  mcp_servers:
    # Inline MCP declaration (alternative to bundle's mcp.yaml)
    - name: postgres
      command: npx
      args: ["-y", "@modelcontextprotocol/server-postgres"]
      env:
        DATABASE_URL: "${DATABASE_URL}"
```

---

## Source directory layout

Each source (local, git, or built-in bundle) follows the same on-disk convention:

```
<source-root>/
├── memory/           ← *.md  —  always-on context blocks
├── rules/            ← *.md  —  path-scoped behavior rules
├── skills/
│   └── <name>/
│       └── SKILL.md  ← frontmatter (name, description) + procedure body
├── commands/         ← *.md  —  /slash-command definitions
├── agents/           ← *.md  —  specialist subagent definitions
├── hooks/
│   └── hooks.yaml    ← event→script mappings
└── mcp.yaml          ← MCP server declarations for this bundle/source
```

### Memory file format

```markdown
---
title: Team Standards
priority: 10
---

Always run `./scripts/check.sh` before committing.
```

### Rule file format

```markdown
---
id: java-conventions
description: Java coding conventions
apply_to: ["**/*.java"]
exclude_agents: []
---

## Naming
PascalCase for classes, camelCase for methods ...
```

### Skill file format

```markdown
---
name: security-review
description: >
  Triggered when the user asks to review security, audit dependencies,
  or check for vulnerabilities.
---

## Procedure
1. Run `./scripts/audit.sh`
2. Check OWASP Top 10 against current code ...
```

### Agent file format

```markdown
---
name: code-reviewer
description: Specialist code review subagent
tools: [Read, Grep, Glob]
model: claude-opus-4-5
---

You are a senior engineer performing a code review ...
```

---

## SDLC primitives

| Primitive | Purpose | Claude Code output | Copilot output |
|-----------|---------|-------------------|----------------|
| `memory` | Always-on context | `CLAUDE.md` | `.github/copilot-instructions.md` |
| `rule` | Path-scoped behavior | `.claude/rules/*.md` | `.github/instructions/*.instructions.md` |
| `skill` | Auto-activated workflow | `.claude/skills/<name>/SKILL.md` | `.github/skills/<name>/SKILL.md` |
| `command` | User-triggered slash command | `.claude/commands/<name>.md` | `.github/prompts/<name>.prompt.md` |
| `agent` | Specialist subagent | `.claude/agents/<name>.md` | `.github/agents/<name>.agent.md` |
| `hook` | Event-triggered script | `.claude/settings.json` + scripts | GHA workflow or instruction fallback |
| `mcp_server` | External tool connector | `.mcp.json` | `.vscode/mcp.json` |

`SKILL.md` is an open standard shared by Claude Code and Copilot — skills written once work in both.

Hooks are Claude Code-only. The Copilot adapter degrades each hook to a `github-action` (emits a GHA workflow), `instruction` (self-enforce text appended to `copilot-instructions.md`), or `skip` — declared per hook.

---

## The knowledge folder

The `discover-repo` skill (from the `core` bundle) writes a structured index at runtime:

```
.claude/knowledge/repo-index.yaml     # or .copilot/knowledge/
```

```yaml
topology: monorepo
scanned_at: 2026-05-17T08:00:00Z
services:
  - name: payments-api
    language: java
    path: services/payments-api
    entry_points: [src/main/java/com/acme/PaymentsApp.java]
    exposed_ports: [8080]
    dependencies: [spring-boot-starter-web, spring-data-jpa]
shared_libs:
  - name: common-utils
    path: libs/common-utils
ci_files: [.github/workflows/ci.yml]
```

Other skills (`codegen-from-ticket`, language codegen skills) read this index to locate the right service and apply the correct conventions automatically.

---

## Project layout

```
agent_init/
├── core/
│   ├── ir.py            # Project + all primitives, provenance on every element
│   ├── merge.py         # append vs override-by-key, per primitive type
│   └── adapter.py       # Adapter protocol + registry
├── adapters/
│   ├── claude_code.py   # .claude/ + CLAUDE.md + .mcp.json
│   └── copilot.py       # .github/ + .vscode/mcp.json + hook fallbacks
├── sources/
│   └── loader.py        # local + git + builtin resolvers; mcp.yaml convention
├── schema/
│   ├── manifest.schema.json  # JSON Schema (draft 2020-12)
│   └── __init__.py           # validator with friendly $pointer errors
├── builtin/                  # Built-in SDLC bundle library
│   ├── core/                 # Repo discovery, ticket-driven codegen
│   ├── atlassian/            # Jira + Confluence skills + mcp.yaml
│   ├── github/               # GitHub PR + Actions CI + mcp.yaml
│   ├── bitbucket/            # Bitbucket PR + Pipelines + mcp.yaml
│   ├── lang-java/            # Java rules + codegen skill
│   ├── lang-rust/            # Rust rules + codegen skill
│   ├── lang-go/              # Go rules + codegen skill
│   ├── ui-react/             # React/TS rules + codegen skill
│   └── architect/            # Solution architect agent
├── wizard.py            # Interactive `init` with bundle selection
├── diff.py              # Render-to-tempdir + unified diff
└── cli.py               # init, build, diff, validate, list-bundles

examples/
├── org-defaults/         # Example org-wide rules repo
└── sample-project/       # Consumes org defaults with local overrides
    ├── agent-init.yaml
    └── rules/

tests/
├── test_merge.py          # Merge engine invariants
├── test_schema.py         # Manifest validation
├── test_e2e.py            # End-to-end sample-project rendering
└── test_builtin_bundles.py  # Bundle loading, skill/agent/rule content, MCP servers
```

---

## Demo — merge in action

In `examples/`, the org defines `tests`, `secrets`, and `security-review`. The project re-defines `tests` (with Kotlin/MockK specifics) and adds `pr-review` and `code-reviewer`. After `agent-init build --show-provenance`:

```
rule:secrets           ← local:../org-defaults
rule:tests             ← local:./rules   (overrode: local:../org-defaults)
skill:security-review  ← local:../org-defaults
skill:pr-review        ← local:./rules
agent:code-reviewer    ← local:./rules
```

When the `atlassian` bundle is also included:

```
skill:jira-epic-generator  ← builtin:atlassian
skill:confluence-adr       ← builtin:atlassian
mcp_server:jira            ← builtin:atlassian
mcp_server:confluence      ← builtin:atlassian
rule:java-conventions      ← builtin:lang-java   (overrode: builtin:atlassian — no conflict)
```

---

## Quick-start with bundles

```bash
# 1. Install
pip install agent-init

# 2. Initialise — wizard asks which bundles to include
agent-init init
# > Which bundles to include? (comma-separated, or 'none') [core]: core, atlassian, lang-java

# 3. Set credentials for Atlassian MCP servers (or add to .env)
export JIRA_BASE_URL=https://acme.atlassian.net
export JIRA_API_TOKEN=...
export JIRA_USER_EMAIL=you@acme.com
export CONFLUENCE_BASE_URL=https://acme.atlassian.net/wiki
export CONFLUENCE_API_TOKEN=...
export CONFLUENCE_USER_EMAIL=you@acme.com

# 4. Build and commit the rendered configs
agent-init build
git add .claude/ .github/ && git commit -m "chore: regenerate agent configs"

# 5. Now in Claude Code or Copilot — skills activate automatically
# "Map the repo"              → discover-repo runs, writes .claude/knowledge/repo-index.yaml
# "Start on PROJ-42"          → codegen-from-ticket reads the ticket and scaffolds code
# "Generate epics for this PRD" → jira-epic-generator creates the Epic → Story → Subtask tree
```

---

## CI gate

```yaml
# .github/workflows/agent-config.yml
- name: Check agent configs are up to date
  run: agent-init diff --check
```

Exits non-zero if any target file would change — same pattern as `terraform plan` or `prettier --check`.

---

## Development

```bash
make dev        # editable install + dev deps
make test       # pytest
make lint       # ruff
make typecheck  # mypy
```

---

## Roadmap

- `eject <target>` — stop generating and commit current output as authored
- Cursor + Windsurf adapters (same Adapter protocol, ~150 lines each)
- `agent-init lint` — rule quality checks (overly long memory, conflicting rules, vague skill descriptions)
- Service mode — HTTP wrapper over `loader.load` + `adapter.render` for orgs that want a central rendering service
- Additional stdlib bundles: Linear, Notion, GitLab CI, Azure DevOps, Python/FastAPI, .NET

---

## License

MIT.
