"""
`agent-init diff` — show what `build` would change without writing.

In --check mode (CI), exits non-zero if anything would change. This is how you
gate PRs on "did you forget to commit the rendered output?".
"""
from __future__ import annotations
import difflib
import filecmp
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def show(rendered: Path, current: Path, paths_to_check: list[str]) -> tuple[bool, list[str]]:
    """Return (any_changes, lines_of_diff_output)."""
    logger.debug("diff: rendered=%s current=%s files=%d", rendered, current, len(paths_to_check))
    out_lines: list[str] = []
    changed = False

    for rel in paths_to_check:
        new_file = rendered / rel
        old_file = current / rel
        if not new_file.exists():
            continue
        if not old_file.exists():
            out_lines.append(f"+ {rel}  (new)")
            changed = True
            continue
        if filecmp.cmp(new_file, old_file, shallow=False):
            continue

        # Binary check — skip diff body for non-text.
        try:
            new_text = new_file.read_text().splitlines(keepends=True)
            old_text = old_file.read_text().splitlines(keepends=True)
        except UnicodeDecodeError:
            out_lines.append(f"~ {rel}  (binary changed)")
            changed = True
            continue

        out_lines.append(f"~ {rel}")
        diff = difflib.unified_diff(
            old_text, new_text,
            fromfile=f"a/{rel}", tofile=f"b/{rel}", n=2,
        )
        out_lines.extend(line.rstrip("\n") for line in diff)
        changed = True

    # Detect files that exist in current but not rendered (orphans).
    rendered_set = set(paths_to_check)
    for kind in (".claude", ".github", ".vscode", "CLAUDE.md", ".mcp.json"):
        kp = current / kind
        if not kp.exists():
            continue
        if kp.is_file() and kind not in rendered_set:
            out_lines.append(f"- {kind}  (would be removed if you delete by hand)")
        elif kp.is_dir():
            for f in kp.rglob("*"):
                if f.is_file():
                    rel = str(f.relative_to(current))
                    if rel not in rendered_set:
                        out_lines.append(f"- {rel}  (orphan; build won't emit this)")

    logger.debug("diff: changed=%s", changed)
    return changed, out_lines
