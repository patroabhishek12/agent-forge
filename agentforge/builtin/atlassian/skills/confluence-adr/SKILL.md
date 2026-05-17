---
name: confluence-adr
description: >
  Triggered when a user says "write an ADR", "document this architecture decision",
  "publish a decision record to Confluence", "create an ADR for <topic>",
  or asks to generate PlantUML diagrams and push them to Confluence.
  Also triggered as a sub-step by jira-epic-generator and jira-analytics.
---

## MCP tools used
- `confluence.create_page`, `confluence.update_page`, `confluence.get_page`
- `confluence.search`

## Procedure

1. **Determine next ADR number**
   - Search Confluence for pages matching `ADR-` in the target space:
     `confluence.search(query="title: ADR- space: <SPACE_KEY>")`
   - Find the highest sequence number; next = max + 1.
   - If no ADRs exist, start at ADR-001.

2. **Gather decision context**
   - Ask the user (or infer from a Jira Epic if provided):
     - What is the problem / context?
     - What decision was made?
     - What were the alternatives considered?
     - What are the consequences (positive and negative)?
   - Current status: Proposed | Accepted | Deprecated | Superseded.

3. **Generate PlantUML diagram (if architectural)**
   - If the decision involves a system interaction, component boundary, or data flow,
     generate a PlantUML diagram:
     - Use `C4Context` or `C4Container` for system-level decisions.
     - Use sequence diagram for protocol/API decisions.
   - Embed the PlantUML source inside a Confluence code block macro.

4. **Compose the ADR page body (Confluence storage format)**

   ```
   ADR-NNN: <Title>
   Status: <Accepted | Proposed | ...>

   ## Context
   <problem statement and forces at play>

   ## Decision
   <the decision taken, written as a positive statement>

   ## Consequences
   ### Positive
   - ...
   ### Negative / Trade-offs
   - ...

   ## Alternatives Considered
   | Alternative | Why rejected |
   |-------------|--------------|
   | ...         | ...          |

   ## Related
   - Jira Epic: <link>
   - Supersedes: <ADR-NNN if applicable>
   ```

5. **Create or update the page**
   - Parent page: `Engineering > Architecture > ADRs` (create if missing).
   - Call `confluence.create_page` with the composed body.
   - Print the resulting Confluence URL.

6. **Link back to Jira**
   - If a Jira Epic key was provided, add a remote link from the Epic to the ADR page
     using `jira.update_issue` (remote links / web links field).
