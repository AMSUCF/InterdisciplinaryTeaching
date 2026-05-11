# Live Weeks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-week `live` flag with two enforcement points — `canvas_sync push --override-live` for Canvas, and a `commit-msg` git hook for local edits — so that already-published weeks can't be silently overwritten.

**Architecture:** A `live: bool` field on each week's YAML frontmatter is read by `canvas_sync/parser.py` into the existing `Week` model. A new tiny module `canvas_sync/live.py` exposes `is_live(path)` and `head_is_live(path)` (the latter via `git show HEAD:<path>`) and is shared by the `push` guardrail and the git hook. The hook reads `HEAD`'s frontmatter so promoting a week to live is not itself blocked.

**Tech Stack:** Python 3.10+, `python-frontmatter` (already a dependency), `pytest` (existing), git hooks via `core.hooksPath`.

**Spec:** `docs/superpowers/specs/2026-05-11-live-weeks-design.md`

**Spec deviation flagged up-front:** The spec called this a "pre-commit hook," but `pre-commit` does not have access to the commit message — and we need to check whether the message contains `[live-edit]`. The correct git hook is `commit-msg`, which receives both the staged file list (via `git diff --cached --name-only`) and the commit message file path as `$1`. The hook lives at `.githooks/commit-msg`. Behavior, override semantics, and installation step are otherwise exactly as specified.

---

## File Structure

**New files:**
- `canvas_sync/live.py` — `is_live()`, `head_is_live()`, `_content_is_live()` (private parser helper).
- `tests/test_live.py` — tests for the three helpers, including a `tmp_path`-based git fixture.
- `.githooks/commit-msg` — Python script (shebang `#!/usr/bin/env python3`) that runs on every commit, reads staged `weeks/week-*.md` paths, and blocks the commit if any were live in HEAD and `[live-edit]` is not in the commit message.

**Modified files:**
- `canvas_sync/models.py` — add `live: bool = False` to `Week`.
- `canvas_sync/parser.py` — read `live` from frontmatter into `Week`.
- `canvas_sync/__main__.py` — add `--override-live` flag to `push`; add `_filter_live_weeks()` helper; wire into `cmd_push`; add "Live" column to `cmd_status`.
- `tests/test_models.py` — assert `Week.live` default is `False`.
- `tests/test_parser.py` — assert parser reads `live` (both true and absent).
- `tests/test_cli.py` — assert `--override-live` is parsed; assert `_filter_live_weeks()` behavior.
- `README.md` — add "Live weeks" section.
- `weeks/week-01.md` — gain `live: true` in frontmatter (separate, final commit).

---

## Task 1: Add `live` field to the `Week` model

**Files:**
- Modify: `canvas_sync/models.py:94-102`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_models.py`:

```python
def test_week_live_default_false():
    w = Week(
        week=2,
        title="Learning Theories",
        starts="2026-05-18",
        body_markdown="## Readings",
        workshop=None,
        assignments=[],
        discussion=None,
    )
    assert w.live is False


def test_week_live_can_be_set_true():
    w = Week(
        week=1,
        title="Welcome",
        starts="2026-05-11",
        body_markdown="## Readings",
        workshop=None,
        assignments=[],
        discussion=None,
        live=True,
    )
    assert w.live is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_models.py::test_week_live_default_false tests/test_models.py::test_week_live_can_be_set_true -v`

Expected: FAIL with `TypeError: Week.__init__() got an unexpected keyword argument 'live'` (second test) and `AttributeError` (first).

- [ ] **Step 3: Add the field to `Week`**

In `canvas_sync/models.py`, locate the `Week` dataclass (around line 94). Add `live: bool = False` after the `slides` field:

```python
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
    live: bool = False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`

Expected: all tests pass, including the two new ones.

- [ ] **Step 5: Commit**

```bash
git add canvas_sync/models.py tests/test_models.py
git commit -m "feat(models): add live flag to Week model"
```

---

## Task 2: Parser reads `live` from frontmatter

**Files:**
- Modify: `canvas_sync/parser.py:59-68`
- Test: `tests/test_parser.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_parser.py`:

```python
SAMPLE_LIVE = """---
week: 1
title: "Welcome"
starts: 2026-05-11
live: true
assignments:
  - title: "Activity Verification"
    points: 50
    due: 2026-05-15
---

## Readings

- Reading
"""


def test_parse_week_file_with_live_true(tmp_path):
    f = tmp_path / "week-01.md"
    f.write_text(SAMPLE_LIVE)
    week = parse_week_file(str(f))
    assert week.live is True


