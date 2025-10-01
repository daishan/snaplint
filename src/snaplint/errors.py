class SnaplintError(Exception):
    """Base class for all snaplint exceptions."""


class UsageError(SnaplintError):
    """For CLI usage errors."""


class SnapshotReadError(SnaplintError):
    """For errors reading the snapshot file."""


class ParseWarning(SnaplintError):
    """A non-fatal warning for a line that could not be parsed."""

    def __init__(self, line: str):
        self.line = line
        super().__init__(f"unparsable: {line}")
