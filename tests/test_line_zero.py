"""Tests for file-level (line 0) errors."""
from __future__ import annotations

from pathlib import Path

from snaplint.diff import diff_snapshot_files
from snaplint.snapshot import build_snapshot_file


def test_line_zero_errors(tmp_path: Path):
    """Test that file-level errors (line 0) are properly tracked."""
    file1 = tmp_path / "test.py"
    file1.write_text("import sys\n")
    
    file_path = str(file1)
    
    # File-level errors often have line:0
    snapshot_lines = [
        f"{file_path}:0:0: F401 'sys' imported but unused",
        f"{file_path}:1:1: E302 expected 2 blank lines",
    ]
    
    snapshot_file = build_snapshot_file(snapshot_lines)
    
    # Verify both errors were captured
    assert len(snapshot_file.files) == 1
    assert snapshot_file.files[0].error_count == 2
    
    # Verify the line 0 error has a special hash based on file path
    entries = snapshot_file.files[0].entries
    line_zero_entry = next((e for e in entries if e.line == 0), None)
    assert line_zero_entry is not None
    assert line_zero_entry.code == "F401"
    assert line_zero_entry.sha1  # Should have a hash
    
    # Verify the line 1 error also exists
    line_one_entry = next((e for e in entries if e.line == 1), None)
    assert line_one_entry is not None
    assert line_one_entry.code == "E302"


def test_line_zero_diff(tmp_path: Path):
    """Test diffing with file-level errors."""
    file1 = tmp_path / "test.py"
    file1.write_text("import sys\n")
    
    file_path = str(file1)
    
    # Snapshot has a file-level error
    snapshot_lines = [
        f"{file_path}:0:0: F401 'sys' imported but unused",
    ]
    
    # Current has the same file-level error
    current_lines = [
        f"{file_path}:0:0: F401 'sys' imported but unused",
    ]
    
    snapshot_file = build_snapshot_file(snapshot_lines)
    current_file = build_snapshot_file(current_lines)
    
    diff = diff_snapshot_files(current=current_file, snapshot=snapshot_file)
    
    # Should show no changes
    assert diff.total_unchanged == 1
    assert diff.total_added == 0
    assert diff.total_removed == 0


def test_line_zero_error_removed(tmp_path: Path):
    """Test that removing a file-level error is detected."""
    file1 = tmp_path / "test.py"
    file1.write_text("import sys\n")
    
    file_path = str(file1)
    
    # Snapshot has a file-level error
    snapshot_lines = [
        f"{file_path}:0:0: F401 'sys' imported but unused",
        f"{file_path}:1:1: E302 expected 2 blank lines",
    ]
    
    # Current only has the line 1 error
    current_lines = [
        f"{file_path}:1:1: E302 expected 2 blank lines",
    ]
    
    snapshot_file = build_snapshot_file(snapshot_lines)
    current_file = build_snapshot_file(current_lines)
    
    diff = diff_snapshot_files(current=current_file, snapshot=snapshot_file)
    
    # Should show one removed error
    assert diff.total_unchanged == 1
    assert diff.total_added == 0
    assert diff.total_removed == 1
    assert diff.file_diffs[0].removed[0].line == 0


def test_multiple_files_with_line_zero(tmp_path: Path):
    """Test multiple files each with their own line 0 errors."""
    file1 = tmp_path / "file1.py"
    file1.write_text("import sys\n")
    file2 = tmp_path / "file2.py"
    file2.write_text("import os\n")
    
    file1_path = str(file1)
    file2_path = str(file2)
    
    snapshot_lines = [
        f"{file1_path}:0:0: F401 'sys' imported but unused",
        f"{file2_path}:0:0: F401 'os' imported but unused",
    ]
    
    snapshot_file = build_snapshot_file(snapshot_lines)
    
    # Should have 2 files, each with 1 error at line 0
    assert len(snapshot_file.files) == 2
    assert all(f.error_count == 1 for f in snapshot_file.files)
    assert all(f.entries[0].line == 0 for f in snapshot_file.files)
    
    # Each file should have a different hash (based on different file paths)
    hashes = [f.entries[0].sha1 for f in snapshot_file.files]
    assert hashes[0] != hashes[1]
