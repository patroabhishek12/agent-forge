---
name: github-actions-ci
description: >
  Triggered when a user says "add CI", "set up GitHub Actions", "create a workflow",
  "fix the CI pipeline", "add a test workflow", or "generate a build pipeline for this project".
---

## Procedure

1. **Detect project language and build tool**
   - Read `repo-index.yaml` if available; otherwise inspect root files.
   - Map language → default workflow template:
     - Java (Maven)  → `maven.yml`
     - Java (Gradle) → `gradle.yml`
     - Go            → `go.yml`
     - Rust          → `rust.yml`
     - Node/React    → `node.yml`
     - Python        → `python.yml`

2. **Compose the workflow file**

   Java (Maven) example — adapt for detected stack:
   ```yaml
   name: CI
   on:
     push:
       branches: [main]
     pull_request:
       branches: [main]
   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-java@v4
           with:
             java-version: '21'
             distribution: temurin
             cache: maven
         - run: mvn -B verify
         - uses: actions/upload-artifact@v4
           if: always()
           with:
             name: test-reports
             path: target/surefire-reports/
   ```

3. **Add secret references**
   - If environment variables (API tokens, DB URLs) are needed, use
     `${{ secrets.SECRET_NAME }}` and remind the user to add them in
     GitHub → Settings → Secrets and variables → Actions.

4. **Write the file**
   - Place at `.github/workflows/<project-slug>-ci.yml`.
   - Do not overwrite an existing workflow without confirmation.

5. **Validate**
   - Check the YAML is well-formed.
   - Remind user to commit the file and push to trigger the workflow.
