"""
GitHub Copilot adapter — renders the IR to .github/.

Layout follows docs.github.com/en/copilot as of May 2026:
  .github/copilot-instructions.md
  .github/instructions/<id>.instructions.md  (with applyTo frontmatter)
  .github/skills/<name>/SKILL.md
  .github/prompts/<name>.prompt.md
  .github/agents/<name>.agent.md
  .github/workflows/<name>.yml              (hook fallback)
"""
from __future__ import annotations
import logging
from pathlib import Path
from ..core.ir import Project, RenderReport

logger = logging.getLogger(__name__)


class CopilotAdapter:
    name = "copilot"
    target_dir = ".github"

    def render(self, project: Project, out: Path) -> RenderReport:
        logger.debug("copilot render start: out=%s", out)
        report = RenderReport(target=self.name)
        root = out / self.target_dir
        root.mkdir(parents=True, exist_ok=True)

        # 1. copilot-instructions.md — repo-wide, always-on.
        self._write(root / "copilot-instructions.md", self._render_main(project), report)
        logger.debug("copilot wrote copilot-instructions.md")

        # 2. instructions/ — path-scoped via applyTo frontmatter.
        for r in project.rules:
            self._write(
                root / "instructions" / f"{r.id}.instructions.md",
                self._render_rule(r),
                report,
            )
            if not r.apply_to:
                report.warnings.append(
                    f"Rule {r.id!r} has no apply_to; will be treated as repo-wide by Copilot."
                )
        logger.debug("copilot wrote rules: %d", len(project.rules))

        # 3. skills/ — SKILL.md is the shared standard, passes through identically.
        for s in project.skills:
            sdir = root / "skills" / s.name
            self._write(sdir / "SKILL.md", self._render_skill(s), report)
            for fname, body in s.resources.items():
                self._write(sdir / fname, body, report)
        logger.debug("copilot wrote skills: %d", len(project.skills))

        # 4. prompts/ — Copilot's equivalent of slash commands.
        for c in project.commands:
            self._write(
                root / "prompts" / f"{c.name}.prompt.md",
                self._render_prompt(c),
                report,
            )
        logger.debug("copilot wrote prompts: %d", len(project.commands))

        # 5. agents/ — Copilot custom agents (.agent.md).
        for a in project.agents:
            self._write(
                root / "agents" / f"{a.name}.agent.md",
                self._render_agent(a),
                report,
            )
        logger.debug("copilot wrote agents: %d", len(project.agents))

        # 6. hooks — Copilot has no native equivalent. Degrade.
        for h in project.hooks:
            if h.fallback == "skip":
                report.skipped.append(f"hook:{h.event}:{h.script_path}")
                continue
            if h.fallback == "github-action":
                self._write(
                    root / "workflows" / f"hook-{h.script_path.replace('/', '-')}.yml",
                    self._render_hook_as_action(h),
                    report,
                )
                report.warnings.append(
                    f"Hook {h.script_path!r} ({h.event}) emitted as GitHub Action; "
                    "runs on PR, not on the developer's machine."
                )
            elif h.fallback == "instruction":
                # Append a self-enforce instruction to copilot-instructions.md
                msg = f"\n\n## Self-enforced check ({h.event})\n\n" \
                      f"Before tool use matching `{h.matcher}`, verify the equivalent of:\n\n" \
                      f"```bash\n{h.script_body}\n```\n"
                with open(root / "copilot-instructions.md", "a") as f:
                    f.write(msg)
                report.warnings.append(
                    f"Hook {h.script_path!r} folded into copilot-instructions.md as self-enforce text."
                )
        if project.hooks:
            logger.debug("copilot processed hooks: %d", len(project.hooks))

        # 7. MCP — Copilot reads .vscode/mcp.json in VS Code.
        if project.mcp_servers:
            import json
            mcp = {
                "servers": {
                    s.name: {"command": s.command, "args": s.args, "env": s.env}
                    for s in project.mcp_servers
                }
            }
            self._write(out / ".vscode" / "mcp.json", json.dumps(mcp, indent=2), report)
            logger.debug("copilot wrote mcp servers: %d", len(project.mcp_servers))

        logger.debug("copilot render complete")
        return report

    # ---------- renderers ----------

    def _render_main(self, p: Project) -> str:
        parts = [f"# {p.name}\n"]
        if p.language or p.stack:
            parts.append(f"**Stack:** {p.language}, {', '.join(p.stack)}\n")
        for block in sorted(p.memory, key=lambda m: -m.priority):
            parts.append(f"## {block.title}\n\n{block.body}\n")
        return "\n".join(parts)

    def _render_rule(self, r) -> str:
        fm = ["---", f"description: \"{r.description}\""]
        if r.apply_to:
            # Copilot expects a single glob string or a list
            fm.append(f"applyTo: \"{','.join(r.apply_to)}\"")
        if r.exclude_agents:
            fm.append(f"excludeAgent: {r.exclude_agents}")
        fm.append("---\n")
        return "\n".join(fm) + r.body

    def _render_skill(self, s) -> str:
        return f"---\nname: {s.name}\ndescription: \"{s.description}\"\n---\n\n{s.body}"

    def _render_prompt(self, c) -> str:
        return f"---\ndescription: \"{c.description}\"\n---\n\n{c.body}"

    def _render_agent(self, a) -> str:
        fm = ["---", f"description: \"{a.description}\""]
        if a.tools:
            fm.append(f"tools: {a.tools}")
        if a.model:
            fm.append(f"model: {a.model}")
        fm.append("---\n")
        return "\n".join(fm) + a.body

    def _render_hook_as_action(self, h) -> str:
        # Minimal GHA fallback. Real version would map matcher → trigger properly.
        triggers = "pull_request" if h.event == "PreToolUse" else "push"
        return f"""name: hook-{h.script_path}
on: [{triggers}]
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: {h.event}
        run: |
{self._indent(h.script_body, 10)}
"""

    @staticmethod
    def _indent(text: str, n: int) -> str:
        pad = " " * n
        return "\n".join(pad + line for line in text.splitlines())

    def _write(self, path: Path, body: str, report: RenderReport) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        report.files_written.append(str(path))
        logger.debug("copilot wrote file: %s", path)
