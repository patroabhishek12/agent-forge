---
name: cut-release
description: Walk through the release checklist and prep a tag
---
Cut a release of payments-service.

1. Run `./gradlew test` and confirm green.
2. Check `CHANGELOG.md` has entries since the last tag; if not, draft them from git log.
3. Suggest the next semver based on changelog (patch/minor/major).
4. Show the exact `git tag` command. Do not run it.
