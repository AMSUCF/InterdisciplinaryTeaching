# tests/test_parser.py
import os
import pytest
from canvas_sync.parser import parse_week_file, load_all_weeks


SAMPLE_WEEK_MD = """---
week: 1
title: "Welcome and Interdisciplinary Teaching"
starts: 2026-05-11
workshop:
  title: "Workshop 1: Introducing AI for DH Pedagogy"
  date: 2026-05-13
  time: "10 AM - noon"
  location: CHDR
assignments:
  - title: "Activity Verification"
    points: 50
    due: 2026-05-15
discussion:
  title: "Introduce yourself"
  points: 30
  due: 2026-05-17
---

## Readings

- Locke, Brandon. "Digital Humanities Pedagogy."

## Discussion Prompt

Introduce yourself and describe your teaching experience.
"""

SAMPLE_NO_OPTIONAL = """---
week: 8
title: "Imagining the Syllabus"
starts: 2026-06-29
assignments:
  - title: "Signature Assignment"
    points: 200
    due: 2026-07-05
---

## Readings

- Cohen, Scott. "Digital Humanities across the Curriculum."
"""


def test_parse_week_file_full(tmp_path):
    f = tmp_path / "week-01.md"
    f.write_text(SAMPLE_WEEK_MD)
    week = parse_week_file(str(f))
    assert week.week == 1
    assert week.title == "Welcome and Interdisciplinary Teaching"
    assert week.starts == "2026-05-11"
    assert week.workshop is not None
    assert week.workshop.title == "Workshop 1: Introducing AI for DH Pedagogy"
    assert len(week.assignments) == 1
    assert week.assignments[0].title == "Activity Verification"
    assert week.assignments[0].points == 50
    assert week.discussion is not None
    assert week.discussion.title == "Introduce yourself"
    assert "Digital Humanities Pedagogy" in week.body_markdown


def test_parse_week_file_no_optional(tmp_path):
    f = tmp_path / "week-08.md"
    f.write_text(SAMPLE_NO_OPTIONAL)
    week = parse_week_file(str(f))
    assert week.week == 8
    assert week.workshop is None
    assert week.discussion is None
    assert len(week.assignments) == 1


def test_load_all_weeks_sorted(tmp_path):
    (tmp_path / "week-03.md").write_text(SAMPLE_NO_OPTIONAL.replace("week: 8", "week: 3"))
    (tmp_path / "week-01.md").write_text(SAMPLE_WEEK_MD)
    weeks = load_all_weeks(str(tmp_path))
    assert len(weeks) == 2
    assert weeks[0].week == 1
    assert weeks[1].week == 3


def test_load_all_weeks_ignores_non_week_files(tmp_path):
    (tmp_path / "week-01.md").write_text(SAMPLE_WEEK_MD)
    (tmp_path / "README.md").write_text("# Not a week file")
    weeks = load_all_weeks(str(tmp_path))
    assert len(weeks) == 1


SAMPLE_WITH_SLIDES = """---
week: 1
title: "Welcome and Interdisciplinary Teaching"
starts: 2026-05-11
slides: week-01
assignments:
  - title: "Activity Verification"
    points: 50
    due: 2026-05-15
---

## Readings

- Some reading
"""


def test_parse_week_file_with_slides(tmp_path):
    f = tmp_path / "week-01.md"
    f.write_text(SAMPLE_WITH_SLIDES)
    week = parse_week_file(str(f))
    assert week.slides == "week-01"


def test_parse_week_file_without_slides_defaults_none(tmp_path):
    f = tmp_path / "week-01.md"
    f.write_text(SAMPLE_WEEK_MD)  # SAMPLE_WEEK_MD does not contain a `slides:` field
    week = parse_week_file(str(f))
    assert week.slides is None
