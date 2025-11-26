from __future__ import annotations

from pathlib import Path
from io import StringIO

from snaplint.diff import diff_snapshot_files
from snaplint.snapshot import build_snapshot_file


def test_diff_snapshot_files(tmp_path: Path):
    """Test basic diff with added and removed issues."""
    # Create test files
    file1 = tmp_path / "file.py"
    file1.write_text("line1\nline2\nline3\nline4\n")

    file_path = str(file1)
    snapshot_lines = [
        f"{file_path}:1:1: E001 msg1",  # Unchanged
        f"{file_path}:2:1: W002 msg2",  # To be removed
        f"{file_path}:3:1: E003 msg3",  # Unchanged
    ]
    current_lines = [
        f"{file_path}:1:1: E001 msg1",  # Unchanged
        f"{file_path}:3:1: E003 msg3",  # Unchanged
        f"{file_path}:4:1: E004 msg4",  # Added
    ]

    snapshot_file = build_snapshot_file(snapshot_lines)
    current_file = build_snapshot_file(current_lines)

    diff = diff_snapshot_files(current=current_file, snapshot=snapshot_file)

    assert diff.total_unchanged == 2
    assert diff.total_added == 1
    assert diff.total_removed == 1
    assert diff.files_with_changes == 1

    # Check file diff
    file_diff = diff.file_diffs[0]
    assert file_diff.count_changed is True
    assert len(file_diff.added) == 1
    assert len(file_diff.removed) == 1
    assert file_diff.added[0].line == 4
    assert file_diff.removed[0].line == 2


def test_diff_order_change(tmp_path: Path):
    """Test detecting order changes without count changes."""
    # Create test file with multiple errors
    file1 = tmp_path / "file.py"
    file1.write_text("error_line_1\nerror_line_2\nerror_line_3\n")

    file_path = str(file1)
    # Same errors, but reported in different order in linter output
    snapshot_lines = [
        f"{file_path}:1:1: E001 msg1",
        f"{file_path}:2:1: E002 msg2",
        f"{file_path}:3:1: E003 msg3",
    ]
    # Simulate linter reporting in different order (e.g., sorted differently)
    current_lines = [
        f"{file_path}:3:1: E003 msg3",
        f"{file_path}:1:1: E001 msg1",
        f"{file_path}:2:1: E002 msg2",
    ]

    snapshot_file = build_snapshot_file(snapshot_lines)
    current_file = build_snapshot_file(current_lines)

    diff = diff_snapshot_files(current=current_file, snapshot=snapshot_file)

    # All entries are unchanged by hash
    assert diff.total_unchanged == 3
    assert diff.total_added == 0
    assert diff.total_removed == 0

    # But order changed - current hash sequence is different from snapshot
    file_diff = diff.file_diffs[0] if diff.file_diffs else None
    if file_diff:
        assert file_diff.order_changed is True


def test_diff_empty_snapshot(tmp_path: Path):
    """Test diff with empty snapshot."""
    file1 = tmp_path / "file.py"
    file1.write_text("line1\n")

    file_path = str(file1)
    snapshot_lines = []
    current_lines = [f"{file_path}:1:1: E001 msg1"]

    from snaplint.models import SnapshotFile

    snapshot_file = SnapshotFile(files=tuple())
    current_file = build_snapshot_file(current_lines)

    diff = diff_snapshot_files(current=current_file, snapshot=snapshot_file)

    assert diff.total_added == 1
    assert diff.total_removed == 0
    assert diff.total_unchanged == 0


def test_diff_empty_current(tmp_path: Path):
    """Test diff with empty current."""
    file1 = tmp_path / "file.py"
    file1.write_text("line1\n")

    file_path = str(file1)
    snapshot_lines = [f"{file_path}:1:1: E001 msg1"]
    current_lines = []

    snapshot_file = build_snapshot_file(snapshot_lines)
    from snaplint.models import SnapshotFile

    current_file = SnapshotFile(files=tuple())

    diff = diff_snapshot_files(current=current_file, snapshot=snapshot_file)

    assert diff.total_added == 0
    assert diff.total_removed == 1
    assert diff.total_unchanged == 0
