from apps.api.app.storage.sqlalchemy import SqlAlchemyRunStore


def test_sqlalchemy_store_persists_runs_and_events(tmp_path) -> None:
    store = SqlAlchemyRunStore(f"sqlite:///{tmp_path / 'repopilot.db'}")
    created = store.create_run(5, "issue", "abcdef1")
    store.append_event(created["id"], "run.queued", {"queue": "local"})
    loaded = store.get_run(created["id"])
    events = store.list_events(created["id"])
    assert loaded is not None
    assert loaded["status"] == "created"
    assert [event["event_type"] for event in events] == ["run.created", "run.queued"]
