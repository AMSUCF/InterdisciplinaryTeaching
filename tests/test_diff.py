# tests/test_diff.py
from canvas_sync.diff import compute_diff, FieldDiff


def test_no_changes():
    local = {"title": "Week 1", "body": "<p>Hello</p>", "points": 50}
    remote = {"title": "Week 1", "body": "<p>Hello</p>", "points": 50}
    diffs = compute_diff(local, remote)
    assert diffs == []


def test_single_field_changed():
    local = {"title": "Week 1", "points": 75}
    remote = {"title": "Week 1", "points": 50}
    diffs = compute_diff(local, remote)
    assert len(diffs) == 1
    assert diffs[0].field == "points"
    assert diffs[0].old_value == 50
    assert diffs[0].new_value == 75


def test_multiple_fields_changed():
    local = {"title": "Week 1 Updated", "points": 75}
    remote = {"title": "Week 1", "points": 50}
    diffs = compute_diff(local, remote)
    assert len(diffs) == 2
    fields = {d.field for d in diffs}
    assert fields == {"title", "points"}


def test_new_field_in_local():
    local = {"title": "Week 1", "points": 50}
    remote = {"title": "Week 1"}
    diffs = compute_diff(local, remote)
    assert len(diffs) == 1
    assert diffs[0].field == "points"
    assert diffs[0].old_value is None
    assert diffs[0].new_value == 50
