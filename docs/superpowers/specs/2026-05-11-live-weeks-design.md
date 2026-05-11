# Tracking live weeks — design

**Date:** 2026-05-11
**Course:** ENG 6813 (Interdisciplinary Teaching), Summer C 2026
**Scope:** Add a guardrail mechanism so that weeks marked "live" cannot have their content pushed to Canvas or committed to git without an explicit, intentional override. Mark Week 1 as live as part of this change. Do not invoke `canvas_sync push` at any point during implementation.

## Motivation

Once a week's module is published to students — visible on the GitHub Pages site and in Webcourses — the local `weeks/week-XX.md` is no longer the unilateral source of truth. Direct edits may have been made in Canvas, and unconsidered changes to the markdown can either silently change what students see on GitHub Pages or be pushed over Canvas edits via `canvas_sync push`. Week 1 is already in this state.

We need a small, explicit guardrail: a per-week boolean flag and two enforcement points (the Canvas push pipeline and the git commit boundary), each with a clear, durable override mechanism.

## Goals

- A single, frontmatter-stored `live: true` flag per week.
- `canvas_sync push` refuses to touch a live week unless `--override-live` is passed.
- A git pre-commit hook blocks commits that modify the body of a week that was *already* live in `HEAD`, unless the commit message contains the literal token `[live-edit]`.
- The hook checks `HEAD`'s frontmatter, not the staged file's, so promoting a week to live ("flipping the flag") is not itself blocked.
- `canvas_sync status` surfaces the live flag for each week.
- Week 1 is marked live as part of this change.

## Non-goals

- No Jekyll-side rendering of the live state (no badge, no template change). The flag is metadata for tooling only.
- No date-based or automatic promotion to live. Promotion is always an explicit edit to the `live:` field.
- No "pull back from Canvas" capability. If Canvas content has drifted from the markdown for a live week, that drift remains; we just stop overwriting it. A future feature could add a pull, but it is out of scope here.
- No CI enforcement beyond the local git hook. The hook covers the realistic threat (accidental local edits); GitHub web-UI edits are rare for this repo and a CI check is over-engineering for the scale.
- No retroactive blocking of past commits that touched week-01.md before this change landed.

## Architecture

### Frontmatter field

```yaml
---
week: 1
title: "Welcome and Interdisciplinary Teaching"
starts: 2026-05-11
live: true        # new — absent or false means draft
slides: week-01
...
---
```

- Type: boolean. Default when absent: `false`.
- Only set on weeks that have been published to students. For this change, only Week 1.

### File layout

**New files:**
- `.githooks/pre-commit` — short Python script (shebang `#!/usr/bin/env python3`) that reads staged `weeks/week-*.md` paths from `git diff --cached --name-only --diff-filter=ACMR`, compares each against its `HEAD` version's frontmatter, and blocks the commit if any was live in `HEAD` and the commit message does not contain `[live-edit]`.
- `canvas_sync/live.py` — tiny module exposing `is_live(week_md_path) -> bool` and `head_is_live(week_md_path) -> bool`. Used by both the canvas_sync push path and the git hook. Reads YAML frontmatter with the same lightweight approach already used in `canvas_sync/parser.py` (no new dependency).
- `docs/superpowers/specs/2026-05-11-live-weeks-design.md` — this document.

**Modified files:**
- `weeks/week-01.md` — gains `live: true` in frontmatter. Body content unchanged. (Landed in a separate, second commit; see Implementation Order.)
- `canvas_sync/models.py` — `Week` gains an optional `live: bool = False` field.
- `canvas_sync/parser.py` — reads `live` from frontmatter into the `Week` model.
- `canvas_sync/__main__.py` — the `push` command accepts a new `--override-live` flag. Before pushing each week, it checks `week.live`; if true and `--override-live` was not passed, the week is skipped with an explanatory error and the overall exit code is non-zero if at least one week was blocked. The `status` command gains a "Live" column. `diff` is read-only and unchanged.
- `README.md` — a new "Live weeks" section explains the flag, the `--override-live` flag, the `[live-edit]` commit message token, and the one-time `git config core.hooksPath .githooks` setup step.
- `tests/` — unit tests for: (a) parser reads `live:` correctly, (b) push command refuses live weeks without override and proceeds with override, (c) `canvas_sync/live.py` reports correct booleans for various fixture files.

### Override mechanisms

