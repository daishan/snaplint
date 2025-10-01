from __future__ import annotations

import argparse
import sys
from pathlib import Path

from snaplint.diff import diff_issue_sets
from snaplint.errors import SnaplintError, SnapshotReadError, UsageError
from snaplint.models import RenderOptions
from snaplint.render import render_diff
from snaplint.snapshot import build_issue_set, read_snapshot


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
    subparsers = parser.add_subparsers(dest="command", required=True)

    # diff command
    parser_diff = subparsers.add_parser("diff", help="Compare linter output to a snapshot.")
    parser_diff.add_argument("snapshot_path", type=Path, help="Path to the snapshot file.")
    parser_diff.add_argument("--ref", type=str, help="Git ref to compare against for moved errors.")

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
    try:
        with snapshot_path.open("w", encoding="utf-8") as f:
            for line in sys.stdin:
                f.write(line)
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
            snapshot_set = read_snapshot(f)
    except OSError as e:
        raise SnapshotReadError(
            f"Could not read snapshot file {snapshot_path}: {e}"
        ) from e

    current_set = build_issue_set(sys.stdin)

    diff_result = diff_issue_sets(
        current=current_set,
        snapshot=snapshot_set,
        ref=args.ref,
    )

    render_options = RenderOptions(
        stdout_is_tty=sys.stdout.isatty(),
        color_enabled=True,  # Always true, render function checks tty
    )

    render_diff(
        diff=diff_result,
        current_set=current_set,
        snapshot_set=snapshot_set,
        options=render_options,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    if diff_result.added:
        return 1  # New issues found

    return 0  # No new issues


if __name__ == "__main__":
    sys.exit(main())