"""Bounded repository context construction for agent inputs."""

from pydantic import BaseModel, Field


class FileSnapshot(BaseModel):
    path: str
    content: str
    language: str | None = None


class ContextFile(BaseModel):
    path: str
    relevance: float = Field(ge=0, le=1)
    excerpt: str


class RepositoryContext(BaseModel):
    repository_id: int
    base_sha: str
    issue_title: str
    issue_body: str
    files: list[ContextFile]


def build_context(
    repository_id: int,
    base_sha: str,
    issue_title: str,
    issue_body: str,
    files: list[FileSnapshot],
    max_files: int = 12,
    max_excerpt_chars: int = 4_000,
) -> RepositoryContext:
    """Select bounded, keyword-relevant file excerpts for a target SHA."""

    keywords = {
        token.lower().strip(".,:;()[]{}")
        for token in f"{issue_title} {issue_body}".split()
        if len(token) >= 3
    }

    def score(file: FileSnapshot) -> tuple[float, str]:
        path_tokens = set(file.path.lower().replace("/", " ").replace("_", " ").split())
        content_tokens = set(file.content.lower().split())
        matches = len(keywords & (path_tokens | content_tokens))
        return (matches / max(len(keywords), 1), file.path)

    ranked = sorted(files, key=score, reverse=True)[:max_files]
    selected = [
        ContextFile(path=file.path, relevance=round(score(file)[0], 3), excerpt=file.content[:max_excerpt_chars])
        for file in ranked
    ]
    return RepositoryContext(
        repository_id=repository_id,
        base_sha=base_sha,
        issue_title=issue_title,
        issue_body=issue_body,
        files=selected,
    )
