from __future__ import annotations

import glob
import os
import re
from typing import Optional

import frontmatter

from canvas_sync.models import Assignment, Discussion, Week, Workshop


def _extract_assignment_descriptions(body: str) -> dict[str, str]:
    """Extract assignment descriptions from the ## Assignments section of the markdown body."""
    match = re.split(r"^## Assignments\s*$", body, flags=re.MULTILINE)
    if len(match) < 2:
        return {}
    section = match[1]
    # Stop at next ## heading
    next_heading = re.split(r"^## ", section, flags=re.MULTILINE)
    section = next_heading[0].strip()

    descriptions = {}
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("- **"):
            continue
        # Parse: - **Title** (points) — Description text
        m = re.match(r"^- \*\*(.+?)\*\*.*?[—–-]\s*(.+)$", line)
        if m:
            title = m.group(1).strip()
            desc = m.group(2).strip()
            descriptions[title] = desc
    return descriptions


def parse_week_file(path: str, course_start: str = "") -> Week:
    post = frontmatter.load(path)
    meta = post.metadata

    workshop: Optional[Workshop] = None
    if "workshop" in meta:
        workshop = Workshop.from_dict(meta["workshop"])

    # Extract descriptions from body before creating Assignment objects
    body_descriptions = _extract_assignment_descriptions(post.content)

    assignments: list[Assignment] = []
    if "assignments" in meta:
        for a in meta["assignments"]:
            if "description" not in a and a["title"] in body_descriptions:
                a["description"] = body_descriptions[a["title"]]
            assignments.append(Assignment.from_dict(a, course_start=course_start))

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


def load_all_weeks(weeks_dir: str, course_start: str = "") -> list[Week]:
    pattern = os.path.join(weeks_dir, "week-*.md")
    files = sorted(glob.glob(pattern))
    return sorted(
        [parse_week_file(f, course_start=course_start) for f in files],
        key=lambda w: w.week,
    )
