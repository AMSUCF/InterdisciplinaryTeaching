# Canvas Sync Utility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI utility that syncs per-week markdown course content to UCF's Canvas LMS, with init/push/status/diff commands and a diff-and-confirm workflow for updates.

**Architecture:** A `canvas_sync` Python package with separate modules for config loading, markdown parsing, data models, Canvas API interactions, and diffing. The CLI uses `argparse` with subcommands. State is tracked in a local JSON file mapping week content to Canvas object IDs.

**Tech Stack:** Python 3.10+, canvasapi, python-frontmatter, pyyaml, markdown, rich, pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `canvas_sync/__init__.py` | Package marker |
| `canvas_sync/__main__.py` | CLI entry point with argparse subcommands |
| `canvas_sync/models.py` | Dataclasses: Week, Assignment, Discussion, Workshop |
| `canvas_sync/config.py` | Load and validate canvas_config.yaml |
| `canvas_sync/parser.py` | Parse week markdown files into model objects |
| `canvas_sync/canvas_api.py` | All Canvas interactions via canvasapi library |
| `canvas_sync/diff.py` | Compare local Week models against Canvas state, display diffs |
| `canvas_sync/state.py` | Load/save .canvas_sync_state.json |
| `requirements.txt` | Python dependencies |
| `tests/test_models.py` | Tests for data models |
| `tests/test_config.py` | Tests for config loading |
| `tests/test_parser.py` | Tests for markdown parsing |
| `tests/test_state.py` | Tests for state file load/save |
| `tests/test_diff.py` | Tests for diff logic |
| `tests/test_canvas_api.py` | Tests for Canvas API layer (mocked) |
| `tests/test_cli.py` | Tests for CLI argument parsing |
| `weeks/week-01.md` through `weeks/week-12.md` | Per-week course content split from index.md |

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `canvas_sync/__init__.py`
- Create: `canvas_config.example.yaml`
- Modify: `.gitignore` (create if absent)

- [ ] **Step 1: Create requirements.txt**

```
canvasapi>=3.0.0
python-frontmatter>=1.0.0
PyYAML>=6.0
Markdown>=3.4
rich>=13.0
pytest>=7.0
```

- [ ] **Step 2: Create canvas_sync/__init__.py**

```python
"""Canvas Sync — sync course markdown to UCF Canvas LMS."""
```

- [ ] **Step 3: Create canvas_config.example.yaml**

```yaml
api_url: https://webcourses.ucf.edu
api_key: YOUR_API_KEY_HERE
course_id: 123456
```

- [ ] **Step 4: Create .gitignore (or append if it exists)**

Add these lines:

```
canvas_config.yaml
.canvas_sync_state.json
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 5: Create empty tests directory**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 6: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 7: Commit**

```bash
git add requirements.txt canvas_sync/__init__.py canvas_config.example.yaml .gitignore tests/__init__.py
git commit -m "chore: scaffold canvas_sync project structure"
```

---

### Task 2: Data Models

**Files:**
- Create: `canvas_sync/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_models.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models.py -v
```

Expected: ImportError — `canvas_sync.models` does not exist yet.

- [ ] **Step 3: Implement models.py**

```python
# canvas_sync/models.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add canvas_sync/models.py tests/test_models.py
git commit -m "feat: add data models for Week, Assignment, Discussion, Workshop"
```

---

### Task 3: Config Loader

**Files:**
- Create: `canvas_sync/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config.py
import os
import pytest
from canvas_sync.config import load_config, Config


def test_load_config_from_file(tmp_path):
    config_file = tmp_path / "canvas_config.yaml"
    config_file.write_text(
        "api_url: https://webcourses.ucf.edu\n"
        "api_key: test-key-123\n"
        "course_id: 99999\n"
    )
    cfg = load_config(str(config_file))
    assert cfg.api_url == "https://webcourses.ucf.edu"
    assert cfg.api_key == "test-key-123"
    assert cfg.course_id == 99999


def test_load_config_missing_field(tmp_path):
    config_file = tmp_path / "canvas_config.yaml"
    config_file.write_text("api_url: https://webcourses.ucf.edu\n")
    with pytest.raises(KeyError):
        load_config(str(config_file))


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/canvas_config.yaml")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement config.py**

