---
name: bitbucket-pipelines-ci
description: >
  Triggered when a user says "add Bitbucket Pipelines", "set up CI for Bitbucket",
  "create a bitbucket-pipelines.yml", or "fix the pipeline".
---

## Procedure

1. **Detect project language and build tool** (same heuristic as github-actions-ci).

2. **Compose `bitbucket-pipelines.yml`**

   Java (Maven) example — adapt for detected stack:
   ```yaml
   image: maven:3.9-eclipse-temurin-21

   pipelines:
     default:
       - step:
           name: Build and Test
           caches:
             - maven
           script:
             - mvn -B verify
           artifacts:
             - target/surefire-reports/**

     branches:
       main:
         - step:
             name: Build
             script:
               - mvn -B package -DskipTests
         - step:
             name: Deploy to Staging
             deployment: staging
             script:
               - echo "Add deploy script here"
   ```

3. **Add repository variables**
   - List any secrets needed (database URLs, API keys).
   - Remind user to add them under Bitbucket → Repository settings →
     Pipelines → Repository variables.

4. **Write the file**
   - Place at `bitbucket-pipelines.yml` in the repo root.
   - Do not overwrite without confirmation.

5. **Validate and report**
   - Confirm YAML is well-formed.
   - Remind user to commit and push to trigger the first pipeline run.
