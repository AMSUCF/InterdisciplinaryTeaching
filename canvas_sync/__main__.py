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

    status_p = sub.add_parser("status", help="Show sync status for all weeks")  # noqa: F841

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
