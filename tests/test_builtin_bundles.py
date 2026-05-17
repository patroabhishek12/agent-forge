"""Tests for built-in bundle loading and schema validation."""
from __future__ import annotations
from pathlib import Path

import pytest

from agent_init.sources.loader import list_bundles, _resolve_builtin, _load_local
from agent_init.schema import validate, ManifestValidationError


EXPECTED_BUNDLES = {
    "core", "atlassian", "github", "bitbucket",
    "lang-java", "lang-rust", "lang-go", "ui-react", "architect",
}


def test_list_bundles_returns_all_expected():
    found = set(list_bundles())
    assert EXPECTED_BUNDLES == found, (
        f"missing: {EXPECTED_BUNDLES - found}, extra: {found - EXPECTED_BUNDLES}"
    )


def test_resolve_builtin_returns_valid_path():
    source_id, path = _resolve_builtin({"type": "builtin", "bundle": "core"})
    assert source_id == "builtin:core"
    assert path.exists()
    assert path.is_dir()


def test_resolve_unknown_bundle_raises():
    with pytest.raises(ValueError, match="unknown builtin bundle"):
        _resolve_builtin({"type": "builtin", "bundle": "does-not-exist"})


@pytest.mark.parametrize("bundle", sorted(EXPECTED_BUNDLES))
def test_bundle_loads_without_error(bundle):
    _, path = _resolve_builtin({"type": "builtin", "bundle": bundle})
    project = _load_local(f"builtin:{bundle}", path)
    assert project is not None


def test_core_bundle_has_discover_repo_skill():
    _, path = _resolve_builtin({"type": "builtin", "bundle": "core"})
    project = _load_local("builtin:core", path)
    names = {s.name for s in project.skills}
    assert "discover-repo" in names
    assert "codegen-from-ticket" in names


def test_atlassian_bundle_has_jira_skills():
    _, path = _resolve_builtin({"type": "builtin", "bundle": "atlassian"})
    project = _load_local("builtin:atlassian", path)
    names = {s.name for s in project.skills}
    assert "jira-epic-generator" in names
    assert "jira-bug-tracer" in names
    assert "jira-analytics" in names
    assert "confluence-adr" in names


def test_atlassian_bundle_declares_mcp_servers():
    _, path = _resolve_builtin({"type": "builtin", "bundle": "atlassian"})
    project = _load_local("builtin:atlassian", path)
    server_names = {s.name for s in project.mcp_servers}
    assert "jira" in server_names
    assert "confluence" in server_names


def test_architect_bundle_has_agent():
    _, path = _resolve_builtin({"type": "builtin", "bundle": "architect"})
    project = _load_local("builtin:architect", path)
    agent_names = {a.name for a in project.agents}
    assert "solution-architect" in agent_names


def test_language_bundles_have_rules():
    for bundle in ("lang-java", "lang-rust", "lang-go"):
        _, path = _resolve_builtin({"type": "builtin", "bundle": bundle})
        project = _load_local(f"builtin:{bundle}", path)
        assert project.rules, f"{bundle} should have at least one rule"


def test_builtin_source_type_passes_schema_validation():
    validate({
        "version": 1,
        "project": {"name": "demo"},
        "sources": [
            {"type": "builtin", "bundle": "core"},
            {"type": "builtin", "bundle": "atlassian"},
            {"type": "local", "path": "./rules"},
        ],
        "targets": ["claude-code"],
    })


def test_builtin_source_missing_bundle_field_fails_schema():
    with pytest.raises(ManifestValidationError):
        validate({
            "version": 1,
            "project": {"name": "demo"},
            "sources": [{"type": "builtin"}],
            "targets": ["claude-code"],
        })
