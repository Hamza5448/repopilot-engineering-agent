"""Structured planner contract, independent of a model provider."""

from pydantic import BaseModel, Field

from packages.context.context import RepositoryContext


class AcceptanceCriterion(BaseModel):
    description: str = Field(min_length=1)
    verifiable_by: str = Field(min_length=1)


class PlanStep(BaseModel):
    order: int = Field(ge=1)
    description: str = Field(min_length=1)
    affected_files: list[str] = Field(default_factory=list)


class PlanOutput(BaseModel):
    summary: str
    assumptions: list[str]
    acceptance_criteria: list[AcceptanceCriterion]
    steps: list[PlanStep]
    risks: list[str]
    validation: list[str]


class Planner:
    """Create a safe baseline plan until the model-backed planner is connected."""

    def plan(self, context: RepositoryContext) -> PlanOutput:
        affected_files = [file.path for file in context.files[:5]]
        return PlanOutput(
            summary=f"Investigate and implement: {context.issue_title}",
            assumptions=["The requested change targets the supplied base commit."],
            acceptance_criteria=[
                AcceptanceCriterion(
                    description="The issue behavior is addressed without unrelated changes.",
                    verifiable_by="Focused regression test and diff review",
                )
            ],
            steps=[
                PlanStep(order=1, description="Inspect the highest-relevance repository files.", affected_files=affected_files),
                PlanStep(order=2, description="Implement the smallest change that satisfies the criteria.", affected_files=affected_files),
                PlanStep(order=3, description="Run project validation and inspect the final diff.", affected_files=[]),
            ],
            risks=["Repository evidence may be incomplete; re-plan if validation disproves an assumption."],
            validation=["Run targeted tests", "Run lint and type checks", "Review diff scope"],
        )
