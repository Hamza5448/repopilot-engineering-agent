from apps.api.app.storage.sqlite import RunStore


def test_run_store_persists_run_and_creation_event(tmp_path) -> None:
    database_path = str(tmp_path / "repopilot.db")
    first_store = RunStore(database_path)
    created = first_store.create_run(42, "issue", "abc1234")

    second_store = RunStore(database_path)
    loaded = second_store.get_run(created["id"])
    events = second_store.list_events(created["id"])

    assert loaded is not None
    assert loaded["repository_id"] == 42
    assert loaded["status"] == "created"
    assert events[0]["event_type"] == "run.created"
    assert second_store.list_runs(10)[0]["id"] == created["id"]
