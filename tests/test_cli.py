from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

from snaplint.cli import main


def mock_stdin(monkeypatch, text: str):
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))

def mock_argv(monkeypatch, *args: str):
    monkeypatch.setattr(sys, "argv", ["snaplint", *args])


@pytest.fixture
def snapshot_file(tmp_path: Path) -> Path:
    return tmp_path / "lint.snapshot.txt"


def test_cli_diff_no_new_issues(
    monkeypatch,
    snapshot_file,
    capsys,
):
    snapshot_content = "file.py:1:1: E001 msg1\n"
    snapshot_file.write_text(snapshot_content)
    mock_stdin(monkeypatch, text=snapshot_content)
    mock_argv(monkeypatch, "diff", str(snapshot_file))

    return_code = main()

    assert return_code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "summary: +0 -0 ~0 (unchanged 1)" in captured.err


def test_cli_diff_new_issues(
    monkeypatch,
    snapshot_file,
    capsys,
):
    snapshot_file.write_text("file.py:1:1: E001 msg1\n")
    mock_stdin(monkeypatch, text="file.py:2:1: E002 msg2\n")
    mock_argv(monkeypatch, "diff", str(snapshot_file))

    return_code = main()

    assert return_code == 1
    captured = capsys.readouterr()
    assert "file.py:2:1: E002 msg2 (+)" in captured.out
    assert "summary: +1 -1 ~0 (unchanged 0)" in captured.err


def test_cli_diff_removed_issues(
    monkeypatch,
    snapshot_file,
    capsys,
):
    snapshot_file.write_text("file.py:1:1: E001 msg1\n")
    mock_stdin(monkeypatch, text="")
    mock_argv(monkeypatch, "diff", str(snapshot_file))

    return_code = main()

    assert return_code == 0
    captured = capsys.readouterr()
    assert "file.py:1:1: E001 msg1 (-)" in captured.out
    assert "summary: +0 -1 ~0 (unchanged 0)" in captured.err


def test_cli_usage_error_no_args(monkeypatch, capsys):
    mock_argv(monkeypatch)
    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 2
    assert "the following arguments are required: command" in capsys.readouterr().err


def test_cli_usage_error_bad_command(monkeypatch, capsys):
    mock_argv(monkeypatch, "badcmd")
    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 2
    assert "invalid choice: 'badcmd'" in capsys.readouterr().err


def test_cli_snapshot_not_found(monkeypatch, capsys):
    mock_argv(monkeypatch, "diff", "nonexistent.txt")
    return_code = main()
    assert return_code == 2
    assert "Snapshot file not found" in capsys.readouterr().err


def test_cli_no_stdin(monkeypatch, snapshot_file, capsys):
    snapshot_file.touch()
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    mock_argv(monkeypatch, "diff", str(snapshot_file))
    return_code = main()
    assert return_code == 2
    assert "stdin is empty" in capsys.readouterr().err


def test_cli_take_snapshot(
    monkeypatch,
    snapshot_file,
    capsys,
):
    input_content = "file.py:1:1: E001 msg1\n"
    mock_stdin(monkeypatch, text=input_content)
    mock_argv(monkeypatch, "take-snapshot", str(snapshot_file))

    return_code = main()

    assert return_code == 0
    assert snapshot_file.read_text() == input_content
    assert f"Snapshot written to {snapshot_file}" in capsys.readouterr().err
