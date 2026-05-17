---
name: codegen-from-ticket
description: >
  Triggered when a user says "implement this story", "code up this Jira ticket",
  "start on PROJ-123", or pastes a Jira issue URL or key. Reads the ticket,
  locates the right service in the repo index, and scaffolds the implementation.
---

## Procedure

1. **Resolve the ticket**
   - If a Jira key or URL is provided, use the Jira MCP tool `get_issue` to fetch
     summary, description, acceptance criteria, and linked subtasks.
   - If only a description is pasted, skip the Jira fetch; treat the text as the spec.

2. **Load repo context**
   - Read `.claude/knowledge/repo-index.yaml` (or `.copilot/knowledge/repo-index.yaml`).
   - If it does not exist, run the `discover-repo` skill first.
   - Match the ticket's component label or text against service names in the index to
     identify the target service.

3. **Select language conventions**
   - Inspect the target service's `language` field from the repo index.
   - Load the corresponding language rule (`lang-java`, `lang-rust`, `lang-go`, etc.)
     to apply naming and structural conventions automatically.

4. **Plan the implementation**
   - Break acceptance criteria into discrete change units (new file, modified method,
     migration, test case).
   - Present the plan as a numbered checklist and ask the user to confirm before writing.

5. **Generate code**
   - Scaffold each change unit in turn:
     - Create new files in the correct package/module directory.
     - Follow the layer conventions for the detected language (controller → service →
       repository, handler → service → store, etc.).
     - Add unit test stubs alongside each new file.
   - Do not commit — leave the working tree dirty for the user to review.

6. **Link back to Jira**
   - After generating, print the Jira issue key and a reminder to transition the issue
     to "In Progress" via the `jira-epic-generator` skill's transition flow if needed.
