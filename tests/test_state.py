# tests/test_state.py
import json
from canvas_sync.state import SyncState


def test_load_empty_state(tmp_path):
    state_file = tmp_path / ".canvas_sync_state.json"
    state = SyncState(str(state_file))
    assert state.get_week("week-01") is None


def test_save_and_load_state(tmp_path):
    state_file = tmp_path / ".canvas_sync_state.json"
    state = SyncState(str(state_file))
    state.set_week("week-01", {
        "module_id": 123,
        "page_id": 456,
        "assignments": [{"title": "Activity Verification", "canvas_id": 789}],
        "discussion_id": 101,
        "last_synced": "2026-04-01T14:30:00",
    })
    state.save()

    state2 = SyncState(str(state_file))
    week = state2.get_week("week-01")
    assert week["module_id"] == 123
    assert week["page_id"] == 456
    assert week["assignments"][0]["canvas_id"] == 789


def test_update_existing_week(tmp_path):
    state_file = tmp_path / ".canvas_sync_state.json"
    state = SyncState(str(state_file))
    state.set_week("week-01", {"module_id": 123})
    state.set_week("week-01", {"module_id": 999, "page_id": 456})
    assert state.get_week("week-01")["module_id"] == 999


def test_all_weeks(tmp_path):
    state_file = tmp_path / ".canvas_sync_state.json"
    state = SyncState(str(state_file))
    state.set_week("week-01", {"module_id": 1})
    state.set_week("week-03", {"module_id": 3})
    all_weeks = state.all_weeks()
    assert "week-01" in all_weeks
    assert "week-03" in all_weeks
    assert len(all_weeks) == 2
