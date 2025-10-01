from __future__ import annotations

import sys
from typing import IO, Iterable

from snaplint.errors import ParseWarning
from snaplint.models import IssueKey, IssueLine, IssueSet
from snaplint.parse import get_issue_key, parse_lines


def build_issue_set(lines: Iterable[str]) -> IssueSet:
    """Build an IssueSet from an iterable of string lines."""
    issue_index: dict[IssueKey, IssueLine] = {}
    for result in parse_lines(lines):
        if isinstance(result, ParseWarning):
            print(f"snaplint: {result}", file=sys.stderr)
        elif isinstance(result, IssueLine):
            key = get_issue_key(result)
            # First one wins, ensuring stability of `original` line
            if key not in issue_index:
                issue_index[key] = result

    return IssueSet(
        items=frozenset(issue_index.keys()),
        index=issue_index,
    )


def read_snapshot(snapshot_file: IO[str]) -> IssueSet:
    """Read a snapshot file and build an IssueSet."""
    return build_issue_set(snapshot_file)
