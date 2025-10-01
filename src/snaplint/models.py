from __future__ import annotations

import re
from typing import Annotated, Any, Literal, Mapping, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    StrictStr,
    model_validator,
)
from pydantic.functional_validators import AfterValidator

# Custom Types


def validate_normalized_path(v: Any) -> str:
    if not isinstance(v, str):
        raise TypeError("string required")
    # On Windows, drive letters are case-insensitive, so normalize to lower
    if re.match(r"^[a-zA-Z]:\\", v):
        v = v[0].lower() + v[1:]
    # Normalize path separators and remove leading './'
    v = v.replace("\\", "/")
    while v.startswith("./"):
        v = v[2:]
    # Collapse multiple slashes
    v = re.sub(r"//+", "/", v)
    if not v:
        raise ValueError("path cannot be empty")
    return v


NormalizedPath = Annotated[str, AfterValidator(validate_normalized_path)]

def to_upper(v: str) -> str:
    return v.upper()


ConstrainedStrUpper = Annotated[str, AfterValidator(to_upper)]


# Pydantic Models


class IssueLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    original: StrictStr
    tool: Literal["flake", "mypy", "pylint", "unknown"]
    path: NormalizedPath
    line: NonNegativeInt
    column: NonNegativeInt = 0
    code: Optional[ConstrainedStrUpper] = None
    message: StrictStr


class IssueKey(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: NormalizedPath
    line: NonNegativeInt
    column: NonNegativeInt
    code: Optional[ConstrainedStrUpper] = None
    message: Optional[StrictStr] = None

    @model_validator(mode='after')
    def code_or_message_exists(self) -> IssueKey:
        if self.code is None and self.message is None:
            raise ValueError("Either code or message must be set")
        if self.code is not None and self.message is not None:
            raise ValueError("Message must be None if code is set")
        return self


class IssueSet(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: frozenset[IssueKey]
    index: Mapping[IssueKey, IssueLine]


class DiffResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    added: tuple[IssueKey, ...]
    removed: tuple[IssueKey, ...]
    moved: tuple[tuple[IssueKey, IssueKey], ...]
    unchanged_count: NonNegativeInt


class RenderOptions(BaseModel):
    model_config = ConfigDict(frozen=True)

    stdout_is_tty: bool
    color_enabled: bool
    sort: bool = True
