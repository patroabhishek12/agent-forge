---
name: jira-bug-tracer
description: >
  Triggered when a user says "trace this bug", "find the root cause in Jira",
  "show me the full lifecycle of bug PROJ-NNN", "what broke in this release",
  or provides a bug ticket key and asks for investigation context.
---

## MCP tools used
- `jira.get_issue`, `jira.search_issues`, `jira.get_issue_changelog`

## Procedure

1. **Fetch the bug ticket**
   - Call `jira.get_issue` with the supplied key.
   - Extract: summary, description, steps to reproduce, environment, severity,
     priority, affected version(s), fix version, reporter, assignee, created date.

2. **Trace linked issues**
   - Follow all issue links: `is caused by`, `is blocked by`, `duplicates`, `relates to`.
   - Fetch each linked issue recursively (up to depth 2) and build a dependency graph.

3. **Inspect change history**
   - Call `jira.get_issue_changelog` to retrieve status transitions and field changes.
   - Identify: when the bug was first reported, who triaged it, when it moved to
     "In Progress", any reopens.

4. **Search for related bugs**
   - Run `jira.search_issues` with JQL:
     `project = <project> AND issuetype = Bug AND component = <component> AND created >= -90d`
   - List related bugs, noting any patterns (same component, same error string).

5. **Identify the originating story / feature**
   - Search for the Epic or Story whose fix version or sprint overlaps with the
     bug's first occurrence.
   - Report the feature that introduced the regression.

6. **Summarise the full lifecycle**
   - Print a timeline:
     ```
     <date> — Bug filed: <summary>
     <date> — Triaged (priority set to <P>)
     <date> — Assigned to <user>
     <date> — In Progress
     <date> — PR raised: <link if available>
     <date> — Fixed / Closed
     ```

7. **Recommend next steps**
   - If bug is open: suggest assignee based on component ownership.
   - If bug is resolved: confirm fix version is scheduled; check if a regression test
     subtask exists; offer to create one via `jira.create_issue`.
