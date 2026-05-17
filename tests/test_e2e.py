"""End-to-end: load the sample project, render, assert the rendered tree is sane."""
from pathlib import Path
import yaml
from agent_init.sources import loader
from agent_init.adapters.claude_code import ClaudeCodeAdapter
from agent_init.adapters.copilot import CopilotAdapter


SAMPLE = Path(__file__).parent.parent / "examples" / "sample-project"


def test_sample_project_renders_both_targets(tmp_path):
    project = loader.load(SAMPLE / "agent-init.yaml")

    cc_report = ClaudeCodeAdapter().render(project, tmp_path)
    cp_report = CopilotAdapter().render(project, tmp_path)

    # Both adapters produced at least the core entrypoint files.
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / ".github" / "copilot-instructions.md").exists()

    # The override worked: rendered `tests` rule must contain the project body, not org's.
    tests_rendered = (tmp_path / ".github" / "instructions" / "tests.instructions.md").read_text()
    assert "MockK" in tests_rendered, "project override of tests rule didn't take"
    assert "One assertion per test" not in tests_rendered, "org body leaked through"

    # Inheritance worked: `secrets` was only in org but should be rendered.
    secrets_rendered = (tmp_path / ".github" / "instructions" / "secrets.instructions.md")
    assert secrets_rendered.exists()
    assert "vault" in secrets_rendered.read_text()

    # Memory blocks from both sources are present.
    claude_md = (tmp_path / "CLAUDE.md").read_text()
    assert "Trunk-based development" in claude_md       # project memory
    assert "non-author" in claude_md                    # org memory

    # No warnings for Claude Code (it natively supports hooks).
    assert cc_report.warnings == []
    # Copilot warns about hook fallbacks.
    assert any("Hook" in w for w in cp_report.warnings)
