# tests/test_canvas_api.py
from unittest.mock import MagicMock, patch, call
from canvas_sync.canvas_api import CanvasSync
from canvas_sync.config import Config
from canvas_sync.models import Week, Assignment, Discussion


def make_config():
    return Config(
        api_url="https://webcourses.ucf.edu",
        api_key="fake-key",
        course_id=99999,
    )


def make_week(week_num=1, title="Test Week", assignments=None, discussion=None):
    return Week(
        week=week_num,
        title=title,
        starts="2026-05-11",
        body_markdown="## Readings\n\n- A reading",
        workshop=None,
        assignments=assignments or [],
        discussion=discussion,
    )


@patch("canvas_sync.canvas_api.Canvas")
def test_create_module(mock_canvas_cls):
    mock_canvas = MagicMock()
    mock_canvas_cls.return_value = mock_canvas
    mock_course = MagicMock()
    mock_canvas.get_course.return_value = mock_course
    mock_module = MagicMock()
    mock_module.id = 100
    mock_course.create_module.return_value = mock_module

    cs = CanvasSync(make_config())
    week = make_week()
    module_id = cs.create_module(week)

    mock_course.create_module.assert_called_once_with(
        module={"name": "Week 1: Test Week", "position": 1}
    )
    assert module_id == 100


@patch("canvas_sync.canvas_api.Canvas")
def test_create_page(mock_canvas_cls):
    mock_canvas = MagicMock()
    mock_canvas_cls.return_value = mock_canvas
    mock_course = MagicMock()
    mock_canvas.get_course.return_value = mock_course
    mock_page = MagicMock()
    mock_page.url = "week-1-test-week"
    mock_course.create_page.return_value = mock_page

    cs = CanvasSync(make_config())
    week = make_week()
    page_url = cs.create_page(week)

    create_call = mock_course.create_page.call_args
    assert create_call[1]["wiki_page"]["title"] == "Week 1: Test Week"
    assert create_call[1]["wiki_page"]["published"] is False
    assert page_url == "week-1-test-week"


@patch("canvas_sync.canvas_api.Canvas")
def test_create_assignment(mock_canvas_cls):
    mock_canvas = MagicMock()
    mock_canvas_cls.return_value = mock_canvas
    mock_course = MagicMock()
    mock_canvas.get_course.return_value = mock_course
    mock_assignment = MagicMock()
    mock_assignment.id = 200
    mock_course.create_assignment.return_value = mock_assignment

    cs = CanvasSync(make_config())
    a = Assignment(title="Activity Verification", points=50, due="2026-05-15", submission_type="online_text_entry")
    assignment_id = cs.create_assignment(a)

    create_call = mock_course.create_assignment.call_args
    assert create_call[1]["assignment"]["name"] == "Activity Verification"
    assert create_call[1]["assignment"]["points_possible"] == 50
    assert create_call[1]["assignment"]["published"] is False
    assert assignment_id == 200


@patch("canvas_sync.canvas_api.Canvas")
def test_create_discussion(mock_canvas_cls):
    mock_canvas = MagicMock()
    mock_canvas_cls.return_value = mock_canvas
    mock_course = MagicMock()
    mock_canvas.get_course.return_value = mock_course
    mock_topic = MagicMock()
    mock_topic.id = 300
    mock_course.create_discussion_topic.return_value = mock_topic

    cs = CanvasSync(make_config())
    d = Discussion(title="Intro discussion", points=30, due="2026-05-17")
    topic_id = cs.create_discussion(d, "<p>Introduce yourself</p>")

    create_call = mock_course.create_discussion_topic.call_args
    assert create_call[1]["title"] == "Intro discussion"
    assert create_call[1]["message"] == "<p>Introduce yourself</p>"
    assert create_call[1]["published"] is False
    assert topic_id == 300


@patch("canvas_sync.canvas_api.Canvas")
def test_add_module_items(mock_canvas_cls):
    mock_canvas = MagicMock()
    mock_canvas_cls.return_value = mock_canvas
    mock_course = MagicMock()
    mock_canvas.get_course.return_value = mock_course
    mock_module = MagicMock()
    mock_course.get_module.return_value = mock_module

    cs = CanvasSync(make_config())
    cs.add_module_item(module_id=100, item_type="Page", content_id="week-1-test", title="Week 1")
    cs.add_module_item(module_id=100, item_type="Assignment", content_id=200, title="Activity")

    assert mock_module.create_module_item.call_count == 2


@patch("canvas_sync.canvas_api.Canvas")
def test_get_page(mock_canvas_cls):
    mock_canvas = MagicMock()
    mock_canvas_cls.return_value = mock_canvas
    mock_course = MagicMock()
    mock_canvas.get_course.return_value = mock_course
    mock_page = MagicMock()
    mock_page.title = "Week 1: Test"
    mock_page.body = "<p>Old content</p>"
    mock_course.get_page.return_value = mock_page

    cs = CanvasSync(make_config())
    page = cs.get_page("week-1-test")
    assert page.title == "Week 1: Test"


@patch("canvas_sync.canvas_api.Canvas")
def test_update_page(mock_canvas_cls):
    mock_canvas = MagicMock()
    mock_canvas_cls.return_value = mock_canvas
    mock_course = MagicMock()
    mock_canvas.get_course.return_value = mock_course
    mock_page = MagicMock()
    mock_course.get_page.return_value = mock_page

    cs = CanvasSync(make_config())
    cs.update_page("week-1-test", title="New Title", body="<p>New</p>")
    mock_page.edit.assert_called_once_with(wiki_page={"title": "New Title", "body": "<p>New</p>"})
