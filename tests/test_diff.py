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
        added=(IssueKey(path="file.py", line=4, column=1, code="E004"),),
        removed=(IssueKey(path="file.py", line=2, column=1, code="W002"),),
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


import os
import subprocess
from pathlib import Path


def test_diff_moved_issues(tmp_path: Path):
    # Create a git repository
    os.chdir(tmp_path)
    subprocess.run(["git", "init"])
    subprocess.run(["git", "config", "user.name", "tester"])
    subprocess.run(["git", "config", "user.email", "tester@example.com"])

    # Create the initial file
    file_path = tmp_path / "file.py"
    file_path.write_text("line1\nline2\nline3\n")
    subprocess.run(["git", "add", "file.py"])
    subprocess.run(["git", "commit", "-m", "initial commit"])
    subprocess.run(["git", "tag", "v1"])

    # Create the snapshot
    snapshot_lines = ["file.py:2:1: E001 my error"]
    snapshot_set = build_issue_set(snapshot_lines)

    # Modify the file
    file_path.write_text("line1\nline1.5\nline2\nline3\n")

    # Create the current issues
    current_lines = ["file.py:3:1: E001 my error"]
    current_set = build_issue_set(current_lines)

    # Run the diff
    diff = diff_issue_sets(current=current_set, snapshot=snapshot_set, ref="v1")

    assert len(diff.moved) == 1
    assert len(diff.added) == 0
    assert len(diff.removed) == 0
    assert diff.unchanged_count == 0

    old_key, new_key = diff.moved[0]
    assert old_key.line == 2
    assert new_key.line == 3


def test_diff_multiple_moved_issues(tmp_path: Path):
    # Create a git repository
    os.chdir(tmp_path)
    subprocess.run(["git", "init"])
    subprocess.run(["git", "config", "user.name", "tester"])
    subprocess.run(["git", "config", "user.email", "tester@example.com"])

    # Create the initial file
    file_path = tmp_path / "file.py"
    file_path.write_text(
        "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    )
    subprocess.run(["git", "add", "file.py"])
    subprocess.run(["git", "commit", "-m", "initial commit"])
    subprocess.run(["git", "tag", "v1"])

    # Create the snapshot
    snapshot_lines = [
        "file.py:2:1: E001 error1",
        "file.py:4:1: E002 error2",
        "file.py:8:1: E003 error3",
    ]
    snapshot_set = build_issue_set(snapshot_lines)

    # Modify the file
    file_path.write_text(
        "line1\ninserted1\ninserted2\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    )

    # Create the current issues
    current_lines = [
        "file.py:4:1: E001 error1",
        "file.py:6:1: E002 error2",
        "file.py:10:1: E003 error3",
    ]
    current_set = build_issue_set(current_lines)

    # Run the diff
    diff = diff_issue_sets(current=current_set, snapshot=snapshot_set, ref="v1")

    assert len(diff.moved) == 3
    assert len(diff.added) == 0
    assert len(diff.removed) == 0
    assert diff.unchanged_count == 0

    # Sort moved issues for stable assertion
    moved = sorted(diff.moved, key=lambda pair: pair[0].line)

    # error1 moved from 2 to 4
    old_key, new_key = moved[0]
    assert old_key.line == 2
    assert new_key.line == 4

    # error2 moved from 4 to 6
    old_key, new_key = moved[1]
    assert old_key.line == 4
    assert new_key.line == 6

    # error3 moved from 8 to 10
    old_key, new_key = moved[2]
    assert old_key.line == 8
    assert new_key.line == 10
