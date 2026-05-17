---
name: discover-repo
description: >
  Triggered when a user asks to "map the repo", "index the project", "document the codebase",
  or "fill the knowledge base". Walks all source trees, catalogues modules/services/packages,
  and writes a structured index to .claude/knowledge/ (or .copilot/knowledge/).
---

## Procedure

1. **Identify repo topology**
   - Check for a monorepo signal: `pnpm-workspace.yaml`, `nx.json`, `lerna.json`, `Cargo.toml`
     with `[workspace]`, `go.work`, or multiple `build.gradle` files.
   - Check for a polyrepo signal: a single root `package.json`, `pom.xml`, `Cargo.toml`, or
     `go.mod` without sub-module declarations.
   - Record topology as `monorepo` or `polyrepo`.

2. **Enumerate services / modules**
   - For each detected sub-project (directory containing a build manifest), extract:
     - `name` — from the manifest (`package.json#name`, `artifactId`, `Cargo.toml#name`, etc.)
     - `language` — inferred from build manifest
     - `path` — relative to repo root
     - `entry_points` — main files (`src/main.*, index.*, cmd/*/main.go`)
     - `exposed_ports` — any port constants from source or Dockerfile / docker-compose
     - `dependencies` — direct deps listed in the manifest

3. **Detect shared layers**
   - Look for directories named `shared/`, `common/`, `libs/`, `packages/` — record them
     separately as `shared_libs`.

4. **Detect CI/CD**
   - Check for `.github/workflows/*.yml`, `bitbucket-pipelines.yml`, `Jenkinsfile`,
     `.gitlab-ci.yml` — record filenames.

5. **Write knowledge index**
   - Determine knowledge root: `.claude/knowledge/` if `.claude/` exists, else
     `.copilot/knowledge/`, else `.agent/knowledge/`.
   - Create `repo-index.yaml` in the knowledge root with structure:

     ```yaml
     topology: monorepo | polyrepo
     scanned_at: <ISO-8601 timestamp>
     services:
       - name: ...
         language: ...
         path: ...
         entry_points: [...]
         exposed_ports: [...]
         dependencies: [...]
     shared_libs:
       - name: ...
         path: ...
     ci_files: [...]
     ```

6. **Summarise to user**
   - Print a table: `service | language | path | entry points`.
   - Mention where `repo-index.yaml` was written.
   - Suggest running `jira-epic-generator` or `codegen-from-ticket` next.
