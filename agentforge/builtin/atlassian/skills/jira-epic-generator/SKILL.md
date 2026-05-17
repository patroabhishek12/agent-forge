---
name: jira-epic-generator
description: >
  Triggered when a user says "create Jira tickets from this requirement",
  "generate epics and stories", "break down this feature into Jira issues",
  or provides a requirements doc / PRD and asks to populate Jira.
  Produces a full Epic → Story → Subtask hierarchy covering the entire feature lifecycle.
---

## MCP tools used
- `jira.create_issue`, `jira.update_issue`, `jira.get_project`

## Procedure

1. **Load requirements**
   - If the user provides a Confluence page URL, fetch the page body via the
     Confluence MCP (`confluence.get_page`).
   - If the user pastes text or a file path, read that content directly.
   - Extract: goal, functional requirements, non-functional requirements, out-of-scope items.

2. **Discover Jira project**
   - Use `jira.get_project` with the project key supplied by the user (or ask for it).
   - Confirm issue types available: Epic, Story, Subtask (or Sub-task), Bug.

3. **Decompose into Epics**
   - Group requirements into functional areas — each becomes one Epic.
   - For each Epic draft: `summary`, `description` (include goal + acceptance criteria),
     estimated size (story points as a rough label), and `labels` from the feature domain.
   - Show the user the Epic list and ask for approval before creating.

4. **Create Epics in Jira**
   - Call `jira.create_issue` for each approved Epic.
   - Record the returned issue key (e.g. `PROJ-10`).

5. **Generate Stories per Epic**
   - For each Epic, produce Stories covering distinct user journeys.
   - Each Story must include:
     - `summary`: "As a <persona>, I want <action> so that <value>"
     - `description`: background + acceptance criteria (Given/When/Then format)
     - `story_points`: estimated
     - `parent` / `epic_link`: the parent Epic key
   - Show Story drafts grouped by Epic; confirm before creating.

6. **Create Stories in Jira**
   - Call `jira.create_issue` for each Story, linking to the parent Epic.

7. **Generate Subtasks per Story**
   - Break each Story into technical Subtasks (API endpoint, DB migration, unit tests,
     integration test, docs update).
   - Each Subtask: `summary`, `assignee` (leave blank), `story_points: 1-3`.
   - Create subtasks via `jira.create_issue` with `issuetype: Subtask` and
     `parent: <story key>`.

8. **Transition new issues to Backlog**
   - Call `jira.update_issue` to set status to `Backlog` / `To Do` on each created issue.

9. **Report**
   - Print a tree: Epic → Stories → Subtasks with Jira keys and links.
   - Offer to also create a Confluence page summarising the epic scope
     (triggers `confluence-adr` skill if accepted).
