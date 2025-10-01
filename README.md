# snaplint

A CLI to snapshot current linter findings and later diff new runs against that snapshot, so teams can adopt linters on large repos without breaking CI.

## Installation

```bash
pip install snaplint
```

## Usage

`snaplint` reads linter output from `STDIN`.

### `snaplint diff <SNAPSHOT_PATH>`

Compares current linter output from `STDIN` against a snapshot file.

**Arguments:**
- `<SNAPSHOT_PATH>`: Path to the snapshot file.

**Options:**
- `--ref <GIT_REF>`: (Optional) A Git reference (e.g., `origin/main`, `HEAD~1`) to compare against for detecting moved errors. When provided, `snaplint` will attempt to identify errors that have only changed their line number by comparing the content of the affected lines in the current branch against the specified Git reference.

**Output:**
-   Lines that are new (present now, absent in snapshot) → printed in <span style="color:red">red</span>, with ` (+)` suffix.
-   Lines that are removed (present in snapshot, absent now) → printed in <span style="color:green">green</span>, with ` (-)` suffix.
-   Lines that have moved (same error, different line number) → printed in <span style="color:yellow">yellow</span>, with ` (~)` suffix.
-   A one-line summary to `STDERR`: `summary: +<new> -<removed> ~<moved> (unchanged <same>)`.

**Exit codes:**
-   `0` → no new issues
-   `1` → there are new issues
-   `2` → usage/IO errors (e.g., missing snapshot, no stdin)
-   `3` → unexpected internal error

**Examples:**

```bash
# Compare a new run to the snapshot
flake8 . | snaplint diff lint.snapshot.txt

# Compare a new run to the snapshot, detecting moved errors against 'origin/main'
flake8 . | snaplint diff lint.snapshot.txt --ref origin/main
```

### `snaplint take-snapshot <SNAPSHOT_PATH>`

Writes `STDIN` directly to `SNAPSHOT_PATH` verbatim (no parsing).

**Arguments:**
- `<SNAPSHOT_PATH>`: Path to the snapshot file.

**Output:**
-   Writes snapshot file; prints a short success line (to `STDERR`).

**Exit codes:**
-   `0` → success
-   `2` → usage/IO errors

**Examples:**

```bash
# Create a snapshot file (via shell redirection)
flake8 . > lint.snapshot.txt

# Create a snapshot file using the take-snapshot command
flake8 . | snaplint take-snapshot lint.snapshot.txt
```

## Supported Linters

`snaplint` automatically detects output from:

-   `flake8` (or compatibles like `flake9`)
-   `mypy`
-   `pylint`

If the line format is not recognized, `snaplint` will attempt a generic `path:line:col: message` parsing and warn on `STDERR` for any lines it cannot parse.