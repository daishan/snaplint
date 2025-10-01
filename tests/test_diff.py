from __future__ import annotations

import random

from snaplint.diff import diff_issue_sets
from snaplint.models import DiffResult, IssueKey
from snaplint.snapshot import build_issue_set


def test_diff_issue_sets():
    snapshot_lines = [
        "file.py:1:1: E001 msg1",  # Unchanged
        "file.py:2:1: W002 msg2",  # To be removed
        "file.py:3:1: E003 msg3",  # Unchanged
    ]
    current_lines = [
        "file.py:1:1: E001 msg1",  # Unchanged
        "file.py:3:1: E003 msg3",  # Unchanged
        "file.py:4:1: E004 msg4",  # Added
    ]

    snapshot_set = build_issue_set(snapshot_lines)
    current_set = build_issue_set(current_lines)

    diff = diff_issue_sets(current=current_set, snapshot=snapshot_set)

    assert diff.unchanged_count == 2
    assert len(diff.added) == 1
    assert len(diff.removed) == 1

    added_key = IssueKey(path="file.py", line=4, column=1, code="E004")
    removed_key = IssueKey(path="file.py", line=2, column=1, code="W002")

    assert diff.added[0] == added_key
    assert diff.removed[0] == removed_key


def test_diff_order_insensitivity():
    snapshot_lines = [
        "file.py:1:1: E001 msg1",
        "file.py:2:1: W002 msg2",
        "file.py:3:1: E003 msg3",
    ]
    current_lines = [
        "file.py:4:1: E004 msg4",
        "file.py:1:1: E001 msg1",
        "file.py:3:1: E003 msg3",
    ]

    # Shuffle the input to ensure order doesn't matter
    random.shuffle(current_lines)

    snapshot_set = build_issue_set(snapshot_lines)
    current_set = build_issue_set(current_lines)

    diff = diff_issue_sets(current=current_set, snapshot=snapshot_set)

    expected_diff = DiffResult(
        added=(
            IssueKey(path="file.py", line=4, column=1, code="E004"),
        ),
        removed=(
            IssueKey(path="file.py", line=2, column=1, code="W002"),
        ),
        moved=(),
        unchanged_count=2,
    )

    assert diff == expected_diff


def test_diff_empty_snapshot():
    snapshot_lines = []
    current_lines = ["file.py:1:1: E001 msg1"]

    snapshot_set = build_issue_set(snapshot_lines)
    current_set = build_issue_set(current_lines)

    diff = diff_issue_sets(current=current_set, snapshot=snapshot_set)

    assert len(diff.added) == 1
    assert len(diff.removed) == 0
    assert diff.unchanged_count == 0


def test_diff_empty_current():
    snapshot_lines = ["file.py:1:1: E001 msg1"]
    current_lines = []

    snapshot_set = build_issue_set(snapshot_lines)
    current_set = build_issue_set(current_lines)

    diff = diff_issue_sets(current=current_set, snapshot=snapshot_set)

    assert len(diff.added) == 0
    assert len(diff.removed) == 1
    assert diff.unchanged_count == 0


def test_diff_moved_issues():
    snapshot_lines = ["file.py:2:1: E001 my error"]
    current_lines = ["file.py:3:1: E001 my error"]

    snapshot_set = build_issue_set(snapshot_lines)
    current_set = build_issue_set(current_lines)

    diff = diff_issue_sets(current=current_set, snapshot=snapshot_set, ref="main")

    assert len(diff.moved) == 1
    assert len(diff.added) == 0
    assert len(diff.removed) == 0
    assert diff.unchanged_count == 0

    old_key, new_key = diff.moved[0]
    assert old_key.line == 2
    assert new_key.line == 3