"""Schema validation tests — make sure typos fail loudly, not silently."""
import pytest
from agent_init.schema import validate, ManifestValidationError


def test_minimal_manifest_passes():
    validate({
        "version": 1,
        "project": {"name": "demo"},
        "targets": ["claude-code"],
    })


def test_full_manifest_passes():
    validate({
        "version": 1,
        "project": {"name": "demo", "language": "python", "stack": ["fastapi"]},
        "sources": [
            {"type": "local", "path": "./rules"},
            {"type": "git", "url": "github.com/x/y", "ref": "v1"},
        ],
        "targets": ["claude-code", "copilot"],
        "policy": {
            "secrets": {"block_paths": [".env"]},
            "mcp_servers": [{"name": "jira", "command": "npx", "args": ["x"]}],
        },
    })


def test_missing_version_fails():
    with pytest.raises(ManifestValidationError) as ei:
        validate({"project": {"name": "x"}, "targets": ["claude-code"]})
    assert "version" in str(ei.value)


def test_unknown_target_fails():
    with pytest.raises(ManifestValidationError) as ei:
        validate({
            "version": 1,
            "project": {"name": "x"},
            "targets": ["claude-cdoe"],  # typo
        })
    assert "targets" in str(ei.value)


def test_unknown_source_type_fails():
    with pytest.raises(ManifestValidationError):
        validate({
            "version": 1,
            "project": {"name": "x"},
            "targets": ["claude-code"],
            "sources": [{"type": "ftp", "url": "x"}],
        })


def test_typo_in_top_level_key_fails():
    """additionalProperties: false means typos in top-level keys fail."""
    with pytest.raises(ManifestValidationError):
        validate({
            "version": 1,
            "project": {"name": "x"},
            "targets": ["claude-code"],
            "polciy": {},  # typo
        })


def test_error_message_includes_pointer():
    with pytest.raises(ManifestValidationError) as ei:
        validate({
            "version": 1,
            "project": {"name": ""},  # empty string violates minLength
            "targets": ["claude-code"],
        })
    assert "project.name" in str(ei.value) or "$" in str(ei.value)
