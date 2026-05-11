import os
import subprocess
import pytest

from canvas_sync.live import is_live, head_is_live, _content_is_live


LIVE_CONTENT = """---
week: 1
title: "Welcome"
starts: 2026-05-11
live: true
---

Body.
"""

DRAFT_CONTENT = """---
week: 2
title: "Learning Theories"
starts: 2026-05-18
---

Body.
"""

EXPLICIT_FALSE_CONTENT = """---
week: 3
title: "Textual Analysis"
starts: 2026-05-25
live: false
---

Body.
"""


def test_content_is_live_true():
    assert _content_is_live(LIVE_CONTENT) is True


def test_content_is_live_missing():
    assert _content_is_live(DRAFT_CONTENT) is False


def test_content_is_live_explicit_false():
    assert _content_is_live(EXPLICIT_FALSE_CONTENT) is False


def test_content_is_live_handles_garbage():
    # No frontmatter, no `live:` — must return False, not raise.
    assert _content_is_live("not frontmatter at all") is False


def test_is_live_reads_disk(tmp_path):
    f = tmp_path / "week-01.md"
    f.write_text(LIVE_CONTENT)
    assert is_live(str(f)) is True


def test_is_live_returns_false_for_missing_file(tmp_path):
    assert is_live(str(tmp_path / "does-not-exist.md")) is False


def _init_repo(tmp_path):
    """Initialize a fresh git repo in tmp_path for hook-related tests."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "init.defaultBranch", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, check=True)


def _commit(tmp_path, msg):
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=tmp_path, check=True)


def test_head_is_live_true_when_head_marks_live(tmp_path):
    _init_repo(tmp_path)
    weeks = tmp_path / "weeks"
    weeks.mkdir()
    (weeks / "week-01.md").write_text(LIVE_CONTENT)
    _commit(tmp_path, "init")
    assert head_is_live("weeks/week-01.md", repo_root=str(tmp_path)) is True


def test_head_is_live_false_when_head_is_draft(tmp_path):
    _init_repo(tmp_path)
    weeks = tmp_path / "weeks"
    weeks.mkdir()
    (weeks / "week-01.md").write_text(DRAFT_CONTENT)
    _commit(tmp_path, "init")
    assert head_is_live("weeks/week-01.md", repo_root=str(tmp_path)) is False


def test_head_is_live_false_for_promotion_commit(tmp_path):
    """Simulate the promotion commit: HEAD has draft, working tree has live."""
    _init_repo(tmp_path)
    weeks = tmp_path / "weeks"
    weeks.mkdir()
    (weeks / "week-01.md").write_text(DRAFT_CONTENT)
    _commit(tmp_path, "init")
    # Now stage the promotion (but don't commit yet)
    (weeks / "week-01.md").write_text(LIVE_CONTENT)
    subprocess.run(["git", "add", "weeks/week-01.md"], cwd=tmp_path, check=True)
    # head_is_live looks at HEAD, not the staged version
    assert head_is_live("weeks/week-01.md", repo_root=str(tmp_path)) is False


def test_head_is_live_false_for_new_file(tmp_path):
    """File that exists in working tree but not in HEAD is not live."""
    _init_repo(tmp_path)
    (tmp_path / "placeholder.txt").write_text("x")
    _commit(tmp_path, "init")
    weeks = tmp_path / "weeks"
    weeks.mkdir()
    (weeks / "week-13.md").write_text(LIVE_CONTENT)
    assert head_is_live("weeks/week-13.md", repo_root=str(tmp_path)) is False
