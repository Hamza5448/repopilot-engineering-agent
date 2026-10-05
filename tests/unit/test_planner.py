from packages.agents.planner import Planner
from packages.context.context import FileSnapshot, build_context


def test_planner_returns_structured_handoff_contract() -> None:
    context = build_context(
        repository_id=1,
        base_sha="abcdef1",
        issue_title="Fix parser",
        issue_body="Add a regression test",
        files=[FileSnapshot(path="parser.py", content="def parse(): pass")],
    )
    plan = Planner().plan(context)
    assert plan.steps[0].order == 1
    assert plan.acceptance_criteria[0].verifiable_by
    assert plan.validation
