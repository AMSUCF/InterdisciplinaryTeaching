# canvas_sync/__main__.py
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from typing import Optional

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
    push_p.add_argument(
        "--override-live",
        action="store_true",
        help="Push even if a week is marked live in its frontmatter",
    )

    status_p = sub.add_parser("status", help="Show sync status for all weeks")  # noqa: F841

    diff_p = sub.add_parser("diff", help="Preview changes without pushing")
    diff_group = diff_p.add_mutually_exclusive_group(required=True)
    diff_group.add_argument("--all", action="store_true", help="Diff all weeks")
    diff_group.add_argument("--week", type=int, help="Diff a specific week number")

    return parser


def cmd_init(config, weeks_dir, state: SyncState):
    cs = CanvasSync(config)
    weeks = load_all_weeks(weeks_dir, course_start=config.course_start)
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


def _splice_slides(body_html: str, slides_html: Optional[str]) -> str:
    """Insert the slides iframe block into a rendered page body.

    Strategy: place the slides block immediately before the first `<h2>`
    heading. If no `<h2>` is present, append to the end. If `slides_html`
    is empty or None, return the body unchanged.
    """
    if not slides_html:
        return body_html
    idx = body_html.find("<h2")
    if idx == -1:
        return body_html.rstrip() + "\n" + slides_html
    return body_html[:idx] + slides_html + body_html[idx:]


def _render_page_body(cs: CanvasSync, week) -> str:
    """Render the Canvas page body for a week, splicing in the slide deck if configured."""
    slides_html = week.slides_section_html(cs.config.slides_base_url)
    return _splice_slides(week.body_html, slides_html)


def _push_week(cs: CanvasSync, week, state: SyncState, force: bool):
    week_key = week.file_key
    week_state = state.get_week(week_key) or {}
    apply_all_ref = [force]

    console.print(f"\n[bold]Pushing {week.module_name}...[/bold]")

    # Module
    if "module_id" not in week_state:
        module_id = cs.create_module(week)
        week_state["module_id"] = module_id
        console.print(f"  [green]Created module[/green] (id={module_id})")

    module_id = week_state["module_id"]

    # Page
    if "page_url" not in week_state:
        body_with_slides = _render_page_body(cs, week)
        page_url = cs.create_page(week, body_html=body_with_slides)
        week_state["page_url"] = page_url
        cs.add_module_item(module_id, "Page", page_url, week.module_name)
        console.print(f"  [green]Created page[/green] (url={page_url})")
    else:
        try:
            page = cs.get_page(week_state["page_url"])
        except Exception:
            console.print(f"  [yellow]Page no longer exists in Canvas, recreating...[/yellow]")
            body_with_slides = _render_page_body(cs, week)
            page_url = cs.create_page(week, body_html=body_with_slides)
            week_state["page_url"] = page_url
            cs.add_module_item(module_id, "Page", page_url, week.module_name)
            console.print(f"  [green]Recreated page[/green] (url={page_url})")
            page = None
        if page is not None:
            body_with_slides = _render_page_body(cs, week)
            local_fields = {"title": week.module_name, "body": body_with_slides}
            remote_fields = {"title": page.title, "body": page.body or ""}
            diffs = compute_diff(local_fields, remote_fields)
            if diffs:
                display_diff(f"Page \"{week.module_name}\"", diffs, console)
                if _confirm(f"Page \"{week.module_name}\"", apply_all_ref):
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
            try:
                canvas_a = cs.get_assignment(entry["canvas_id"])
            except Exception:
                console.print(f"  [yellow]Assignment \"{assignment.title}\" no longer exists, recreating...[/yellow]")
                aid = cs.create_assignment(assignment)
                entry = {"title": assignment.title, "canvas_id": aid}
                cs.add_module_item(module_id, "Assignment", aid, assignment.title)
                console.print(f"  [green]Recreated assignment[/green] \"{assignment.title}\" (id={aid})")
                canvas_a = None
            if canvas_a is not None:
                local_fields = {
                    "name": assignment.title,
                    "description": assignment.description,
                    "points_possible": assignment.points,
                    "due_at": assignment.due_datetime.isoformat(),
                    "unlock_at": assignment.unlock_datetime.isoformat(),
                    "lock_at": assignment.lock_datetime.isoformat(),
                    "submission_types": [assignment.submission_type],
                }
                remote_fields = {
                    "name": getattr(canvas_a, "name", ""),
                    "description": getattr(canvas_a, "description", "") or "",
                    "points_possible": getattr(canvas_a, "points_possible", 0),
                    "due_at": getattr(canvas_a, "due_at", ""),
                    "unlock_at": getattr(canvas_a, "unlock_at", "") or "",
                    "lock_at": getattr(canvas_a, "lock_at", "") or "",
                    "submission_types": getattr(canvas_a, "submission_types", []),
                }
                diffs = compute_diff(local_fields, remote_fields)
                if diffs:
                    display_diff(f"Assignment \"{assignment.title}\"", diffs, console)
                    if _confirm(f"Assignment \"{assignment.title}\"", apply_all_ref):
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
            try:
                topic = cs.get_discussion(week_state["discussion_id"])
            except Exception:
                console.print(f"  [yellow]Discussion no longer exists, recreating...[/yellow]")
                did = cs.create_discussion(week.discussion, prompt_html)
                week_state["discussion_id"] = did
                cs.add_module_item(module_id, "Discussion", did, week.discussion.title)
                console.print(f"  [green]Recreated discussion[/green] (id={did})")
                topic = None
            if topic is not None:
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
                    if _confirm(f"Discussion \"{week.discussion.title}\"", apply_all_ref):
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


