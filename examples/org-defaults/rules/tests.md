---
id: tests
description: Default testing conventions (org-wide)
apply_to: ["**/test/**"]
---
- Tests must be deterministic; no real network, no real clocks.
- One assertion per test where reasonable.
- Cover both happy path and at least one error path.
