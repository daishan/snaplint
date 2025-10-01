# snaplint

A CLI to snapshot current linter findings and later diff new runs against that snapshot, so teams can adopt linters on large repos without breaking CI.

## Installation

```bash
pip install snaplint
```

## Usage

`snaplint` reads linter output from `STDIN`.

### Create a snapshot

First, create a snapshot of the current linter findings. You can do this with shell redirection:

```bash
flake8 . > lint.snapshot.txt
```

Or, you can use the `take-snapshot` helper command:

```bash
flake8 . | snaplint take-snapshot lint.snapshot.txt
```

### Compare against a snapshot

Later, to see what's changed, pipe a new linter run into `snaplint diff`:

```bash
flake8 . | snaplint diff lint.snapshot.txt
```

-   **New issues** will be printed in <span style="color:red">red</span>.
-   **Fixed issues** will be printed in <span style="color:green">green</span>.

`snaplint` will exit with code `0` only if no new issues were introduced.

### Supported Linters

`snaplint` automatically detects output from:

-   `flake8` (or compatibles like `flake9`)
-   `mypy`
-   `pylint`

If the line format is not recognized, `snaplint` will attempt a generic `path:line:col: message` parsing and warn on `STDERR` for any lines it cannot parse.
