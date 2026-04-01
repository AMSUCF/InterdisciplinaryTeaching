from __future__ import annotations

from canvasapi import Canvas
from canvasapi.exceptions import ResourceDoesNotExist

from canvas_sync.config import Config
from canvas_sync.models import Assignment, Discussion


class CanvasSync:
    def __init__(self, config: Config):
        self._canvas = Canvas(config.api_url, config.api_key)
        self._course = self._canvas.get_course(config.course_id)

    def create_module(self, week) -> int:
        module = self._course.create_module(
            module={"name": week.module_name, "position": week.week}
        )
        return module.id

    def create_page(self, week) -> str:
        page = self._course.create_page(
            wiki_page={
                "title": week.module_name,
                "body": week.body_html,
                "published": False,
            }
        )
        return page.url

    def create_assignment(self, assignment: Assignment) -> int:
        result = self._course.create_assignment(
            assignment={
                "name": assignment.title,
                "points_possible": assignment.points,
                "due_at": assignment.due_datetime.isoformat(),
                "submission_types": [assignment.submission_type],
                "published": False,
            }
        )
        return result.id

    def create_discussion(self, discussion: Discussion, message_html: str) -> int:
        topic = self._course.create_discussion_topic(
            title=discussion.title,
            message=message_html,
            assignment={
                "points_possible": discussion.points,
                "due_at": discussion.due_datetime.isoformat(),
            },
            published=False,
        )
        return topic.id

    def add_module_item(self, module_id: int, item_type: str, content_id, title: str) -> None:
        module = self._course.get_module(module_id)
        item = {"type": item_type, "title": title}
        if item_type == "Page":
            item["page_url"] = content_id
        else:
            item["content_id"] = content_id
        module.create_module_item(module_item=item)

    def get_page(self, page_url: str):
        return self._course.get_page(page_url)

    def get_assignment(self, assignment_id: int):
        return self._course.get_assignment(assignment_id)

    def get_discussion(self, topic_id: int):
        return self._course.get_discussion_topic(topic_id)

    def update_page(self, page_url: str, **fields) -> None:
        page = self._course.get_page(page_url)
        page.edit(wiki_page=fields)

    def update_assignment(self, assignment_id: int, **fields) -> None:
        assignment = self._course.get_assignment(assignment_id)
        assignment.edit(assignment=fields)

    def update_discussion(self, topic_id: int, **fields) -> None:
        topic = self._course.get_discussion_topic(topic_id)
        topic.edit(**fields)

    def object_exists(self, getter, obj_id) -> bool:
        try:
            getter(obj_id)
            return True
        except ResourceDoesNotExist:
            return False
