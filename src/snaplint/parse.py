from __future__ import annotations

import re
from typing import Final, Iterable, Iterator, Pattern

from snaplint.errors import ParseWarning
from snaplint.models import IssueKey, IssueLine

# Regexes for different linter formats
# flake8: path/to/file.py:LINE:COL: CODE Message
FLAKE8_RE: Final[Pattern[str]] = re.compile(
    r"^(?P<path>(?:\./)?[^:]+):(?P<line>\d+):(?P<col>\d+): "
    r"(?P<code>[A-Z]+\d+) (?P<msg>.+)$"
)

MYPY_RE: Final[Pattern[str]] = re.compile(
    r"^(?P<path>[^:]+):(?P<line>\d+):(?:(?P<col>\d+):)? "
    r"(?P<level>error|warning|note): (?P<msg>.+?)(?:\s+\[(?P<code>[a-z-]+)\])?$"
)

# pylint (style 1): path/to/file.py:LINE:COL: CODE: Message (symbol)
PYLINT_RE1: Final[Pattern[str]] = re.compile(
    r"^(?P<path>[^:]+):(?P<line>\d+):(?P<col>\d+): (?P<code>[A-Z]\d{4}): "
    r"(?P<msg>.+) \((?P<symbol>.*)\)$"
)

# pylint (style 2): path/to/file.py:LINE: [CODE(symbol)] Message
PYLINT_RE2: Final[Pattern[str]] = re.compile(
    r"^(?P<path>[^:]+):(?P<line>\d+): \[(?P<code>[A-Z]\d{4})\((?P<symbol>.*)\)\] "
    r"(?P<msg>.+)$"
)

# Generic: path:line[:col]: message
GENERIC_RE: Final[Pattern[str]] = re.compile(
    r"^(?P<path>[^:]+):(?P<line>\d+):(?:(?P<col>\d+):)? (?P<msg>.+)$"
)


def _normalize_message(text: str) -> str:
    """Collapse internal whitespace and trim."""
    return re.sub(r"\s+", " ", text).strip()


def _parse_line(line: str) -> IssueLine | None:
    """Attempt to parse a single line of linter output."""
    line = line.strip()
    if not line:
        return None

    # Flake8
    if match := FLAKE8_RE.match(line):
        return IssueLine(
            original=line,
            tool="flake",
            path=str(match.group("path")),
            line=int(match.group("line")),
            column=int(match.group("col")),
            code=str(match.group("code")),
            message=_normalize_message(match.group("msg")),
        )

    # Mypy
    if match := MYPY_RE.match(line):
        code = match.group("code") or match.group("level")
        return IssueLine(
            original=line,
            tool="mypy",
            path=str(match.group("path")),
            line=int(match.group("line")),
            column=int(match.group("col") or 0),
            code=str(code),
            message=_normalize_message(match.group("msg")),
        )

    # Pylint (Style 1)
    if match := PYLINT_RE1.match(line):
        return IssueLine(
            original=line,
            tool="pylint",
            path=str(match.group("path")),
            line=int(match.group("line")),
            column=int(match.group("col")),
            code=str(match.group("code")),
            message=_normalize_message(match.group("msg")),
        )

    # Pylint (Style 2)
    if match := PYLINT_RE2.match(line):
        return IssueLine(
            original=line,
            tool="pylint",
            path=str(match.group("path")),
            line=int(match.group("line")),
            column=0,  # Column is not available in this format
            code=str(match.group("code")),
            message=_normalize_message(match.group("msg")),
        )

    # Generic Fallback
    if match := GENERIC_RE.match(line):
        return IssueLine(
            original=line,
            tool="unknown",
            path=str(match.group("path")),
            line=int(match.group("line")),
            column=int(match.group("col") or 0),
            message=_normalize_message(match.group("msg")),
        )

    return None


def get_issue_key(issue: IssueLine) -> IssueKey:
    """Create an identity key for an issue."""
    if issue.code:
        return IssueKey(
            path=issue.path,
            line=issue.line,
            column=issue.column,
            code=issue.code,
        )
    return IssueKey(
        path=issue.path,
        line=issue.line,
        column=issue.column,
        message=issue.message,
    )


def parse_lines(lines: Iterable[str]) -> Iterator[IssueLine | ParseWarning]:
    """Parse an iterator of lines, yielding IssueLine or ParseWarning."""
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        try:
            issue = _parse_line(stripped_line)
            if issue:
                yield issue
            else:
                yield ParseWarning(line=stripped_line)
        except (ValueError, TypeError) as e:
            # Catch validation errors from Pydantic models
            yield ParseWarning(line=f"{stripped_line} (parse error: {e})")
