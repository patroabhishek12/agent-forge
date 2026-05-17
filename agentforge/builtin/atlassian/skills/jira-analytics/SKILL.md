---
name: jira-analytics
description: >
  Triggered when a user asks for "sprint analytics", "epic progress report",
  "stakeholder summary", "velocity report", "how many bugs are open",
  "show me release health", or any question about project-level Jira metrics.
  Produces a one-stop analytics view suitable for stakeholders.
---

## MCP tools used
- `jira.search_issues`, `jira.get_sprint`, `jira.get_board`

## Procedure

1. **Determine scope**
   - Ask (or infer from context): project key, sprint or date range, and audience
     (engineering team vs. stakeholder / executive).

2. **Collect epic-level progress**
   - Search all Epics in the project:
     `issuetype = Epic ORDER BY created DESC`
   - For each Epic fetch child stories; compute:
     - total story points (planned)
     - completed story points (Done/Closed)
     - percentage complete
     - number of open bugs linked to this Epic

3. **Collect sprint metrics** (if board/sprint available)
   - Fetch the active sprint via `jira.get_sprint`.
   - Compute: committed points, completed points, scope change (stories added/removed
     mid-sprint), carry-over count.

4. **Bug health**
   - Count open bugs by severity (Critical, Major, Minor) and by component.
   - Compute bug arrival rate vs. resolution rate over the last 30 days.
   - Flag any Critical bugs unassigned or stale > 5 days.

5. **Cycle time**
   - For issues closed in the date range, compute median time from "In Progress" to
     "Done" using changelog data.

6. **Render the report**

   ### Stakeholder view (audience = stakeholder)
   ```
   Epic Progress
   ─────────────────────────────────────────────
   PROJ-10 User Auth        ████████░░  80%  (16/20 pts)
   PROJ-25 Payments         ████░░░░░░  40%  ( 8/20 pts)

   Open Bugs: 3 Critical  |  8 Major  |  12 Minor
   Active Sprint: Sprint 14 — 62% complete (2 days left)
   ```

   ### Engineering view (audience = engineering)
   - Full table with story points, assignees, cycle time, carry-over.
   - Bug breakdown by component with owners.

7. **Export option**
   - Offer to publish the report as a Confluence page under the project space.
   - If accepted, invoke the `confluence-adr` skill's page-creation flow with the
     report content.
