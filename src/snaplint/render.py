from __future__ import annotations

import sys
from typing import TextIO

from snaplint.models import DiffResult, IssueSet, RenderOptions

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def _colorize(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


def render_diff(
    diff: DiffResult,
    current_set: IssueSet,
    snapshot_set: IssueSet,
    options: RenderOptions,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> None:
    """Render the diff result to stdout and stderr."""
    use_color = options.color_enabled and options.stdout_is_tty

    # Print removed issues (in green)
    for key in diff.removed:
        line = snapshot_set.index[key].original
        output = f"{line} (-)"
        if use_color:
            print(_colorize(output, GREEN), file=stdout)
        else:
            print(output, file=stdout)

    # Print added issues (in red)
    for key in diff.added:
        line = current_set.index[key].original
        output = f"{line} (+)"
        if use_color:
            print(_colorize(output, RED), file=stdout)
        else:
            print(output, file=stdout)

    # Print moved issues (in yellow)
    for old_key, new_key in diff.moved:
        old_line = snapshot_set.index[old_key].original
        new_line = current_set.index[new_key].original
        output = f"{old_line} -> {new_line.split(':', 1)[1]} (~)"
        if use_color:
            print(_colorize(output, YELLOW), file=stdout)
        else:
            print(output, file=stdout)

    # Print summary to stderr
    summary = (
        f"summary: +{len(diff.added)} -{len(diff.removed)} ~{len(diff.moved)} "
        f"(unchanged {diff.unchanged_count})"
    )
    print(summary, file=stderr)
