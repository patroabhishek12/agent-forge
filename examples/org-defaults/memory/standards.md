---
title: Engineering Standards (org-wide)
priority: 1
---
- All PRs require one approval from a non-author.
- No force-pushes to `main` or `release/*`.
- Secrets are never committed; use the vault. CI fails on any match of the secrets regex.
- Every service owns an on-call rotation and a runbook in `docs/runbook.md`.