```python
# canvas_sync/config.py
from __future__ import annotations

from dataclasses import dataclass

import yaml


@dataclass
class Config:
    api_url: str
    api_key: str
    course_id: int


def load_config(path: str) -> Config:
    with open(path) as f:
        data = yaml.safe_load(f)
    return Config(
        api_url=data["api_url"],
        api_key=data["api_key"],
        course_id=data["course_id"],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add canvas_sync/config.py tests/test_config.py
git commit -m "feat: add config loader for canvas_config.yaml"
```

---

### Task 4: State File Manager

**Files:**
- Create: `canvas_sync/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_state.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement state.py**

```python
# canvas_sync/state.py
from __future__ import annotations

import json
import os
from typing import Optional


class SyncState:
    def __init__(self, path: str):
        self._path = path
        self._data: dict = {}
        if os.path.exists(path):
            with open(path) as f:
                self._data = json.load(f)

    def get_week(self, key: str) -> Optional[dict]:
        return self._data.get(key)

    def set_week(self, key: str, value: dict) -> None:
        self._data[key] = value

    def all_weeks(self) -> dict:
        return dict(self._data)

    def save(self) -> None:
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_state.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add canvas_sync/state.py tests/test_state.py
git commit -m "feat: add state file manager for tracking Canvas IDs"
```

---

### Task 5: Markdown Parser

**Files:**
- Create: `canvas_sync/parser.py`
- Create: `tests/test_parser.py`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_parser.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement parser.py**

```python
# canvas_sync/parser.py
from __future__ import annotations

import glob
import os
from typing import Optional

import frontmatter

from canvas_sync.models import Assignment, Discussion, Week, Workshop


def parse_week_file(path: str) -> Week:
    post = frontmatter.load(path)
    meta = post.metadata

    workshop: Optional[Workshop] = None
    if "workshop" in meta:
        workshop = Workshop.from_dict(meta["workshop"])

    assignments: list[Assignment] = []
    if "assignments" in meta:
        assignments = [Assignment.from_dict(a) for a in meta["assignments"]]

    discussion: Optional[Discussion] = None
    if "discussion" in meta:
        discussion = Discussion.from_dict(meta["discussion"])

    return Week(
        week=meta["week"],
        title=meta["title"],
        starts=str(meta["starts"]),
        body_markdown=post.content,
        workshop=workshop,
        assignments=assignments,
        discussion=discussion,
    )


