"""Provider-neutral test and static-analysis result contracts."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ValidationKind(StrEnum):
    TEST = "test"
    LINT = "lint"
    TYPE_CHECK = "type_check"
    SECURITY = "security"


class ValidationResult(BaseModel):
    kind: ValidationKind
    passed: bool
    exit_code: int | None = None
    summary: str = ""
    output_artifact_id: str | None = None
    duration_ms: int = Field(default=0, ge=0)


class ValidationReport(BaseModel):
    results: list[ValidationResult]

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)
