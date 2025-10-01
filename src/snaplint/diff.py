from __future__ import annotations

import difflib

from snaplint.models import DiffResult, IssueSet


def _get_sort_key(k):
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
                # Find the best match (closest line number)
                best_match = min(
                    potential_matches,
                    key=lambda removed_key: abs(added_key.line - removed_key.line),
                )

                original_line = snapshot.index[best_match].original
                current_line = current.index[added_key].original

                # Use difflib to compare the lines, ignoring the line numbers
                original_parts = original_line.split(":", 2)
                current_parts = current_line.split(":", 2)

                if len(original_parts) == 3 and len(current_parts) == 3:
                    if original_parts[0] == current_parts[0] and original_parts[2] == current_parts[2]:
                        moved_keys.append((best_match, added_key))
                        removed_keys.remove(best_match)
                        potential_matches.remove(best_match)
                        continue

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
