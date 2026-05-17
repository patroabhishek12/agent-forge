---
name: security-review
description: Use when reviewing code that touches auth, secrets, network boundaries, or data flowing in from users. Applies the org security checklist.
---
# Security review

Walk this checklist for any changed file in scope:

1. **Input validation** — every external input has a schema and a max size.
2. **AuthN/AuthZ** — every protected endpoint checks the caller's identity *and* their permission.
3. **Secrets** — no hardcoded keys, tokens, or passwords; values come from the vault.
4. **Logging** — no PII or secrets in logs; structured fields only.
5. **Dependencies** — any new dependency goes through `osv-scanner` before merge.

Report findings as: file:line — severity — what to change.
