---
title: Atlassian Integration Context
priority: 5
---

## Jira conventions

- **Epic** — large feature slice, multiple sprints. Label with `type: Epic`.
- **Story** — user-facing unit of value, fits in one sprint. Child of an Epic.
- **Subtask** — technical breakdown inside a Story (≤ 1 day each).
- **Bug** — defect with reproduction steps, severity, and affected version.

Story-point scale used by default: 1, 2, 3, 5, 8, 13.
Always link stories to their parent Epic using the "Epic Link" field (or `parent` in
next-gen projects).

## Confluence conventions

- ADRs live under the space page tree: **Engineering > Architecture > ADRs**.
- ADR title format: `ADR-NNN: <Decision title>`.
- Required sections: Status, Context, Decision, Consequences, Alternatives Considered.
- PlantUML diagrams should use `@startuml / @enduml` inside a Confluence code block
  macro with language set to `plantuml`.
