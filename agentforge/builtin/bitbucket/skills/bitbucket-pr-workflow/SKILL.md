---
name: bitbucket-pr-workflow
description: >
  Triggered when a user says "open a PR on Bitbucket", "create a pull request",
  "push my changes and raise a PR", or "submit this for review on Bitbucket".
  Stages commits, pushes the branch, and creates a Bitbucket pull request.
---

## MCP tools used
- `bitbucket.create_pull_request`

## Procedure

1. **Verify working tree**
   - Reject if on `main` or `master`. Prompt to create/switch to a feature branch.

2. **Stage and commit**
   - Compose a Conventional Commits message: `<type>(<scope>): <summary>`.
   - If a Jira key is available, append to the message body: `PROJ-NNN #comment <summary>`.
     Bitbucket + Jira smart commits will automatically transition the issue.

3. **Push the branch**
   - Run `git push --set-upstream origin <branch>`.

4. **Compose PR description**
   ```
   ## What
   <what changed and why>

   ## How to test
   1. <step>
   2. <step>

   ## Checklist
   - [ ] Tests pass
   - [ ] No new lint warnings
   - [ ] Jira issue transitioned to "In Review"

   Refs: PROJ-NNN
   ```

5. **Create the PR**
   - Call `bitbucket.create_pull_request` with:
     - `title`: from Jira story or branch name
     - `description`: composed body above
     - `source.branch.name`: current branch
     - `destination.branch.name`: `main`
     - `reviewers`: ask the user for reviewer slugs, or leave empty

6. **Report**
   - Print the PR URL and remind user to add reviewers if not set.
