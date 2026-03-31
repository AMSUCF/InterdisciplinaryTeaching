# Canvas Sync Utility — Design Spec

**Date:** 2026-03-31
**Project:** InterdisciplinaryTeaching (ENG 6813, Summer C 2026)
**Purpose:** Python CLI utility that syncs course content from per-week markdown files to UCF's Canvas LMS (Webcourses), supporting initial scaffolding and incremental updates with diff-based confirmation.

## Content Organization

The current single `index.md` is split into per-week markdown files under `weeks/`. Each file uses frontmatter for structured metadata and a markdown body for content.

### Directory Structure

```
InterdisciplinaryTeaching/
├── index.md                    # Jekyll site (kept as-is for GitHub Pages)
├── weeks/
│   ├── week-01.md
│   ├── week-02.md
│   └── ...week-12.md
├── canvas_sync/
│   ├── __main__.py             # CLI entry point (python -m canvas_sync ...)
│   ├── config.py               # Load canvas_config.yaml
│   ├── parser.py               # Parse week markdown files
│   ├── canvas_api.py           # Canvas interactions via canvasapi
│   ├── diff.py                 # Compare local vs Canvas state
│   └── models.py               # Internal data models (Week, Reading, Assignment, etc.)
├── canvas_config.yaml          # API key, course ID, base URL (gitignored)
├── .canvas_sync_state.json     # Tracks Canvas IDs for pushed objects (gitignored)
└── requirements.txt            # canvasapi, python-frontmatter, pyyaml, markdown, rich
```

### Week File Format

Each `weeks/week-NN.md` file has this structure:

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

- Locke, Brandon. ["Digital Humanities Pedagogy..."](https://...)
- Croxall, Brian...

## Discussion Prompt

Introduce yourself and describe your teaching experience...

## Workshop Notes

*Optional: NEH Workshop 1 details...*
```

- Frontmatter fields drive creation of Canvas modules, assignments, and discussion topics.
- The markdown body is rendered to HTML and becomes the Canvas page content.
- `workshop` is optional (not all weeks have workshops).
- `discussion` is optional (not all weeks have discussion posts).
- `assignments` is a list (some weeks have assignments, some don't).

## Canvas Object Mapping

Each week file produces these Canvas objects:

| Markdown Source | Canvas Object | Key Fields |
|---|---|---|
| Week frontmatter (`week`, `title`) | Module | Name (e.g., "Week 1: Welcome and Interdisciplinary Teaching"), position |
| Markdown body (rendered to HTML) | Page | Title, body HTML |
| `assignments` list in frontmatter | Assignment(s) | Name, points, due date, submission type |
| `discussion` in frontmatter + `## Discussion Prompt` body section | Discussion Topic | Title, points, due date, message (HTML) |

### Module Item Order

Objects are added to the module as items in this sequence:
1. Content page (readings + workshop info)
2. Assignment(s)
3. Discussion topic

### Defaults

- All objects are created **unpublished** so the instructor can review in Canvas before releasing.
- Assignment submission type defaults to `online_text_entry` (overridable via frontmatter field `submission_type`).
- Due dates are date-only in frontmatter (e.g., `2026-05-15`); the utility appends `T23:59:00` Eastern time and converts to ISO 8601 for Canvas.

## CLI Commands

Invoked as `python -m canvas_sync <command>`.

### `init`

Reads all week files in `weeks/`, creates a Canvas module for each one (empty, ordered by week number), using the title from each file's frontmatter. Establishes the course skeleton before detailed content is ready.

```
python -m canvas_sync init
```

### `push`

Syncs markdown content to Canvas. Creates new objects or updates existing ones.

```
python -m canvas_sync push --all
python -m canvas_sync push --week 3
python -m canvas_sync push --week 3 --force    # skip confirmation
```

For updates to existing objects, shows a diff and asks for confirmation (see Diff & Confirmation Workflow below).

### `status`

Shows sync state for all weeks as a table: whether each week exists in Canvas, whether local content differs, and last sync time.

```
python -m canvas_sync status
```

### `diff`

Preview changes without pushing.

```
python -m canvas_sync diff --all
python -m canvas_sync diff --week 3
```

## Diff & Confirmation Workflow

### State Tracking

A local `.canvas_sync_state.json` file (gitignored) maps each week's objects to their Canvas IDs:

```json
{
  "week-01": {
    "module_id": 12345,
    "page_id": 67890,
    "assignments": [{"title": "Activity Verification", "canvas_id": 11111}],
    "discussion_id": 22222,
    "last_synced": "2026-04-01T14:30:00"
  }
}
```

### Diff Process

When pushing a week that already has Canvas IDs in the state file:

1. Fetch the current Canvas object using the stored ID.
2. Compare relevant fields (title, body HTML, points, due dates) against what the markdown would produce.
3. Display a readable diff with colored output (via `rich`): field name, current Canvas value, new local value.

### Confirmation Prompt

For each object with changes:

```
Week 1 - Assignment "Activity Verification":
  points: 50 -> 75
  due: 2026-05-15 -> 2026-05-16
Apply this update? [y/n/a(ll)/q(uit)]
```

- **y** — apply this update
- **n** — skip this update
- **a** — apply all remaining updates without further prompts
- **q** — abort, apply nothing further

### Edge Cases

- If a Canvas ID in the state file no longer exists (manually deleted in Canvas), treat it as a new object and offer to recreate it.
- To reset sync state, delete `.canvas_sync_state.json` and run `init` again.

## Configuration

`canvas_config.yaml` (gitignored):

```yaml
api_url: https://webcourses.ucf.edu
api_key: YOUR_API_KEY_HERE
course_id: 123456
```

## Technical Details

### Dependencies

- `canvasapi` — Canvas LMS API wrapper (built by UCF)
- `python-frontmatter` — Parse YAML frontmatter from markdown files
- `pyyaml` — YAML config file parsing
- `markdown` — Convert markdown body to HTML (with `tables` and `fenced_code` extensions)
- `rich` — Colored terminal output for tables, diffs, and progress

### Markdown to HTML

The markdown body of each week file is rendered to HTML using Python's `markdown` library before uploading to Canvas pages and discussion messages.

### Timezone Handling

Due dates in frontmatter are date-only. The utility appends `T23:59:00` in US/Eastern and converts to ISO 8601 format for the Canvas API.

### Rate Limiting

The `canvasapi` library handles Canvas API rate limiting automatically. For bulk operations (`push --all`), the utility logs progress per-week.

## Out of Scope

These remain manual tasks:
- PDF file uploads to Canvas
- Canvas course settings (grading scheme, navigation, etc.)
- Publishing objects (done in Canvas after review)
- Non-open-access readings — only linked/open-access readings are included in page content