def test_parse_week_file_without_live_defaults_false(tmp_path):
    f = tmp_path / "week-01.md"
    f.write_text(SAMPLE_WEEK_MD)  # SAMPLE_WEEK_MD has no `live:` field
    week = parse_week_file(str(f))
    assert week.live is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_parser.py::test_parse_week_file_with_live_true tests/test_parser.py::test_parse_week_file_without_live_defaults_false -v`

Expected: FAIL — `test_parse_week_file_with_live_true` will fail because parser is not yet reading `live`, so `week.live` will be `False` even when `live: true` is in the frontmatter.

- [ ] **Step 3: Update `parse_week_file`**

In `canvas_sync/parser.py`, modify the `Week(...)` constructor call at the end of `parse_week_file` to pass `live`:

```python
    return Week(
        week=meta["week"],
        title=meta["title"],
        starts=str(meta["starts"]),
        body_markdown=post.content,
        workshop=workshop,
        assignments=assignments,
        discussion=discussion,
        slides=meta.get("slides"),
        live=bool(meta.get("live", False)),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_parser.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add canvas_sync/parser.py tests/test_parser.py
git commit -m "feat(parser): read live flag from week frontmatter"
```

---

## Task 3: Create `canvas_sync/live.py` with `is_live()` and `head_is_live()`

**Files:**
- Create: `canvas_sync/live.py`
- Create: `tests/test_live.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_live.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_live.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'canvas_sync.live'`.

- [ ] **Step 3: Create `canvas_sync/live.py`**

Write the file:

```python
"""Helpers for the live-week guardrail.

`is_live(path)` inspects the file on disk; `head_is_live(path)` inspects
the version at `git HEAD`. Both surface a single boolean: was this week
marked `live: true` in its YAML frontmatter? Used by both the
`canvas_sync push` guardrail and the `.githooks/commit-msg` hook so that
the definition of "live" cannot drift between them.
"""
from __future__ import annotations

import os
import subprocess
from typing import Optional

import frontmatter


def _content_is_live(content: str) -> bool:
    """Return True iff the raw markdown `content` parses to frontmatter
    with `live: true`. Any parse failure is treated as not-live."""
    try:
        post = frontmatter.loads(content)
    except Exception:
        return False
    return bool(post.metadata.get("live", False))


def is_live(path: str) -> bool:
    """Return True iff the file on disk at `path` has `live: true` in
    its YAML frontmatter. Missing file is not-live."""
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        return _content_is_live(f.read())


def head_is_live(path: str, repo_root: Optional[str] = None) -> bool:
    """Return True iff the version of `path` at `git HEAD` has
    `live: true`. If `path` did not exist in HEAD (new file, brand-new
    repo, detached HEAD without a HEAD ref), returns False.

    `path` is interpreted as relative to `repo_root`. If `repo_root` is
    None, the current working directory is used."""
    if repo_root is None:
        repo_root = os.getcwd()
    rel = path
    if os.path.isabs(rel):
        rel = os.path.relpath(rel, repo_root)
    # Git uses forward slashes regardless of platform.
    rel = rel.replace(os.sep, "/")
    result = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    return _content_is_live(result.stdout)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_live.py -v`

Expected: all 9 tests pass.

- [ ] **Step 5: Commit**

```bash
git add canvas_sync/live.py tests/test_live.py
git commit -m "feat(live): add is_live and head_is_live helpers"
```

---

## Task 4: Add `--override-live` flag to `push` CLI

**Files:**
- Modify: `canvas_sync/__main__.py:39-43` (argparse `push` subcommand)
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cli.py`:

```python
def test_push_override_live_default_false():
    parser = build_parser()
    args = parser.parse_args(["push", "--week", "1"])
    assert args.override_live is False


def test_push_override_live_true():
    parser = build_parser()
    args = parser.parse_args(["push", "--week", "1", "--override-live"])
    assert args.override_live is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::test_push_override_live_default_false tests/test_cli.py::test_push_override_live_true -v`

Expected: FAIL with `AttributeError: 'Namespace' object has no attribute 'override_live'`.

- [ ] **Step 3: Add the flag in `build_parser`**

In `canvas_sync/__main__.py`, inside `build_parser`, locate the `push_p` block (around line 39). Add an `--override-live` flag immediately after the existing `--force` line:

```python
    push_p = sub.add_parser("push", help="Push week content to Canvas")
    push_group = push_p.add_mutually_exclusive_group(required=True)
    push_group.add_argument("--all", action="store_true", help="Push all weeks")
    push_group.add_argument("--week", type=int, help="Push a specific week number")
    push_p.add_argument("--force", action="store_true", help="Skip confirmation prompts")
    push_p.add_argument(
        "--override-live",
        action="store_true",
        help="Push even if a week is marked live in its frontmatter",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add canvas_sync/__main__.py tests/test_cli.py
git commit -m "feat(cli): add --override-live flag to push"
```

---

## Task 5: Wire `_filter_live_weeks` into `cmd_push`

**Files:**
- Modify: `canvas_sync/__main__.py:237-250` (`cmd_push`)
- Modify: `canvas_sync/__main__.py:357-371` (`main`)
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cli.py`:

```python
from canvas_sync.__main__ import _filter_live_weeks
from canvas_sync.models import Week


def _wk(num, live=False):
    return Week(
        week=num,
        title=f"W{num}",
        starts="2026-05-11",
        body_markdown="",
        workshop=None,
        assignments=[],
        discussion=None,
        live=live,
    )


def test_filter_live_weeks_no_live_pass_through():
    weeks = [_wk(1, live=False), _wk(2, live=False)]
    kept, skipped = _filter_live_weeks(weeks, override_live=False)
    assert [w.week for w in kept] == [1, 2]
    assert skipped == []


def test_filter_live_weeks_skips_when_not_overridden():
    weeks = [_wk(1, live=True), _wk(2, live=False), _wk(3, live=True)]
    kept, skipped = _filter_live_weeks(weeks, override_live=False)
    assert [w.week for w in kept] == [2]
    assert [w.week for w in skipped] == [1, 3]


def test_filter_live_weeks_override_keeps_all():
    weeks = [_wk(1, live=True), _wk(2, live=False)]
    kept, skipped = _filter_live_weeks(weeks, override_live=True)
    assert [w.week for w in kept] == [1, 2]
    assert skipped == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::test_filter_live_weeks_no_live_pass_through tests/test_cli.py::test_filter_live_weeks_skips_when_not_overridden tests/test_cli.py::test_filter_live_weeks_override_keeps_all -v`

Expected: FAIL with `ImportError: cannot import name '_filter_live_weeks'`.

- [ ] **Step 3: Implement `_filter_live_weeks` and use it in `cmd_push`**

In `canvas_sync/__main__.py`, add `_filter_live_weeks` immediately above `cmd_push` (around line 237):

```python
def _filter_live_weeks(weeks, override_live: bool):
    """Split weeks into (kept, skipped). If override_live is False,
    weeks with `live: true` go to skipped; otherwise everything is kept."""
    if override_live:
        return list(weeks), []
    kept = [w for w in weeks if not w.live]
    skipped = [w for w in weeks if w.live]
    return kept, skipped
```

Update `cmd_push` to use it and to exit non-zero if any week was skipped:

```python
def cmd_push(config, weeks_dir, state: SyncState, week_num=None, all_weeks=False, force=False, override_live=False):
    cs = CanvasSync(config)
    if all_weeks:
        weeks = load_all_weeks(weeks_dir, course_start=config.course_start)
    else:
        path = os.path.join(weeks_dir, f"week-{week_num:02d}.md")
        if not os.path.exists(path):
            console.print(f"[red]File not found: {path}[/red]")
            sys.exit(1)
        weeks = [parse_week_file(path, course_start=config.course_start)]

    kept, skipped = _filter_live_weeks(weeks, override_live)
    for w in skipped:
        console.print(
            f"[yellow]Skipping {w.module_name}: marked live. "
            f"Pass --override-live to push anyway.[/yellow]"
        )

    for week in kept:
        _push_week(cs, week, state, force)

    if kept:
        console.print("\n[bold green]Push complete.[/bold green]")
    if skipped:
        sys.exit(2)
```

Update the dispatch in `main()` (around line 367) to pass the new flag:

```python
    elif args.command == "push":
        cmd_push(
            config,
            args.weeks_dir,
            state,
            week_num=args.week,
            all_weeks=args.all,
            force=args.force,
            override_live=args.override_live,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add canvas_sync/__main__.py tests/test_cli.py
git commit -m "feat(push): refuse live weeks unless --override-live is passed"
```

---

## Task 6: Add "Live" column to `cmd_status`

**Files:**
- Modify: `canvas_sync/__main__.py:253-275` (`cmd_status`)

- [ ] **Step 1: Update `cmd_status`**

In `canvas_sync/__main__.py`, modify the `cmd_status` function. After `table.add_column("Last Synced")`, insert a Live column. Easiest: insert it right after the Week column.

Replace the function body with:

```python
def cmd_status(config, weeks_dir, state: SyncState):
    weeks = load_all_weeks(weeks_dir, course_start=config.course_start)
    table = Table(title="Canvas Sync Status")
    table.add_column("Week", style="bold")
    table.add_column("Live")
    table.add_column("Module")
    table.add_column("Page")
    table.add_column("Assignments")
    table.add_column("Discussion")
    table.add_column("Last Synced")

    for week in weeks:
        live = "[green]✓[/green]" if week.live else ""
        ws = state.get_week(week.file_key)
        if ws is None:
            table.add_row(week.module_name, live, "—", "—", "—", "—", "never")
        else:
            module = f"[green]✓[/green] {ws.get('module_id', '—')}" if "module_id" in ws else "—"
            page = f"[green]✓[/green]" if "page_url" in ws else "—"
            assigns = str(len(ws.get("assignments", []))) if ws.get("assignments") else "—"
            disc = f"[green]✓[/green]" if "discussion_id" in ws else "—"
            synced = ws.get("last_synced", "never")
            table.add_row(week.module_name, live, module, page, assigns, disc, synced)

    console.print(table)
```

- [ ] **Step 2: Run all tests to confirm nothing regressed**

Run: `pytest tests -v`

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add canvas_sync/__main__.py
git commit -m "feat(status): show Live column in status table"
```

---

## Task 7: Create the `commit-msg` git hook

**Files:**
- Create: `.githooks/commit-msg`

- [ ] **Step 1: Create the hook script**

Create `.githooks/commit-msg`:

```python
#!/usr/bin/env python3
"""commit-msg hook: refuse commits that touch a week which was already
live in HEAD, unless the commit message contains the literal token
`[live-edit]`.

Installation (one-time, per clone):
    git config core.hooksPath .githooks

Bypass for one commit:
    Include `[live-edit]` anywhere in the commit message, OR run
    `git commit --no-verify` (universal escape hatch — skips all hooks).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Make canvas_sync importable when the hook runs from the repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from canvas_sync.live import head_is_live  # noqa: E402


OVERRIDE_TOKEN = "[live-edit]"


def main(argv):
    if len(argv) < 2:
        print("commit-msg hook invoked without a message path; skipping.", file=sys.stderr)
        return 0
    msg_path = argv[1]
    try:
        message = Path(msg_path).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"commit-msg hook: could not read message file ({exc}); skipping.", file=sys.stderr)
        return 0

    if OVERRIDE_TOKEN in message:
        return 0

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # If git itself fails here, fall through rather than block.
        return 0

    staged = [line for line in result.stdout.splitlines() if line.strip()]
    blocked = []
    for path in staged:
        if not path.startswith("weeks/") or not path.endswith(".md"):
            continue
        if head_is_live(path, repo_root=str(REPO_ROOT)):
            blocked.append(path)

    if not blocked:
        return 0

    sys.stderr.write(
        "\nThis commit edits week(s) that are already live in HEAD:\n"
    )
    for p in blocked:
        sys.stderr.write(f"  - {p}\n")
    sys.stderr.write(
        "\nLive weeks should not be edited without intent. To proceed,\n"
        f"include the token {OVERRIDE_TOKEN} anywhere in your commit message,\n"
        "or use `git commit --no-verify` (skips all hooks).\n\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 2: Mark the hook executable**

Run:

```bash
git update-index --chmod=+x .githooks/commit-msg
chmod +x .githooks/commit-msg 2>/dev/null || true
```

(The `git update-index` line records the executable bit in git's index even on filesystems that don't carry it natively; the second line is a no-op on Windows but harmless.)

- [ ] **Step 3: Verify the hook script syntax**

Run: `python -c "import py_compile; py_compile.compile('.githooks/commit-msg', doraise=True)"`

Expected: no output (success). If you get a syntax error, fix it before continuing.

- [ ] **Step 4: Smoke-test the hook by hand from the repo root**

Set up the hooks path (one-time on your machine; it's not committed to the repo, it's a local git config):

```bash
git config core.hooksPath .githooks
```

Create a throwaway test by editing a not-yet-live week (e.g. `weeks/week-02.md` — add a trailing newline) and stage it:

```bash
echo "" >> weeks/week-02.md
git add weeks/week-02.md
```

Then attempt a commit with a normal message:

```bash
git commit -m "test: hook should allow this"
```

Expected: the commit succeeds (week-02.md is not live in HEAD).

Reset the test edit:

```bash
git reset --soft HEAD~1
git restore --staged weeks/week-02.md
git checkout -- weeks/week-02.md
```

- [ ] **Step 5: Commit the hook**

```bash
git add .githooks/commit-msg
git commit -m "feat(hooks): commit-msg hook blocks edits to live weeks"
```

---

## Task 8: Document Live Weeks in the README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add the "Live weeks" section**

Open `README.md` and insert a new section immediately before the `## Development` section near the bottom of the file. Use this exact content:

```markdown
## Live Weeks

Once a week is published to students it is *live*: the rendered GitHub Pages page and the Webcourses module may have been edited directly, and unconsidered changes here can overwrite them silently. Mark a week as live by adding `live: true` to its YAML frontmatter:

```yaml
---
week: 1
title: "Welcome and Interdisciplinary Teaching"
starts: 2026-05-11
live: true
...
---
```

Two guardrails kick in once that flag is set:

1. **`canvas_sync push` refuses to touch live weeks.** Run with `--override-live` to bypass:

   ```bash
   python -m canvas_sync push --week 1 --override-live
   ```

   `status` and `diff` are read-only and remain available. `status` shows a Live column so you can see at a glance which weeks are locked.

2. **A `commit-msg` git hook blocks edits to weeks that were live in `HEAD`.** Bypass for a single commit by including the token `[live-edit]` anywhere in your commit message:

   ```bash
   git commit -m "fix: typo in week 1 reading list [live-edit]"
   ```

   `git commit --no-verify` is the universal escape hatch but also skips all other hooks.

   The hook is checked into the repo at `.githooks/commit-msg`. Activate it once per clone with:

   ```bash
   git config core.hooksPath .githooks
   ```

The hook reads `HEAD`'s frontmatter (not the staged version), so the commit that promotes a week to live is allowed cleanly without `[live-edit]`. Subsequent edits — and demotions back to draft — do require the token.
```

- [ ] **Step 2: Sanity-check rendering**

Open `README.md` in a Markdown previewer (or just read it through). Confirm the code fences nest correctly and the section reads cleanly.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document live-week guardrail and hook setup"
```

---

## Task 9: Mark Week 1 as live (separate commit)

**Files:**
- Modify: `weeks/week-01.md`

This commit must come *after* the hook landed in Task 7. It will be the first real exercise of the "promotion commit is allowed" path.

- [ ] **Step 1: Confirm `weeks/week-01.md` is not currently live**

Run: `git show HEAD:weeks/week-01.md | head -20`

Expected: frontmatter shows no `live:` field. (If it shows `live: true`, stop and investigate — the promotion has already happened.)

- [ ] **Step 2: Add `live: true` to the frontmatter**

Edit `weeks/week-01.md`. The current frontmatter:

```yaml
---
week: 1
title: "Welcome and Interdisciplinary Teaching"
starts: 2026-05-11
slides: week-01
workshop:
  ...
```

Insert `live: true` on a new line directly after the `starts:` line:

```yaml
---
week: 1
title: "Welcome and Interdisciplinary Teaching"
starts: 2026-05-11
live: true
slides: week-01
workshop:
  ...
```

Do not touch any body content. This is a frontmatter-only edit.

- [ ] **Step 3: Verify the hook allows the promotion commit**

```bash
git add weeks/week-01.md
git commit -m "feat: mark week 1 live"
```

Expected: commit succeeds. The hook reads HEAD's frontmatter (which has no `live: true`), so it does not block. No `[live-edit]` token needed.

If the hook blocks here, something is wrong — the spec's HEAD-based semantics are exactly to allow this case. Re-read the hook source and the `head_is_live` implementation before bypassing.

- [ ] **Step 4: Verify the guardrail is now active**

Run: `python -m canvas_sync status` and confirm Week 1's Live column shows `✓`.

Then run: `python -m canvas_sync push --week 1` (the `--week 1` form; do **not** add `--override-live`).

Expected: the tool prints `Skipping Week 1: ... Pass --override-live to push anyway.` and exits non-zero. Do **not** actually push under any circumstance during this verification — we explicitly committed to not running `canvas_sync push` during this work.

If you want to verify the override path without actually pushing, you can stop here — the unit tests in Task 5 already cover that branch.

---

## Verification Checklist

Run after all tasks are complete:

- [ ] `pytest tests -v` — all tests pass.
- [ ] `python -m canvas_sync status` — Week 1 row shows Live ✓.
- [ ] `python -m canvas_sync push --week 1` — refuses with the live message, exits non-zero.
- [ ] Trivial edit to `weeks/week-01.md` (e.g. trailing whitespace), `git commit -m "test"` — hook blocks.
- [ ] Same edit, `git commit -m "test [live-edit]"` — hook allows. Then reset that test commit before continuing.
- [ ] `git log --oneline -10` — commits are in the order specified (guardrail first, week-1 promotion last).
- [ ] No `canvas_sync push` was invoked at any point that actually contacted Canvas.
