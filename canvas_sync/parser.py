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
