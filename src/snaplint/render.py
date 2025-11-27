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
        # Print removed issues only in verbose mode (in green with - suffix)
        if options.verbose:
            for entry in file_diff.removed:
                output = f"{entry.original} (-)"
                if use_color:
                    print(_colorize(output, GREEN), file=stdout)
                else:
                    print(output, file=stdout)

        # Print added issues (in red with + suffix)
        for entry in file_diff.added:
            output = f"{entry.original} (+)"
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
