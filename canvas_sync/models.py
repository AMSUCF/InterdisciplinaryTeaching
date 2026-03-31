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
    submission_type: str = "online_text_entry"

    @classmethod
    def from_dict(cls, data: dict) -> Assignment:
        return cls(
            title=data["title"],
            points=data["points"],
            due=str(data["due"]),
            submission_type=data.get("submission_type", "online_text_entry"),
        )

    @property
    def due_datetime(self) -> datetime:
        date = datetime.strptime(self.due, "%Y-%m-%d")
        return date.replace(hour=23, minute=59, second=0, tzinfo=EASTERN)


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

    @property
    def module_name(self) -> str:
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

    @property
    def file_key(self) -> str:
        return f"week-{self.week:02d}"