def _filter_live_weeks(weeks, override_live: bool):
    """Split weeks into (kept, skipped). If override_live is False,
    weeks with `live: true` go to skipped; otherwise everything is kept."""
    if override_live:
        return list(weeks), []
    kept = [w for w in weeks if not w.live]
    skipped = [w for w in weeks if w.live]
    return kept, skipped


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


def cmd_diff(config, weeks_dir, state: SyncState, week_num=None, all_weeks=False):
    cs = CanvasSync(config)
    if all_weeks:
        weeks = load_all_weeks(weeks_dir, course_start=config.course_start)
    else:
        path = os.path.join(weeks_dir, f"week-{week_num:02d}.md")
        if not os.path.exists(path):
            console.print(f"[red]File not found: {path}[/red]")
            sys.exit(1)
        weeks = [parse_week_file(path, course_start=config.course_start)]

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
            body_with_slides = _render_page_body(cs, week)
            local_fields = {"title": week.module_name, "body": body_with_slides}
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
                    "description": assignment.description,
                    "points_possible": assignment.points,
                    "due_at": assignment.due_datetime.isoformat(),
                    "unlock_at": assignment.unlock_datetime.isoformat(),
                    "lock_at": assignment.lock_datetime.isoformat(),
                    "submission_types": [assignment.submission_type],
                }
                remote_fields = {
                    "name": getattr(canvas_a, "name", ""),
                    "description": getattr(canvas_a, "description", "") or "",
                    "points_possible": getattr(canvas_a, "points_possible", 0),
                    "due_at": getattr(canvas_a, "due_at", ""),
                    "unlock_at": getattr(canvas_a, "unlock_at", "") or "",
                    "lock_at": getattr(canvas_a, "lock_at", "") or "",
                    "submission_types": getattr(canvas_a, "submission_types", []),
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
        cmd_push(
            config,
            args.weeks_dir,
            state,
            week_num=args.week,
            all_weeks=args.all,
            force=args.force,
            override_live=args.override_live,
        )
    elif args.command == "status":
        cmd_status(config, args.weeks_dir, state)
    elif args.command == "diff":
        cmd_diff(config, args.weeks_dir, state, week_num=args.week, all_weeks=args.all)


if __name__ == "__main__":
    main()
