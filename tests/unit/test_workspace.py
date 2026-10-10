import subprocess

import pytest

from packages.sandbox.workspace import RepositoryWorkspace, WorkspaceError


def git(path, *args):
    return subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True).stdout.strip()


def create_repository(tmp_path):
    repository = tmp_path / "source"
    repository.mkdir()
    git(repository, "init", "-b", "main")
    git(repository, "config", "user.name", "Test")
    git(repository, "config", "user.email", "test@example.com")
    (repository / "parser.py").write_text("VALUE = 1\n")
    git(repository, "add", "parser.py")
    git(repository, "commit", "-m", "initial")
    return repository, git(repository, "rev-parse", "HEAD")


def test_workspace_clones_exact_sha_and_applies_patch(tmp_path) -> None:
    repository, sha = create_repository(tmp_path)
    workspace = RepositoryWorkspace(tmp_path / "workspace")
    assert workspace.clone_at(str(repository), sha) == sha
    changed = workspace.apply_patch("""diff --git a/parser.py b/parser.py
--- a/parser.py
+++ b/parser.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 2
""")
    assert changed == ["parser.py"]
    assert "VALUE = 2" in workspace.diff()


def test_workspace_collects_bounded_text_snapshots(tmp_path) -> None:
    repository, sha = create_repository(tmp_path)
    (repository / "README.md").write_text("RepoPilot\n")
    git(repository, "add", "README.md")
    git(repository, "commit", "-m", "docs")
    sha = git(repository, "rev-parse", "HEAD")
    workspace = RepositoryWorkspace(tmp_path / "workspace")
    workspace.clone_at(str(repository), sha)
    snapshots = workspace.file_snapshots()
    assert {snapshot.path for snapshot in snapshots} == {"README.md", "parser.py"}


def test_workspace_rejects_protected_path_patch(tmp_path) -> None:
    repository, sha = create_repository(tmp_path)
    workspace = RepositoryWorkspace(tmp_path / "workspace")
    workspace.clone_at(str(repository), sha)
    patch = """diff --git a/.env b/.env
new file mode 100644
--- /dev/null
+++ b/.env
@@ -0,0 +1 @@
+SECRET=never
"""
    with pytest.raises(WorkspaceError, match="Protected"):
        workspace.apply_patch(patch)
