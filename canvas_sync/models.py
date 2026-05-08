from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import markdown
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("US/Eastern")


@dataclass
class Workshop:
    title: str
    date: str
    time: str
    location: str

    @classmethod
    def from_dict(cls, data: dict) -> Workshop:
        return cls(
            title=data["title"],
            date=str(data["date"]),
            time=data["time"],
            location=data["location"],
        )


@dataclass
class Assignment:
    title: str
    points: int
    due: str
    course_start: str = ""
    description: str = ""
    submission_type: str = "online_upload"

    @classmethod
    def from_dict(cls, data: dict, course_start: str = "") -> Assignment:
        return cls(
            title=data["title"],
            points=data["points"],
            due=str(data["due"]),
            course_start=course_start,
            description=data.get("description", ""),
            submission_type=data.get("submission_type", "online_upload"),
        )

    @property
    def due_datetime(self) -> datetime:
        date = datetime.strptime(self.due, "%Y-%m-%d")
        return date.replace(hour=23, minute=59, second=0, tzinfo=EASTERN)

    @property
    def unlock_datetime(self) -> datetime:
        from datetime import timedelta
        three_weeks_before = self.due_datetime - timedelta(weeks=3)
        if self.course_start:
            course_start_dt = datetime.strptime(self.course_start, "%Y-%m-%d")
            course_start_dt = course_start_dt.replace(hour=0, minute=0, second=0, tzinfo=EASTERN)
            if three_weeks_before < course_start_dt:
                return course_start_dt
        return three_weeks_before

    @property
    def lock_datetime(self) -> datetime:
        from datetime import timedelta
        return self.due_datetime + timedelta(weeks=1)


@dataclass
class Discussion:
    title: str
    points: int
    due: str

    @classmethod
    def from_dict(cls, data: dict) -> Discussion:
        return cls(
            title=data["title"],
            points=data["points"],
            due=str(data["due"]),
        )

    @property
    def due_datetime(self) -> datetime:
        date = datetime.strptime(self.due, "%Y-%m-%d")
        return date.replace(hour=23, minute=59, second=0, tzinfo=EASTERN)


@dataclass
class Week:
    week: int
    title: str
    starts: str
    body_markdown: str
    workshop: Optional[Workshop]
    assignments: list[Assignment] = field(default_factory=list)
    discussion: Optional[Discussion] = None
    slides: Optional[str] = None

    @property
    def module_name(self) -> str:
        if self.week == 0:
            return self.title
        return f"Week {self.week}: {self.title}"

    @property
    def body_html(self) -> str:
        md = markdown.Markdown(extensions=["tables", "fenced_code"])
        return md.convert(self.body_markdown)

    @property
    def discussion_prompt_html(self) -> Optional[str]:
        match = re.split(r"^## Discussion Prompt\s*$", self.body_markdown, flags=re.MULTILINE)
        if len(match) < 2:
            return None
        prompt_md = match[1]
        # Stop at next ## heading if any
        next_heading = re.split(r"^## ", prompt_md, flags=re.MULTILINE)
        prompt_md = next_heading[0].strip()
        md = markdown.Markdown(extensions=["tables", "fenced_code"])
        return md.convert(prompt_md)

    def slides_section_html(self, base_url: str) -> Optional[str]:
        """Render the iframe block to embed the deck in a Canvas page.

        Returns None when no slide deck is configured for this week.
        Inline styles are used (not classes) because Canvas strips
        unknown CSS classes from page bodies.
        """
        if not self.slides:
            return None
        url = f"{base_url.rstrip('/')}/{self.slides}/"
        return (
            "<h2>Slides</h2>\n"
            '<div class="slides-embed" style="position:relative; '
            'padding-bottom:56.25%; height:0; overflow:hidden; max-width:100%;">\n'
            f'  <iframe src="{url}" '
            'style="position:absolute; top:0; left:0; width:100%; height:100%; border:0;" '
            'allowfullscreen loading="lazy" title="Week Slides"></iframe>\n'
            "</div>\n"
            f'<p><a href="{url}" target="_blank" rel="noopener">Open slides in a new tab</a></p>\n'
        )

    @property
    def file_key(self) -> str:
        return f"week-{self.week:02d}"
