---
title: Project conventions
priority: 10
---
- Trunk-based development. PRs merge to `main` via squash.
- All endpoints require OpenAPI annotations.
- Database migrations go through Flyway; never edit committed migrations.
- Logs use structured JSON via Logback's `LogstashEncoder`.
