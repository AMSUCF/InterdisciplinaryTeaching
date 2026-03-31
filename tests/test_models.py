from canvas_sync.models import Workshop, Assignment, Discussion, Week


def test_workshop_from_dict():
    data = {
        "title": "Workshop 1: Introducing AI for DH Pedagogy",
        "date": "2026-05-13",
        "time": "10 AM - noon",
        "location": "CHDR",
    }
    ws = Workshop.from_dict(data)
    assert ws.title == "Workshop 1: Introducing AI for DH Pedagogy"
    assert ws.date == "2026-05-13"
    assert ws.time == "10 AM - noon"
    assert ws.location == "CHDR"


def test_assignment_from_dict_defaults():
    data = {"title": "Activity Verification", "points": 50, "due": "2026-05-15"}
    a = Assignment.from_dict(data)
    assert a.title == "Activity Verification"
    assert a.points == 50
    assert a.due == "2026-05-15"
    assert a.submission_type == "online_text_entry"


def test_assignment_from_dict_custom_submission_type():
    data = {
        "title": "Final Portfolio",
        "points": 160,
        "due": "2026-08-01",
        "submission_type": "online_upload",
    }
    a = Assignment.from_dict(data)
    assert a.submission_type == "online_upload"


def test_discussion_from_dict():
    data = {
        "title": "Introduce yourself",
        "points": 30,
        "due": "2026-05-17",
    }
    d = Discussion.from_dict(data)
    assert d.title == "Introduce yourself"
    assert d.points == 30
    assert d.due == "2026-05-17"


def test_week_module_name():
    w = Week(
        week=1,
        title="Welcome and Interdisciplinary Teaching",
        starts="2026-05-11",
        body_markdown="## Readings\n\n- Some reading",
        workshop=None,
        assignments=[],
        discussion=None,
    )
    assert w.module_name == "Week 1: Welcome and Interdisciplinary Teaching"


def test_week_body_html():
    w = Week(
        week=3,
        title="AI for Textual Analysis",
        starts="2026-05-25",
        body_markdown="## Readings\n\n- A reading\n\n| Col1 | Col2 |\n|------|------|\n| a | b |",
        workshop=None,
        assignments=[],
        discussion=None,
    )
    html = w.body_html
    assert "<h2>" in html
    assert "<table>" in html


def test_week_discussion_prompt_html():
    body = "## Readings\n\n- A reading\n\n## Discussion Prompt\n\nDescribe your experience.\n\nWhat do you think?"
    w = Week(
        week=1,
        title="Welcome",
        starts="2026-05-11",
        body_markdown=body,
        workshop=None,
        assignments=[],
        discussion=Discussion(title="Intro", points=30, due="2026-05-17"),
    )
    html = w.discussion_prompt_html
    assert "Describe your experience." in html
    assert "What do you think?" in html
    assert "Readings" not in html


def test_week_discussion_prompt_html_none_when_no_section():
    w = Week(
        week=1,
        title="Welcome",
        starts="2026-05-11",
        body_markdown="## Readings\n\n- A reading",
        workshop=None,
        assignments=[],
        discussion=None,
    )
    assert w.discussion_prompt_html is None


def test_week_due_datetime():
    w = Week(
        week=1,
        title="Welcome",
        starts="2026-05-11",
        body_markdown="",
        workshop=None,
        assignments=[Assignment(title="Test", points=50, due="2026-05-15", submission_type="online_text_entry")],
        discussion=None,
    )
    dt = w.assignments[0].due_datetime
    assert dt.hour == 23
    assert dt.minute == 59
    assert str(dt.tzinfo) == "US/Eastern" or "Eastern" in str(dt.tzinfo)
