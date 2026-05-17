---
name: pr-review
description: Use when reviewing a pull request or preparing one for merge. Checks tests, migrations, API contracts, and observability.
---

# Pull Request Review

Walk through these checks in order. Stop and report at the first that fails.

1. **Tests** — every changed `*.kt` under `src/main` has a corresponding test change or a justification in the PR body.
2. **Migrations** — any new file under `src/main/resources/db/migration` is forward-only and idempotent. No edits to existing migrations.
3. **API contracts** — every new endpoint has `@Operation` and `@ApiResponse` annotations.
4. **Observability** — every new code path emits at least one structured log at INFO and adds a counter/timer if it crosses an external boundary.
5. **Secrets** — diff contains no values matching `[A-Z_]+_KEY|TOKEN|SECRET`.

Output: a markdown report with one line per check (✅ / ❌ + one sentence).
