# Interdisciplinary Teaching (ENG 6813)

Course materials for **ENG 6813: Interdisciplinary Teaching**, Summer C 2026 at UCF. This repository serves as both a GitHub Pages course site and the source of truth for Canvas LMS content, synced via the included `canvas_sync` tool.

**Instructors:** Dr. Anastasia Salter and Dr. Mel Stanfill

**Course site:** [https://anastasiasalter.net/InterdisciplinaryTeaching/](https://anastasiasalter.net/InterdisciplinaryTeaching/)

## Repository Structure

```
weeks/              # Weekly module content (Markdown with YAML frontmatter)
  week-00.md        # Course overview / "Start Here" page
  week-01.md        # Week 1: Welcome and Interdisciplinary Teaching
  ...
  week-12.md        # Week 12: Final Portfolio
canvas_sync/        # Python tool for syncing content to Canvas LMS
canvas_config.yaml  # Canvas API configuration (not committed — see setup)
index.md            # Course syllabus (GitHub Pages home page)
_config.yml         # Jekyll configuration for GitHub Pages
```

## Canvas Sync Tool

`canvas_sync` is a CLI tool that pushes the weekly Markdown files in `weeks/` to Canvas LMS as modules, pages, assignments, and discussion topics. It uses the Canvas REST API via the `canvasapi` library, tracks sync state locally, and shows diffs before applying changes.

### Prerequisites

- Python 3.10+
- A Canvas API access token ([how to generate one](https://community.canvaslms.com/t5/Admin-Guide/How-do-I-manage-API-access-tokens-as-an-admin/ta-p/89))

### Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create your configuration file by copying the example:

   ```bash
   cp canvas_config.example.yaml canvas_config.yaml
   ```

3. Edit `canvas_config.yaml` with your Canvas instance details:

   ```yaml
   api_url: https://webcourses.ucf.edu
   api_key: YOUR_API_KEY_HERE
   course_id: 123456
   course_start: 2026-05-11      # optional, used for assignment unlock dates
   ```

   **Do not commit `canvas_config.yaml`** — it contains your API key.

### Commands

All commands are run with `python -m canvas_sync`.

#### `init` — Create empty modules

```bash
python -m canvas_sync init
```

Creates a Canvas module for each week file. Run this once when setting up a new course shell.

#### `push` — Push content to Canvas

```bash
# Push a single week
python -m canvas_sync push --week 1

# Push all weeks
python -m canvas_sync push --all

# Push without confirmation prompts
python -m canvas_sync push --all --force
```

For each week, this creates or updates:
- A **page** with the week's Markdown content rendered as HTML
- **Assignments** defined in the frontmatter (with points, due dates, and descriptions)
- A **discussion topic** if defined in the frontmatter (with the prompt extracted from the `## Discussion Prompt` section)

When updating existing content, the tool shows a diff of local vs. Canvas state and asks for confirmation before applying changes. You can approve individually, choose "apply all," or quit.

#### `status` — Check sync state

```bash
python -m canvas_sync status
```

Displays a table showing which weeks have been synced, what Canvas objects exist (module, page, assignments, discussion), and when each was last synced.

#### `diff` — Preview changes

```bash
# Diff a single week
python -m canvas_sync diff --week 3

# Diff all weeks
python -m canvas_sync diff --all
```

Compares local Markdown content against the current Canvas state and shows what would change on the next push, without modifying anything.

### Week File Format

Each file in `weeks/` uses YAML frontmatter to define metadata and Markdown for the page body:

```yaml
---
week: 1
title: "Welcome and Interdisciplinary Teaching"
starts: 2026-05-11
workshop:                              # optional
  title: "Workshop 1: Introducing AI"
  date: 2026-05-13
  time: "10 AM - noon"
  location: CHDR
assignments:                           # optional, list
  - title: "Activity Verification"
    points: 50
    due: 2026-05-15
discussion:                            # optional
  title: "Introduce yourself"
  points: 30
  due: 2026-05-17
---

Week body content in Markdown...

## Discussion Prompt

The text under this heading is used as the discussion topic body in Canvas.
```

### Options

| Flag | Description |
|------|-------------|
| `--config PATH` | Path to config YAML (default: `canvas_config.yaml`) |
| `--weeks-dir PATH` | Path to weeks directory (default: `weeks`) |
| `--state-file PATH` | Path to state JSON (default: `.canvas_sync_state.json`) |

### State File

The tool stores sync state in `.canvas_sync_state.json`, which maps week keys to Canvas object IDs (module, page URL, assignment IDs, discussion ID). This file is how the tool knows what already exists in Canvas. Do not edit it manually.

## Development

Run the test suite:

```bash
pytest
```

## License

Course materials are for educational use at UCF.
