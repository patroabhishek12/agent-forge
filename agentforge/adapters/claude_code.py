"""
Claude Code adapter — renders the IR to .claude/.

Verified against docs.anthropic.com/en/docs/claude-code as of May 2026.
"""
from __future__ import annotations
import logging
import json
from pathlib import Path
from ..core.ir import Project, RenderReport

logger = logging.getLogger(__name__)


class ClaudeCodeAdapter:
    name = "claude-code"
    target_dir = ".claude"

    def render(self, project: Project, out: Path) -> RenderReport:
        logger.debug("claude-code render start: out=%s", out)
        report = RenderReport(target=self.name)
        root = out / self.target_dir
        root.mkdir(parents=True, exist_ok=True)

        # 1. CLAUDE.md — memory + pointers to rules/
        claude_md = self._render_claude_md(project)
        self._write(out / "CLAUDE.md", claude_md, report)
        logger.debug("claude-code wrote CLAUDE.md")

        # 2. rules/ — path-scoped behavior. Claude Code has no native applyTo,
        #    so we write each as a markdown file and reference them in CLAUDE.md.
        for rule in project.rules:
            self._write(
                root / "rules" / f"{rule.id}.md",
                self._render_rule(rule),
                report,
            )
        logger.debug("claude-code wrote rules: %d", len(project.rules))

        # 3. skills/ — one folder per skill, SKILL.md inside.
        for skill in project.skills:
            sdir = root / "skills" / skill.name
            self._write(sdir / "SKILL.md", self._render_skill(skill), report)
            for fname, body in skill.resources.items():
                self._write(sdir / fname, body, report)
        logger.debug("claude-code wrote skills: %d", len(project.skills))

        # 4. commands/ — one .md file per command.
        for cmd in project.commands:
            self._write(root / "commands" / f"{cmd.name}.md", cmd.body, report)
        logger.debug("claude-code wrote commands: %d", len(project.commands))

        # 5. agents/ — Claude Code subagents with frontmatter.
        for agent in project.agents:
            self._write(
                root / "agents" / f"{agent.name}.md",
                self._render_agent(agent),
                report,
            )
        logger.debug("claude-code wrote agents: %d", len(project.agents))

        # 6. hooks/ — scripts + settings.json wiring.
        if project.hooks:
            settings = self._render_settings(project)
            self._write(root / "settings.json", json.dumps(settings, indent=2), report)
            for hook in project.hooks:
                self._write(
                    root / "hooks" / hook.script_path,
                    hook.script_body,
                    report,
                    executable=True,
                )
            logger.debug("claude-code wrote hooks: %d", len(project.hooks))

        # 7. .mcp.json — MCP servers live at repo root, not under .claude/.
        if project.mcp_servers:
            mcp = {
                "mcpServers": {
                    s.name: {"command": s.command, "args": s.args, "env": s.env}
                    for s in project.mcp_servers
                }
            }
            self._write(out / ".mcp.json", json.dumps(mcp, indent=2), report)
            logger.debug("claude-code wrote mcp servers: %d", len(project.mcp_servers))

        logger.debug("claude-code render complete")
        return report

    # ---------- renderers ----------

    def _render_claude_md(self, p: Project) -> str:
        parts = [f"# {p.name}\n"]
        if p.language or p.stack:
            parts.append(f"**Stack:** {p.language}, {', '.join(p.stack)}\n")
        for block in sorted(p.memory, key=lambda m: -m.priority):
            parts.append(f"## {block.title}\n\n{block.body}\n")
        if p.rules:
            parts.append("## Rules\n\nPath-scoped behaviors live in `.claude/rules/`:\n")
            for r in p.rules:
                scopes = ", ".join(r.apply_to) if r.apply_to else "all files"
                parts.append(f"- [`{r.id}`](.claude/rules/{r.id}.md) — {r.description} *(scope: {scopes})*")
            parts.append("")
        return "\n".join(parts)

    def _render_rule(self, r) -> str:
        # Claude Code rules are plain markdown; frontmatter is optional.
        fm = ["---", f"id: {r.id}", f"description: {r.description}"]
        if r.apply_to:
            fm.append(f"apply_to: {r.apply_to}")
        fm.append("---\n")
        return "\n".join(fm) + r.body

    def _render_skill(self, s) -> str:
        # The shared SKILL.md standard — same shape Copilot uses.
        return f"---\nname: {s.name}\ndescription: \"{s.description}\"\n---\n\n{s.body}"

    def _render_agent(self, a) -> str:
        fm_lines = ["---", f"name: {a.name}", f"description: \"{a.description}\""]
        if a.tools:
            fm_lines.append(f"tools: {a.tools}")
        if a.model:
            fm_lines.append(f"model: {a.model}")
        fm_lines.append("---\n")
        return "\n".join(fm_lines) + a.body

    def _render_settings(self, p: Project) -> dict:
        hooks_by_event: dict = {}
        for h in p.hooks:
            hooks_by_event.setdefault(h.event, []).append({
                "matcher": h.matcher,
                "command": f".claude/hooks/{h.script_path}",
            })
        return {"hooks": hooks_by_event}

    # ---------- I/O ----------

    def _write(self, path: Path, body: str, report: RenderReport, executable: bool = False) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        if executable:
            path.chmod(0o755)
        report.files_written.append(str(path))
        logger.debug("claude-code wrote file: %s", path)
