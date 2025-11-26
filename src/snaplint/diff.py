from __future__ import annotations

from snaplint.models import DiffResult, FileDiff, SnapshotEntry, SnapshotFile


def _diff_file_snapshots(
    current_entries: list[SnapshotEntry],
    snapshot_entries: list[SnapshotEntry],
    path: str,
) -> FileDiff:
    """Compare entries for a single file."""
    # Build hash sets for comparison
    current_hashes = {e.sha1 for e in current_entries}
    snapshot_hashes = {e.sha1 for e in snapshot_entries}

    # Build hash -> entry mappings
    current_hash_map = {e.sha1: e for e in current_entries}
    snapshot_hash_map = {e.sha1: e for e in snapshot_entries}

    # Determine added and removed
    added_hashes = current_hashes - snapshot_hashes
    removed_hashes = snapshot_hashes - current_hashes
    unchanged_hashes = current_hashes & snapshot_hashes

    added_entries = tuple(
        current_hash_map[h] for h in sorted(added_hashes, key=lambda h: current_hash_map[h].line)
    )
    removed_entries = tuple(
        snapshot_hash_map[h] for h in sorted(removed_hashes, key=lambda h: snapshot_hash_map[h].line)
    )

    # Check if count changed - true if there are any additions or removals
    count_changed = len(added_entries) > 0 or len(removed_entries) > 0

    # Check if order changed (compare hash sequences for unchanged items)
    current_sequence = [e.sha1 for e in current_entries if e.sha1 in unchanged_hashes]
    snapshot_sequence = [e.sha1 for e in snapshot_entries if e.sha1 in unchanged_hashes]
    order_changed = current_sequence != snapshot_sequence

    return FileDiff(
        path=path,
        count_changed=count_changed,
        order_changed=order_changed,
        added=added_entries,
        removed=removed_entries,
        unchanged_count=len(unchanged_hashes),
    )


def diff_snapshot_files(
    current: SnapshotFile,
    snapshot: SnapshotFile,
) -> DiffResult:
    """Compare two snapshot files and return the diff."""
    # Build file path -> FileSnapshot mappings
    current_files = {fs.path: fs for fs in current.files}
    snapshot_files = {fs.path: fs for fs in snapshot.files}

    all_paths = set(current_files.keys()) | set(snapshot_files.keys())

    file_diffs: list[FileDiff] = []
    total_added = 0
    total_removed = 0
    total_unchanged = 0
    files_with_changes = 0

    for path in sorted(all_paths):
        current_file = current_files.get(path)
        snapshot_file = snapshot_files.get(path)

        if current_file is None:
            # File only in snapshot (all removed)
            file_diff = FileDiff(
                path=path,
                count_changed=True,
                order_changed=False,
                added=tuple(),
                removed=snapshot_file.entries,
                unchanged_count=0,
            )
        elif snapshot_file is None:
            # File only in current (all added)
            file_diff = FileDiff(
                path=path,
                count_changed=True,
                order_changed=False,
                added=current_file.entries,
                removed=tuple(),
                unchanged_count=0,
            )
        else:
            # File in both
            file_diff = _diff_file_snapshots(
                current_entries=list(current_file.entries),
                snapshot_entries=list(snapshot_file.entries),
                path=path,
            )

        # Only include files with changes
        if file_diff.added or file_diff.removed or file_diff.order_changed:
            file_diffs.append(file_diff)
            files_with_changes += 1

        total_added += len(file_diff.added)
        total_removed += len(file_diff.removed)
        total_unchanged += file_diff.unchanged_count

    return DiffResult(
        file_diffs=tuple(file_diffs),
        total_added=total_added,
        total_removed=total_removed,
        total_unchanged=total_unchanged,
        files_with_changes=files_with_changes,
    )
