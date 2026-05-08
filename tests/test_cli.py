# tests/test_cli.py
from canvas_sync.__main__ import build_parser, _splice_slides


def test_init_command():
    parser = build_parser()
    args = parser.parse_args(["init"])
    assert args.command == "init"


def test_push_all():
    parser = build_parser()
    args = parser.parse_args(["push", "--all"])
    assert args.command == "push"
    assert args.all is True
    assert args.week is None
    assert args.force is False


def test_push_week():
    parser = build_parser()
    args = parser.parse_args(["push", "--week", "3"])
    assert args.command == "push"
    assert args.week == 3
    assert args.all is False


def test_push_force():
    parser = build_parser()
    args = parser.parse_args(["push", "--week", "3", "--force"])
    assert args.force is True


def test_status_command():
    parser = build_parser()
    args = parser.parse_args(["status"])
    assert args.command == "status"


def test_diff_all():
    parser = build_parser()
    args = parser.parse_args(["diff", "--all"])
    assert args.command == "diff"
    assert args.all is True


def test_diff_week():
    parser = build_parser()
    args = parser.parse_args(["diff", "--week", "5"])
    assert args.command == "diff"
    assert args.week == 5


def test_splice_slides_inserts_before_first_h2():
    body = (
        "<p>Welcome paragraph.</p>\n"
        "<p>NEH workshop note.</p>\n"
        "<h2>Readings</h2>\n"
        "<ul><li>A reading</li></ul>\n"
        "<h2>Discussion Prompt</h2>\n"
        "<p>Question.</p>\n"
    )
    slides = "<h2>Slides</h2>\n<div>iframe-here</div>\n"
    result = _splice_slides(body, slides)
    # Slides block should appear in the output exactly once
    assert result.count("<h2>Slides</h2>") == 1
    # Original Readings heading still present
    assert "<h2>Readings</h2>" in result
    # Slides block should appear BEFORE Readings
    slides_idx = result.index("<h2>Slides</h2>")
    readings_idx = result.index("<h2>Readings</h2>")
    assert slides_idx < readings_idx
    # Welcome paragraph should still appear before slides
    welcome_idx = result.index("Welcome paragraph.")
    assert welcome_idx < slides_idx


def test_splice_slides_appends_when_no_h2():
    body = "<p>Just an intro paragraph, no headings.</p>\n"
    slides = "<h2>Slides</h2>\n<div>iframe</div>\n"
    result = _splice_slides(body, slides)
    # Body intact
    assert "Just an intro paragraph" in result
    # Slides block appended at the end
    assert result.endswith(slides) or result.rstrip().endswith(slides.rstrip())


def test_splice_slides_returns_body_unchanged_when_slides_html_empty():
    body = "<p>Hello</p>\n<h2>Readings</h2>\n"
    result = _splice_slides(body, "")
    assert result == body


def test_splice_slides_returns_body_unchanged_when_slides_html_none():
    body = "<p>Hello</p>\n<h2>Readings</h2>\n"
    result = _splice_slides(body, None)
    assert result == body


from unittest.mock import MagicMock
from canvas_sync.__main__ import _render_page_body


def test_render_page_body_no_slides_returns_body_html():
    """When week has no slides, _render_page_body returns body_html unchanged."""
    cs = MagicMock()
    cs.config.slides_base_url = "https://example.com/slides/"
    week = MagicMock()
    week.slides = None
    week.body_html = "<p>Hello</p>\n<h2>Readings</h2>\n"
    week.slides_section_html.return_value = None  # slides_section_html returns None when slides is unset
    result = _render_page_body(cs, week)
    assert result == "<p>Hello</p>\n<h2>Readings</h2>\n"


def test_render_page_body_with_slides_splices_iframe():
    """When week has slides, _render_page_body splices the iframe before the first <h2>."""
    cs = MagicMock()
    cs.config.slides_base_url = "https://example.com/slides/"
    week = MagicMock()
    week.slides = "week-01"
    week.body_html = "<p>Welcome.</p>\n<h2>Readings</h2>\n"
    week.slides_section_html.return_value = "<h2>Slides</h2>\n<iframe></iframe>\n"
    result = _render_page_body(cs, week)
    assert "<h2>Slides</h2>" in result
    slides_idx = result.index("<h2>Slides</h2>")
    readings_idx = result.index("<h2>Readings</h2>")
    assert slides_idx < readings_idx
