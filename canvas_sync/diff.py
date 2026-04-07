from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from rich.console import Console
from rich.table import Table


@dataclass
class FieldDiff:
    field: str
    old_value: Any
    new_value: Any


def compute_diff(local: dict, remote: dict) -> list[FieldDiff]:
    diffs = []
    for key, local_val in local.items():
        remote_val = remote.get(key)
        if local_val != remote_val:
            diffs.append(FieldDiff(field=key, old_value=remote_val, new_value=local_val))
    return diffs


def display_diff(object_label: str, diffs: list[FieldDiff], console: Optional[Console] = None) -> None:
    if console is None:
        console = Console()
    if not diffs:
        console.print(f"  [green]{object_label}: no changes[/green]")
        return
    console.print(f"\n  [bold]{object_label}:[/bold]")
    for d in diffs:
        console.print(f"    [red]{d.field}:[/red] {d.old_value} [yellow]->[/yellow] {d.new_value}")


def prompt_confirm(object_label: str) -> str:
    """Prompt user for confirmation. Returns 'y', 'n', 'a', or 'q'."""
    while True:
        response = input(f"  Apply update to {object_label}? [y/n/a(ll)/q(uit)] ").strip().lower()
        if response in ("y", "n", "a", "q"):
            return response
        print("  Please enter y, n, a, or q.")
