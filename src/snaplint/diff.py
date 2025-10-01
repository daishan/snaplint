from __future__ import annotations

import subprocess

from snaplint.models import DiffResult, IssueKey, IssueSet


def _get_sort_key(k: IssueKey) -> tuple[str, int, int, str, str]:
    return k.path, k.line, k.column, k.code or "", k.message or ""


def diff_issue_sets(
    current: IssueSet,
    snapshot: IssueSet,
    ref: str | None = None,
) -> DiffResult:
    """Compare two issue sets and return the diff."""
    added_keys = set(current.items - snapshot.items)
    removed_keys = set(snapshot.items - current.items)
    moved_keys: list[tuple[IssueKey, IssueKey]] = []

    if ref:
        # Create a map of removed issues indexed by (path, code, message)
        removed_map: dict[tuple[str, str | None, str | None], list[IssueKey]] = {}
        for key in removed_keys:
            lookup_key = (key.path, key.code, key.message)
            if lookup_key not in removed_map:
                removed_map[lookup_key] = []
            removed_map[lookup_key].append(key)

        still_added = set()
        for added_key in added_keys:
            lookup_key = (added_key.path, added_key.code, added_key.message)
            if potential_matches := removed_map.get(lookup_key):
                # Since the linter output is sorted, we can assume the first
                # match is the correct one.
                best_match = potential_matches[0]

                try:
                    # Get the content of the file from the ref
                    snapshot_file_content = subprocess.check_output(
                        ["git", "show", f"{ref}:{best_match.path}"], text=True
                    )
                    snapshot_lines = snapshot_file_content.splitlines()
                    original_line_content = snapshot_lines[best_match.line - 1].strip()

                    # Get the content of the file from the current directory
                    with open(added_key.path) as f:
                        current_lines = f.readlines()
                    current_line_content = current_lines[added_key.line - 1].strip()

                    if original_line_content == current_line_content:
                        moved_keys.append((best_match, added_key))
                        removed_keys.remove(best_match)
                        potential_matches.pop(0)
                        continue

                except (
                    subprocess.CalledProcessError,
                    FileNotFoundError,
                    IndexError,
                ):
                    # If git show fails, or the file doesn't exist, or the line
                    # doesn't exist, we can't determine if the error moved.
                    pass

            still_added.add(added_key)
        added_keys = still_added

    # Sort keys for stable output
    sorted_added = tuple(sorted(added_keys, key=_get_sort_key))
    sorted_removed = tuple(sorted(removed_keys, key=_get_sort_key))
    sorted_moved = tuple(sorted(moved_keys, key=lambda pair: _get_sort_key(pair[1])))

    return DiffResult(
        added=sorted_added,
        removed=sorted_removed,
        moved=sorted_moved,
        unchanged_count=len(current.items & snapshot.items),
    )
