from packages.context.context import FileSnapshot, build_context


def test_context_ranks_relevant_files_and_bounds_excerpts() -> None:
    context = build_context(
        repository_id=1,
        base_sha="abcdef1",
        issue_title="Fix parser validation",
        issue_body="Parser rejects valid input",
        files=[
            FileSnapshot(path="README.md", content="project overview"),
            FileSnapshot(path="parser.py", content="parser validation\n" * 100),
        ],
        max_excerpt_chars=40,
    )
    assert context.files[0].path == "parser.py"
    assert len(context.files[0].excerpt) == 40
    assert context.base_sha == "abcdef1"
