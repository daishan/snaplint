from __future__ import annotations

import sys
from typing import TextIO

from snaplint.models import DiffResult, RenderOptions

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def _colorize(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


def render_diff(
    diff: DiffResult,
    options: RenderOptions,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> None:
    """Render the diff result to stdout and stderr."""
    use_color = options.color_enabled and options.stdout_is_tty

    # Process each file with changes
    for file_diff in diff.file_diffs:
        # Print file header if there are changes
        if file_diff.added or file_diff.removed or file_diff.order_changed:
            header = f"\n{file_diff.path}:"
            if use_color:
                print(_colorize(header, BLUE), file=stdout)
            else:
                print(header, file=stdout)

            # Show count change indicator
            if file_diff.count_changed:
                old_count = file_diff.unchanged_count + len(file_diff.removed)
                new_count = file_diff.unchanged_count + len(file_diff.added)
                count_msg = f"  [count changed: {old_count} -> {new_count}]"
                if use_color:
                    print(_colorize(count_msg, YELLOW), file=stdout)
                else:
                    print(count_msg, file=stdout)

            # Show order change indicator
            if file_diff.order_changed and not file_diff.count_changed:
                order_msg = "  [order changed]"
                if use_color:
                    print(_colorize(order_msg, YELLOW), file=stdout)
                else:
                    print(order_msg, file=stdout)

            # Print removed issues (in green)
            for entry in file_diff.removed:
                output = f"  - {entry.original}"
                if use_color:
                    print(_colorize(output, GREEN), file=stdout)
                else:
                    print(output, file=stdout)

            # Print added issues (in red)
            for entry in file_diff.added:
                output = f"  + {entry.original}"
                if use_color:
                    print(_colorize(output, RED), file=stdout)
                else:
                    print(output, file=stdout)

    # Print summary to stderr
    summary_parts = [
        f"+{diff.total_added}",
        f"-{diff.total_removed}",
        f"(unchanged {diff.total_unchanged})",
    ]

    if diff.files_with_changes > 0:
        summary_parts.append(f"{diff.files_with_changes} file(s) with changes")

    summary = f"summary: {' '.join(summary_parts)}"
    print(summary, file=stderr)
