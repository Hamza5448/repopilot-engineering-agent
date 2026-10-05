from apps.api.app.github.repositories import RepositoryStore


def test_repository_store_upserts_and_lists_by_name() -> None:
    store = RepositoryStore()
    store.upsert_from_github(
        {"id": 2, "full_name": "team/zeta", "default_branch": "trunk"}, 99
    )
    store.upsert_from_github({"id": 1, "full_name": "team/alpha"}, 99)
    store.upsert_from_github({"id": 2, "full_name": "team/zeta", "private": True}, 99)

    repositories = store.list()
    assert [repository.full_name for repository in repositories] == ["team/alpha", "team/zeta"]
    assert repositories[1].private is True
    assert repositories[1].default_branch == "main"


def test_missing_repository_returns_none() -> None:
    assert RepositoryStore().get(404) is None
