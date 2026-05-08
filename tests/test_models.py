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


def test_week_slides_default_none():
    w = Week(
        week=2,
        title="Learning Theories",
        starts="2026-05-18",
        body_markdown="## Readings",
        workshop=None,
        assignments=[],
        discussion=None,
    )
    assert w.slides is None
    assert w.slides_section_html("https://example.com/slides/") is None


def test_week_slides_section_html_renders_iframe():
    w = Week(
        week=1,
        title="Welcome",
        starts="2026-05-11",
        body_markdown="## Readings",
        workshop=None,
        assignments=[],
        discussion=None,
        slides="week-01",
    )
    html = w.slides_section_html("https://example.com/slides/")
    assert html is not None
    # Header
    assert "<h2>Slides</h2>" in html
    # Iframe with full URL
    assert 'src="https://example.com/slides/week-01/"' in html
    # Responsive wrapper inline styles (Canvas strips classes)
    assert "padding-bottom:56.25%" in html
    # Allowfullscreen and lazy loading
    assert "allowfullscreen" in html
    assert 'loading="lazy"' in html
    # Fallback link
    assert 'href="https://example.com/slides/week-01/"' in html
    assert "Open slides in a new tab" in html


def test_week_slides_section_html_handles_trailing_slash():
    """slides_base_url with or without trailing slash should both produce the same URL."""
    w_with_slug = Week(
        week=1,
        title="W",
        starts="2026-05-11",
        body_markdown="",
        workshop=None,
        assignments=[],
        discussion=None,
        slides="week-01",
    )
    with_slash = w_with_slug.slides_section_html("https://example.com/slides/")
    without_slash = w_with_slug.slides_section_html("https://example.com/slides")
    # Both should produce a URL ending in /slides/week-01/
    assert "/slides/week-01/" in with_slash
    assert "/slides/week-01/" in without_slash
    # And not /slides//week-01/ from the with-slash variant
    assert "/slides//week-01/" not in with_slash
