#!/usr/bin/env bash
# Block edits to migrations that already exist in main.
set -euo pipefail
file="${CLAUDE_TOOL_FILE_PATH:-}"
if [[ -z "$file" ]]; then exit 0; fi
if git ls-tree -r main --name-only | grep -qx "$file"; then
  echo "REFUSE: $file already exists on main; migrations are forward-only." >&2
  exit 2
fi
