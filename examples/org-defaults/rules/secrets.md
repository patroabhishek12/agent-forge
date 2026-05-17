---
id: secrets
description: Never write or echo secrets
apply_to: ["**/*"]
---
- Never paste, log, or commit values matching `[A-Z_]+_(KEY|TOKEN|SECRET|PASSWORD)`.
- When you encounter one in code, replace it with a reference to the vault and flag it in the PR description.
- Test fixtures use `dummy_*` placeholders.