| Surface | Override | Why this form |
|---|---|---|
| `canvas_sync push` | `--override-live` flag | Discoverable in `--help`; explicit; cannot be set in config (intentional friction). |
| Git pre-commit hook | `[live-edit]` token in commit message | Durable: visible in `git log` forever, unlike `--no-verify` which leaves no trace. Doesn't bypass other hooks. `--no-verify` still works as the universal escape hatch but is not the documented path. |

### Hook semantics: HEAD-based check

The hook decides "was this file live *before* this commit?" by reading `git show HEAD:<path>` and parsing its frontmatter. Consequences:

- **Promotion commit (draft → live):** HEAD has no `live: true` → hook passes silently. The commit that flips the flag does not need `[live-edit]`.
- **Edit to a live week:** HEAD has `live: true` → blocked unless `[live-edit]` is in the message.
- **Edit to a draft week:** HEAD has no `live: true` → passes silently.
- **Brand-new week file (no HEAD version):** treated as not-live → passes silently.
- **Demotion commit (live → draft):** HEAD has `live: true` → blocked, since this is itself an edit to a live file. The user must include `[live-edit]` to demote. This is the right behavior: demoting a live week is a significant decision and should be marked.
- **Initial commit / empty repo / detached HEAD:** if `git show HEAD:<path>` fails, treat as not-live and pass.

### canvas_sync push semantics

When `push` is invoked (either `--week N` or `--all`), the tool iterates weeks and, for each one whose `live` is true:

- If `--override-live` was passed: proceed with the normal diff/confirmation flow.
- Otherwise: print `Skipping week N: marked live. Pass --override-live to push anyway.` and continue to the next week. Track that at least one was skipped, and exit non-zero at the end so scripts and CI cannot silently miss the skip.

`status` and `diff` are read-only and behave as before, except `status` adds a "Live" column displaying ✓ or blank.

## Data flow

```
weeks/week-XX.md frontmatter
        │
        ├──► canvas_sync/parser.py ──► Week.live ──► push() guard ──► Canvas API
        │
        └──► .githooks/pre-commit (via canvas_sync/live.py) ──► block/allow commit
```

Both enforcement points read from the same source (`canvas_sync/live.py`), so the definition of "live" cannot drift between them.

## Implementation order

Two commits, in this order:

1. **Guardrail commit** — adds `canvas_sync/live.py`, `Week.live`, parser change, `--override-live` flag, status column, `.githooks/pre-commit`, tests, README section. Touches no `weeks/*.md` files, so the hook (even self-installed) has nothing to block.
2. **Promote Week 1 commit** — single change: add `live: true` to `weeks/week-01.md`. The hook sees HEAD's week-01.md still has no `live: true`, so it allows the commit cleanly without `[live-edit]`.

The user runs `git config core.hooksPath .githooks` once, manually, after pulling the first commit. (The README will say so.) We do not auto-install the hook from any tool, since hook installation is a security-sensitive operation that should be explicit.

`canvas_sync push` is never invoked during implementation.

## Testing

Unit tests (pytest, alongside existing `tests/`):

- `test_live.py`: `is_live()` and `head_is_live()` return correct booleans for fixture files with `live: true`, `live: false`, and missing `live:`.
- `test_parser.py` (extend): asserts `Week.live` is `False` by default and `True` when the frontmatter says so.
- `test_push.py` (extend or new): with a fixture week marked live, `push` without `--override-live` skips the week, returns non-zero, and does not call the Canvas API mock; with `--override-live`, push proceeds normally.

Manual verification (instructor, after merge):

- Run `python -m canvas_sync status` and confirm Week 1 shows as Live.
- Run `python -m canvas_sync push --week 1` and confirm it refuses with the expected message.
- Run `python -m canvas_sync push --week 1 --override-live` and confirm the normal diff/confirmation flow appears (then abort at the confirmation; do not actually push).
- Make a trivial edit to `weeks/week-01.md`, attempt `git commit -m "test"`, confirm the hook blocks.
- Repeat with `git commit -m "test [live-edit]"`, confirm the hook allows.

## Risks and mitigations

- **Risk:** Instructor forgets to run `git config core.hooksPath .githooks` and assumes they are protected. **Mitigation:** README's "Live weeks" section is explicit about the one-time setup; the canvas_sync side of the guardrail still works independently.
- **Risk:** Someone uses the GitHub web UI to edit a live week, bypassing the local hook. **Mitigation:** Documented but accepted; a CI check is out of scope for this iteration.
- **Risk:** `[live-edit]` token in a commit message that wasn't really intended to edit a live week (e.g. typo in unrelated commit). **Mitigation:** Low impact — at worst it permits an edit that the author was about to make anyway. The token is a forcing function for awareness, not a cryptographic gate.
