from packages.validation.results import ValidationKind, ValidationReport, ValidationResult


def test_validation_report_is_failed_when_one_check_fails() -> None:
    report = ValidationReport(
        results=[
            ValidationResult(kind=ValidationKind.TEST, passed=True),
            ValidationResult(kind=ValidationKind.LINT, passed=False, exit_code=1),
        ]
    )
    assert report.passed is False
