"""Tests for the merge engine. These are the load-bearing invariants of the tool."""
from agent_init.core.ir import (
    Project, MemoryBlock, Rule, Skill, Hook, _Provenance,
)
from agent_init.core.merge import merge_into


def _rule(rid: str, body: str, src: str) -> Rule:
    return Rule(id=rid, description="", body=body, provenance=_Provenance(source=src))


def _skill(name: str, body: str, src: str) -> Skill:
    return Skill(name=name, description="x", body=body, provenance=_Provenance(source=src))


def test_rule_override_by_id():
    base = Project(name="x")
    org = Project(name="x", rules=[_rule("tests", "ORG", "org")])
    proj = Project(name="x", rules=[_rule("tests", "PROJECT", "project")])

    merge_into(base, org)
    merge_into(base, proj)

    assert len(base.rules) == 1
    assert base.rules[0].body == "PROJECT"
    assert base.rules[0].provenance.source == "project"
    assert "org" in base.rules[0].provenance.overrode


def test_rule_inheritance_when_not_overridden():
    base = Project(name="x")
    org = Project(name="x", rules=[_rule("secrets", "ORG", "org")])
    proj = Project(name="x", rules=[_rule("tests", "PROJECT", "project")])

    merge_into(base, org)
    merge_into(base, proj)

    by_id = {r.id: r for r in base.rules}
    assert by_id["secrets"].body == "ORG"
    assert by_id["secrets"].provenance.source == "org"
    assert by_id["tests"].body == "PROJECT"


def test_memory_appends():
    base = Project(name="x")
    a = Project(name="x", memory=[MemoryBlock(title="A", body="a", priority=1)])
    b = Project(name="x", memory=[MemoryBlock(title="B", body="b", priority=10)])

    merge_into(base, a)
    merge_into(base, b)

    assert len(base.memory) == 2
    assert {m.title for m in base.memory} == {"A", "B"}


def test_hooks_append_not_override():
    """Two hooks for the same event with different scripts are both kept."""
    base = Project(name="x")
    a = Project(name="x", hooks=[Hook(event="PreToolUse", script_path="a.sh", script_body="")])
    b = Project(name="x", hooks=[Hook(event="PreToolUse", script_path="b.sh", script_body="")])

    merge_into(base, a)
    merge_into(base, b)

    assert len(base.hooks) == 2


def test_skill_override_records_provenance_chain():
    base = Project(name="x")
    merge_into(base, Project(name="x", skills=[_skill("pr-review", "v1", "org")]))
    merge_into(base, Project(name="x", skills=[_skill("pr-review", "v2", "team")]))
    merge_into(base, Project(name="x", skills=[_skill("pr-review", "v3", "project")]))

    assert len(base.skills) == 1
    assert base.skills[0].body == "v3"
    # Each override records the source it masked at that step.
    assert base.skills[0].provenance.overrode == ["team"]


def test_stack_unions_dont_duplicate():
    base = Project(name="x", stack=["a"])
    merge_into(base, Project(name="x", stack=["a", "b"]))
    assert base.stack == ["a", "b"]