def load_all_weeks(weeks_dir: str) -> list[Week]:
    pattern = os.path.join(weeks_dir, "week-*.md")
    files = sorted(glob.glob(pattern))
    return sorted(
        [parse_week_file(f) for f in files],
        key=lambda w: w.week,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_parser.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add canvas_sync/parser.py tests/test_parser.py
git commit -m "feat: add markdown parser for week files"
```

---

### Task 6: Split index.md into Week Files

**Files:**
- Create: `weeks/week-01.md` through `weeks/week-12.md`

This task is manual content extraction from `index.md`. Each week section becomes its own file with appropriate frontmatter. The `index.md` stays as-is for the Jekyll site.

- [ ] **Step 1: Create weeks directory**

```bash
mkdir -p weeks
```

- [ ] **Step 2: Create week-01.md**

```markdown
---
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
    type: assignment
    points: 50
    due: 2026-05-15
discussion:
  title: "Introduce yourself and describe your teaching experience"
  points: 30
  due: 2026-05-17
---

## Readings

- Locke, Brandon. ["Digital Humanities Pedagogy as Essential Liberal Education: A Framework for Curriculum Development."](https://www.digitalhumanities.org/dhq/vol/11/3/000303/000303.html) *DHQ: Digital Humanities Quarterly* 11.3 (2017).
- Croxall, Brian and Diane K. Jakacki. ["What We Teach When We Teach DH."](https://dhdebates.gc.cuny.edu/read/what-we-teach-when-we-teach-dh/section/c2790674-f5bb-41b7-9938-a47a4d2fb308#intro) *What We Teach When We Teach DH.*
- Mollick, Ethan. ["My class required AI. Here's what I've learned so far."](https://www.oneusefulthing.org/p/my-class-required-ai-heres-what-ive) *One Useful Thing.*

## Discussion Prompt

Introduce yourself and describe your teaching experience (current or anticipated). What courses do you teach or hope to teach? What is your initial relationship with AI tools in your own work?
```

- [ ] **Step 3: Create week-02.md through week-12.md**

Follow the same pattern for each week, extracting from `index.md`:
- `week` number, `title` from the `### Week N:` heading
- `starts` date from the heading parenthetical
- `workshop` (if the week has an italicized NEH Workshop line)
- `assignments` (if the week has a `**Due:**` line with point values — cross-reference the Evaluation table)
- `discussion` (if the week has a `**Discussion:**` line — 30 points each per the Evaluation table)
- Readings go under `## Readings`
- Discussion description goes under `## Discussion Prompt`

Key data from the syllabus Evaluation table for due dates and points:

| Week | Assignments | Discussion |
|------|------------|------------|
| 1 | Activity Verification (50 pts, May 15) | Yes (30 pts) |
| 2 | — | Yes (30 pts) |
| 3 | — | Yes (30 pts) |
| 4 | — | Yes (30 pts) |
| 5 | — | Yes (30 pts) |
| 6 | — | Yes (30 pts) |
| 7 | — | Yes (30 pts) |
| 8 | Signature Assignment (200 pts, July 5) | — |
| 9 | — | Yes (30 pts) |
| 10 | Course Syllabus (200 pts, July 19) | — |
| 11 | Teaching Statement (150 pts, July 26) | — |
| 12 | Final Portfolio & Reflection (160 pts, Aug 1) | — |

Discussion due dates: Sunday of each module week (the `starts` date + 6 days).

- [ ] **Step 4: Verify parsing works**

```bash
python -c "from canvas_sync.parser import load_all_weeks; weeks = load_all_weeks('weeks'); print(f'{len(weeks)} weeks loaded'); [print(f'  {w.module_name}') for w in weeks]"
```

Expected: 12 weeks listed in order.

- [ ] **Step 5: Commit**

```bash
git add weeks/
git commit -m "content: split index.md into per-week markdown files with frontmatter"
```

---

### Task 7: Canvas API Layer

**Files:**
- Create: `canvas_sync/canvas_api.py`
- Create: `tests/test_canvas_api.py`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_canvas_api.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement canvas_api.py**

```python
# canvas_sync/canvas_api.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_canvas_api.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add canvas_sync/canvas_api.py tests/test_canvas_api.py
git commit -m "feat: add Canvas API layer using canvasapi library"
```

---

### Task 8: Diff Engine

**Files:**
- Create: `canvas_sync/diff.py`
- Create: `tests/test_diff.py`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_diff.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement diff.py**

```python
# canvas_sync/diff.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from rich.console import Console
from rich.table import Table


@dataclass
class FieldDiff:
    field: str
    old_value: Any
    new_value: Any


def compute_diff(local: dict, remote: dict) -> list[FieldDiff]:
    diffs = []
    for key, local_val in local.items():
        remote_val = remote.get(key)
        if local_val != remote_val:
            diffs.append(FieldDiff(field=key, old_value=remote_val, new_value=local_val))
    return diffs


def display_diff(object_label: str, diffs: list[FieldDiff], console: Optional[Console] = None) -> None:
    if console is None:
        console = Console()
    if not diffs:
        console.print(f"  [green]{object_label}: no changes[/green]")
        return
    console.print(f"\n  [bold]{object_label}:[/bold]")
    for d in diffs:
        console.print(f"    [red]{d.field}:[/red] {d.old_value} [yellow]→[/yellow] {d.new_value}")


def prompt_confirm(object_label: str) -> str:
    """Prompt user for confirmation. Returns 'y', 'n', 'a', or 'q'."""
    while True:
        response = input(f"  Apply update to {object_label}? [y/n/a(ll)/q(uit)] ").strip().lower()
        if response in ("y", "n", "a", "q"):
            return response
        print("  Please enter y, n, a, or q.")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_diff.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add canvas_sync/diff.py tests/test_diff.py
git commit -m "feat: add diff engine for comparing local vs Canvas state"
```

---

### Task 9: CLI Entry Point

**Files:**
- Create: `canvas_sync/__main__.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cli.py
from canvas_sync.__main__ import build_parser


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cli.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement __main__.py**

```python
# canvas_sync/__main__.py
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table

from canvas_sync.config import load_config
from canvas_sync.parser import load_all_weeks, parse_week_file
from canvas_sync.canvas_api import CanvasSync
from canvas_sync.diff import compute_diff, display_diff, prompt_confirm
from canvas_sync.state import SyncState

console = Console()

DEFAULT_CONFIG = "canvas_config.yaml"
DEFAULT_WEEKS_DIR = "weeks"
DEFAULT_STATE_FILE = ".canvas_sync_state.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="canvas_sync",
        description="Sync course markdown to Canvas LMS",
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to config YAML")
    parser.add_argument("--weeks-dir", default=DEFAULT_WEEKS_DIR, help="Path to weeks directory")
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE, help="Path to state JSON")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create empty modules in Canvas for all weeks")

    push_p = sub.add_parser("push", help="Push week content to Canvas")
    push_group = push_p.add_mutually_exclusive_group(required=True)
    push_group.add_argument("--all", action="store_true", help="Push all weeks")
    push_group.add_argument("--week", type=int, help="Push a specific week number")
    push_p.add_argument("--force", action="store_true", help="Skip confirmation prompts")

    status_p = sub.add_parser("status", help="Show sync status for all weeks")

    diff_p = sub.add_parser("diff", help="Preview changes without pushing")
    diff_group = diff_p.add_mutually_exclusive_group(required=True)
    diff_group.add_argument("--all", action="store_true", help="Diff all weeks")
    diff_group.add_argument("--week", type=int, help="Diff a specific week number")

    return parser


def cmd_init(config, weeks_dir, state: SyncState):
    cs = CanvasSync(config)
    weeks = load_all_weeks(weeks_dir)
    console.print(f"Creating {len(weeks)} modules in Canvas...")
    for week in weeks:
        module_id = cs.create_module(week)
        week_state = state.get_week(week.file_key) or {}
        week_state["module_id"] = module_id
        week_state["last_synced"] = datetime.now().isoformat()
        state.set_week(week.file_key, week_state)
        state.save()
        console.print(f"  [green]✓[/green] {week.module_name} (module_id={module_id})")
    console.print("[bold green]Init complete.[/bold green]")


def _push_week(cs: CanvasSync, week, state: SyncState, force: bool):
    week_key = week.file_key
    week_state = state.get_week(week_key) or {}
    apply_all = force

    console.print(f"\n[bold]Pushing {week.module_name}...[/bold]")

    # Module
    if "module_id" not in week_state:
        module_id = cs.create_module(week)
        week_state["module_id"] = module_id
        console.print(f"  [green]Created module[/green] (id={module_id})")

    module_id = week_state["module_id"]

    # Page
    if "page_url" not in week_state:
        page_url = cs.create_page(week)
        week_state["page_url"] = page_url
        cs.add_module_item(module_id, "Page", page_url, week.module_name)
        console.print(f"  [green]Created page[/green] (url={page_url})")
    else:
        page = cs.get_page(week_state["page_url"])
        local_fields = {"title": week.module_name, "body": week.body_html}
        remote_fields = {"title": page.title, "body": page.body or ""}
        diffs = compute_diff(local_fields, remote_fields)
        if diffs:
            display_diff(f"Page \"{week.module_name}\"", diffs, console)
            if apply_all or _confirm(f"Page \"{week.module_name}\"", apply_all_ref=[apply_all]):
                cs.update_page(week_state["page_url"], **local_fields)
                console.print("  [green]Updated page[/green]")

    # Assignments
    existing_assignments = {a["title"]: a for a in week_state.get("assignments", [])}
    new_assignments = []
    for assignment in week.assignments:
        if assignment.title not in existing_assignments:
            aid = cs.create_assignment(assignment)
            new_assignments.append({"title": assignment.title, "canvas_id": aid})
            cs.add_module_item(module_id, "Assignment", aid, assignment.title)
            console.print(f"  [green]Created assignment[/green] \"{assignment.title}\" (id={aid})")
        else:
            entry = existing_assignments[assignment.title]
            canvas_a = cs.get_assignment(entry["canvas_id"])
            local_fields = {
                "name": assignment.title,
                "points_possible": assignment.points,
                "due_at": assignment.due_datetime.isoformat(),
            }
            remote_fields = {
                "name": getattr(canvas_a, "name", ""),
                "points_possible": getattr(canvas_a, "points_possible", 0),
                "due_at": getattr(canvas_a, "due_at", ""),
            }
            diffs = compute_diff(local_fields, remote_fields)
            if diffs:
                display_diff(f"Assignment \"{assignment.title}\"", diffs, console)
                if apply_all or _confirm(f"Assignment \"{assignment.title}\"", apply_all_ref=[apply_all]):
                    cs.update_assignment(entry["canvas_id"], **local_fields)
                    console.print(f"  [green]Updated assignment[/green] \"{assignment.title}\"")
            new_assignments.append(entry)
    week_state["assignments"] = new_assignments

    # Discussion
    if week.discussion:
        prompt_html = week.discussion_prompt_html or ""
        if "discussion_id" not in week_state:
            did = cs.create_discussion(week.discussion, prompt_html)
            week_state["discussion_id"] = did
            cs.add_module_item(module_id, "Discussion", did, week.discussion.title)
            console.print(f"  [green]Created discussion[/green] \"{week.discussion.title}\" (id={did})")
        else:
            topic = cs.get_discussion(week_state["discussion_id"])
            local_fields = {
                "title": week.discussion.title,
                "message": prompt_html,
            }
            remote_fields = {
                "title": getattr(topic, "title", ""),
                "message": getattr(topic, "message", ""),
            }
            diffs = compute_diff(local_fields, remote_fields)
            if diffs:
                display_diff(f"Discussion \"{week.discussion.title}\"", diffs, console)
                if apply_all or _confirm(f"Discussion \"{week.discussion.title}\"", apply_all_ref=[apply_all]):
                    cs.update_discussion(week_state["discussion_id"], **local_fields)
                    console.print(f"  [green]Updated discussion[/green]")

    week_state["last_synced"] = datetime.now().isoformat()
    state.set_week(week_key, week_state)
    state.save()


def _confirm(label: str, apply_all_ref: list) -> bool:
    if apply_all_ref[0]:
        return True
    response = prompt_confirm(label)
    if response == "y":
        return True
    if response == "a":
        apply_all_ref[0] = True
        return True
    if response == "q":
        console.print("[yellow]Aborted.[/yellow]")
        sys.exit(0)
    return False


def cmd_push(config, weeks_dir, state: SyncState, week_num=None, all_weeks=False, force=False):
    cs = CanvasSync(config)
    if all_weeks:
        weeks = load_all_weeks(weeks_dir)
    else:
        path = os.path.join(weeks_dir, f"week-{week_num:02d}.md")
        if not os.path.exists(path):
            console.print(f"[red]File not found: {path}[/red]")
            sys.exit(1)
        weeks = [parse_week_file(path)]

    for week in weeks:
        _push_week(cs, week, state, force)
    console.print("\n[bold green]Push complete.[/bold green]")


def cmd_status(config, weeks_dir, state: SyncState):
    weeks = load_all_weeks(weeks_dir)
    table = Table(title="Canvas Sync Status")
    table.add_column("Week", style="bold")
    table.add_column("Module")
    table.add_column("Page")
    table.add_column("Assignments")
    table.add_column("Discussion")
    table.add_column("Last Synced")

    for week in weeks:
        ws = state.get_week(week.file_key)
        if ws is None:
            table.add_row(week.module_name, "—", "—", "—", "—", "never")
        else:
            module = f"[green]✓[/green] {ws.get('module_id', '—')}" if "module_id" in ws else "—"
            page = f"[green]✓[/green]" if "page_url" in ws else "—"
            assigns = str(len(ws.get("assignments", []))) if ws.get("assignments") else "—"
            disc = f"[green]✓[/green]" if "discussion_id" in ws else "—"
            synced = ws.get("last_synced", "never")
            table.add_row(week.module_name, module, page, assigns, disc, synced)

    console.print(table)


def cmd_diff(config, weeks_dir, state: SyncState, week_num=None, all_weeks=False):
    cs = CanvasSync(config)
    if all_weeks:
        weeks = load_all_weeks(weeks_dir)
    else:
        path = os.path.join(weeks_dir, f"week-{week_num:02d}.md")
        if not os.path.exists(path):
            console.print(f"[red]File not found: {path}[/red]")
            sys.exit(1)
        weeks = [parse_week_file(path)]

    any_changes = False
    for week in weeks:
        ws = state.get_week(week.file_key)
        if ws is None:
            console.print(f"\n[bold]{week.module_name}:[/bold] [yellow]not yet pushed[/yellow]")
            any_changes = True
            continue

        console.print(f"\n[bold]{week.module_name}:[/bold]")

        if "page_url" in ws:
            page = cs.get_page(ws["page_url"])
            local_fields = {"title": week.module_name, "body": week.body_html}
            remote_fields = {"title": page.title, "body": page.body or ""}
            diffs = compute_diff(local_fields, remote_fields)
            if diffs:
                any_changes = True
            display_diff("Page", diffs, console)

        existing_assignments = {a["title"]: a for a in ws.get("assignments", [])}
        for assignment in week.assignments:
            if assignment.title not in existing_assignments:
                console.print(f"  [yellow]New assignment: \"{assignment.title}\"[/yellow]")
                any_changes = True
            else:
                entry = existing_assignments[assignment.title]
                canvas_a = cs.get_assignment(entry["canvas_id"])
                local_fields = {
                    "name": assignment.title,
                    "points_possible": assignment.points,
                    "due_at": assignment.due_datetime.isoformat(),
                }
                remote_fields = {
                    "name": getattr(canvas_a, "name", ""),
                    "points_possible": getattr(canvas_a, "points_possible", 0),
                    "due_at": getattr(canvas_a, "due_at", ""),
                }
                diffs = compute_diff(local_fields, remote_fields)
                if diffs:
                    any_changes = True
                display_diff(f"Assignment \"{assignment.title}\"", diffs, console)

        if week.discussion and "discussion_id" in ws:
            topic = cs.get_discussion(ws["discussion_id"])
            prompt_html = week.discussion_prompt_html or ""
            local_fields = {"title": week.discussion.title, "message": prompt_html}
            remote_fields = {"title": getattr(topic, "title", ""), "message": getattr(topic, "message", "")}
            diffs = compute_diff(local_fields, remote_fields)
            if diffs:
                any_changes = True
            display_diff(f"Discussion \"{week.discussion.title}\"", diffs, console)
        elif week.discussion and "discussion_id" not in ws:
            console.print(f"  [yellow]New discussion: \"{week.discussion.title}\"[/yellow]")
            any_changes = True

    if not any_changes:
        console.print("\n[green]Everything is up to date.[/green]")


def main():
    parser = build_parser()
    args = parser.parse_args()

    config = load_config(args.config)
    state = SyncState(args.state_file)

    if args.command == "init":
        cmd_init(config, args.weeks_dir, state)
    elif args.command == "push":
        cmd_push(config, args.weeks_dir, state, week_num=args.week, all_weeks=args.all, force=args.force)
    elif args.command == "status":
        cmd_status(config, args.weeks_dir, state)
    elif args.command == "diff":
        cmd_diff(config, args.weeks_dir, state, week_num=args.week, all_weeks=args.all)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cli.py -v
```

Expected: All PASS.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests across all test files PASS.

- [ ] **Step 6: Commit**

```bash
git add canvas_sync/__main__.py tests/test_cli.py
git commit -m "feat: add CLI entry point with init, push, status, diff commands"
```

---

### Task 10: End-to-End Smoke Test

**Files:**
- No new files — uses existing week files and a mock config

- [ ] **Step 1: Verify week files parse correctly**

```bash
python -c "
from canvas_sync.parser import load_all_weeks
weeks = load_all_weeks('weeks')
print(f'{len(weeks)} weeks loaded')
for w in weeks:
    print(f'  {w.module_name}')
    print(f'    assignments: {[a.title for a in w.assignments]}')
    print(f'    discussion: {w.discussion.title if w.discussion else None}')
    print(f'    workshop: {w.workshop.title if w.workshop else None}')
"
```

Expected: 12 weeks listed with correct assignments, discussions, and workshops matching the syllabus.

- [ ] **Step 2: Verify CLI help works**

```bash
python -m canvas_sync --help
python -m canvas_sync push --help
python -m canvas_sync diff --help
```

Expected: Help text displayed for each command with correct arguments.

- [ ] **Step 3: Verify status command works without Canvas connection**

```bash
python -m canvas_sync status --weeks-dir weeks --state-file /tmp/test_state.json
```

Expected: Table showing all 12 weeks with "never" for last synced (no state file exists yet).

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: address issues found during smoke testing"
```

(Skip this step if no fixes were needed.)
