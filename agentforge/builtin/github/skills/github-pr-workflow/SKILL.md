---
name: github-pr-workflow
description: >
  Triggered when a user says "open a PR", "create a pull request", "push my changes",
  "raise a PR for this story", or "submit this for review".
  Stages commits, pushes the branch, and creates a pull request with a structured description.
---

## MCP tools used
- `github.create_pull_request`, `github.list_pull_requests`

## Procedure

1. **Verify working tree**
   - Check `git status` — confirm there are staged or unstaged changes.
   - If the branch is `main` or `master`, refuse and ask the user to switch to a
     feature branch first.

2. **Stage and commit**
   - If changes are unstaged, present a summary and ask the user to confirm staging all.
   - Run `git add -p` guidance or `git add .` based on user preference.
   - Compose a commit message:
     - Format: `<type>(<scope>): <imperative summary>` (Conventional Commits).
     - Types: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`.
     - If a Jira key is available from context, append `Refs: PROJ-NNN`.

3. **Push the branch**
   - Run `git push --set-upstream origin <branch>`.

4. **Compose PR description**
   ```
   ## Summary
   <one-paragraph description of what this PR does>

   ## Changes
   - <bullet list of meaningful changes>

   ## Testing
   - [ ] Unit tests pass locally
   - [ ] Integration tests pass
   - [ ] Manual smoke test performed

   ## Jira
   Refs: <PROJ-NNN link if available>
   ```

5. **Create the PR**
   - Call `github.create_pull_request` with:
     - `title`: derived from the Jira story summary or branch name
     - `body`: the composed description
     - `base`: `main` (or the configured default branch)
     - `head`: current branch
     - `draft`: true if user asks for a draft

6. **Report**
   - Print the PR URL.
   - Remind user to assign reviewers and link the PR to the Jira issue.
