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
