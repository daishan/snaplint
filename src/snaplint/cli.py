from __future__ import annotations

import argparse
import sys
from pathlib import Path

from snaplint.diff import diff_snapshot_files
from snaplint.errors import SnaplintError, SnapshotReadError, UsageError
from snaplint.models import RenderOptions
from snaplint.render import render_diff
from snaplint.snapshot import build_snapshot_file, read_snapshot, write_snapshot


def main() -> int:
    try:
        return _main()
    except SnaplintError as e:
        print(f"error: {e}", file=sys.stderr)
        if isinstance(e, UsageError):
            return 2
        if isinstance(e, SnapshotReadError):
            return 2
        return 3
    except Exception as e:
        print(f"unexpected internal error: {e}", file=sys.stderr)
        return 3


def _main() -> int:
    parser = argparse.ArgumentParser(description="Snapshot linter findings.")
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 0.1.1"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # diff command
    parser_diff = subparsers.add_parser(
        "diff", help="Compare linter output to a snapshot."
    )
    parser_diff.add_argument(
        "snapshot_path", type=Path, help="Path to the snapshot file."
    )

    # take-snapshot command
    parser_take_snapshot = subparsers.add_parser(
        "take-snapshot", help="Write linter output to a snapshot file."
    )
    parser_take_snapshot.add_argument(
        "snapshot_path", type=Path, help="Path to the snapshot file."
    )

    args = parser.parse_args()

    if args.command == "take-snapshot":
        return _run_take_snapshot(args)
    if args.command == "diff":
        return _run_diff(args)

    # This should be unreachable due to the initial check
    return 3


def _run_take_snapshot(args: argparse.Namespace) -> int:
    if sys.stdin.isatty():
        raise UsageError("stdin is empty. Pipe linter output to snaplint.")

    snapshot_path = args.snapshot_path

    # Build snapshot from stdin
    snapshot_file = build_snapshot_file(sys.stdin)

    try:
        with snapshot_path.open("w", encoding="utf-8") as f:
            write_snapshot(snapshot_file, f)
    except OSError as e:
        raise SnapshotReadError(
            f"Could not write to snapshot file {snapshot_path}: {e}"
        ) from e

    print(f"Snapshot written to {snapshot_path}", file=sys.stderr)
    return 0


def _run_diff(args: argparse.Namespace) -> int:
    if sys.stdin.isatty():
        raise UsageError("stdin is empty. Pipe linter output to snaplint.")

    snapshot_path = args.snapshot_path
    if not snapshot_path.exists():
        raise SnapshotReadError(f"Snapshot file not found: {snapshot_path}")

    try:
        with snapshot_path.open("r", encoding="utf-8") as f:
            snapshot_file = read_snapshot(f)
    except OSError as e:
        raise SnapshotReadError(
            f"Could not read snapshot file {snapshot_path}: {e}"
        ) from e

    current_file = build_snapshot_file(sys.stdin)

    diff_result = diff_snapshot_files(
        current=current_file,
        snapshot=snapshot_file,
    )

    render_options = RenderOptions(
        stdout_is_tty=sys.stdout.isatty(),
        color_enabled=True,  # Always true, render function checks tty
    )

    render_diff(
        diff=diff_result,
        options=render_options,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    if diff_result.total_added > 0:
        return 1  # New issues found

    return 0  # No new issues


if __name__ == "__main__":
    sys.exit(main())
