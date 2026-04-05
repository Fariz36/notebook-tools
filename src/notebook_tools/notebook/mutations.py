import uuid

from notebook_tools.notebook.model import cell_ref, cell_snapshot, cell_source
from notebook_tools.notebook.revisions import source_revision
from notebook_tools.utils.errors import DomainError


def ensure_cell_revision(cell, expected_revision):
    if expected_revision is None:
        return
    actual_revision = source_revision(cell_source(cell))
    if actual_revision != expected_revision:
        raise DomainError(
            "cell_revision_conflict",
            "Cell source changed since it was last read.",
            retryable=True,
            details={
                "cell_ref": {"cell_id": cell.get("id")},
                "expected_revision": expected_revision,
                "actual_revision": actual_revision,
            },
        )


def apply_edit(cell, *, edit_mode, new_content):
    current = cell_source(cell)
    if edit_mode == "replace":
        updated = new_content
    elif edit_mode == "append":
        updated = f"{current}{new_content}"
    elif edit_mode == "prepend":
        updated = f"{new_content}{current}"
    else:
        raise DomainError("invalid_request", f"Unsupported edit mode: {edit_mode}")

    cell["source"] = updated
    return current, updated


def minimal_diff_summary(before, after):
    if before == after:
        return "No source change."
    before_len = len(before)
    after_len = len(after)
    if after.startswith(before):
        return f"Appended {after_len - before_len} characters."
    if before.endswith(after):
        return f"Removed {before_len - after_len} trailing characters."
    if after.endswith(before):
        return f"Prepended {after_len - before_len} characters."
    return f"Replaced cell source ({before_len} chars -> {after_len} chars)."


def make_new_cell(*, cell_type, content):
    cell_id = uuid.uuid4().hex[:8]
    cell = {
        "id": cell_id,
        "cell_type": cell_type,
        "metadata": {},
        "source": content,
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    elif cell_type not in {"markdown", "raw"}:
        raise DomainError("invalid_request", f"Unsupported cell type: {cell_type}")
    return cell


def insert_cell(notebook, *, position, cell_type, content):
    cells = notebook["cells"]
    if position < 0 or position > len(cells):
        raise DomainError(
            "invalid_request",
            "Insert position out of range.",
            details={"position": position},
        )
    cell = make_new_cell(cell_type=cell_type, content=content)
    cells.insert(position, cell)
    return cell_ref(cell, position), [
        cell_snapshot(item, index) for index, item in enumerate(cells)
    ]


def _ordering_snapshot(cells):
    return [cell_snapshot(item, index) for index, item in enumerate(cells)]


def delete_cell(notebook, *, index, confirmation_token):
    if confirmation_token != "confirm":
        raise DomainError(
            "confirmation_required",
            "delete-cell requires confirmation_token='confirm'.",
            details={"required_token": "confirm"},
        )

    cells = notebook["cells"]
    if index < 0 or index >= len(cells):
        raise DomainError("cell_not_found", f"Cell index out of range: {index}")

    removed = cells.pop(index)
    return cell_ref(removed, index), _ordering_snapshot(cells)


def move_cell(notebook, *, index, position):
    cells = notebook["cells"]
    if index < 0 or index >= len(cells):
        raise DomainError("cell_not_found", f"Cell index out of range: {index}")
    if position < 0 or position >= len(cells):
        raise DomainError(
            "invalid_request",
            "Target position out of range.",
            details={"position": position},
        )

    cell = cells.pop(index)
    cells.insert(position, cell)
    return cell_ref(cell, position), _ordering_snapshot(cells)


def _split_source_into_parts(source, split_points):
    lines = source.splitlines(keepends=True)
    if not lines:
        raise DomainError("invalid_request", "Cannot split an empty cell.")

    normalized = sorted(set(split_points))
    if not normalized:
        raise DomainError(
            "invalid_request", "split-cell requires at least one split point."
        )
    for point in normalized:
        if point <= 0 or point >= len(lines):
            raise DomainError(
                "invalid_request",
                "Split points must create non-empty parts.",
                details={"split_point": point, "line_count": len(lines)},
            )

    parts = []
    start = 0
    for point in normalized:
        parts.append("".join(lines[start:point]))
        start = point
    parts.append("".join(lines[start:]))
    return parts


def split_cell(notebook, *, index, split_points):
    cells = notebook["cells"]
    if index < 0 or index >= len(cells):
        raise DomainError("cell_not_found", f"Cell index out of range: {index}")

    cell = cells[index]
    parts = _split_source_into_parts(cell_source(cell), split_points)
    cell["source"] = parts[0]

    created_refs = []
    if cell.get("cell_type") == "code":
        cell["execution_count"] = None
        cell["outputs"] = []

    insert_at = index + 1
    for part in parts[1:]:
        new_cell = make_new_cell(cell_type=cell.get("cell_type", "code"), content=part)
        cells.insert(insert_at, new_cell)
        created_refs.append(cell_ref(new_cell, insert_at))
        insert_at += 1

    return {
        "updated_cell_ref": cell_ref(cell, index),
        "created_cell_refs": created_refs,
        "cells": _ordering_snapshot(cells),
    }


def _merge_sources(parts):
    merged = ""
    for part in parts:
        if not merged:
            merged = part
            continue
        if merged.endswith("\n") or not part:
            merged += part
        else:
            merged += f"\n{part}"
    return merged


def merge_cells(notebook, *, indexes):
    ordered_indexes = sorted(set(indexes))
    if len(ordered_indexes) < 2:
        raise DomainError(
            "invalid_request", "merge-cells requires at least two target cells."
        )

    cells = notebook["cells"]
    for index in ordered_indexes:
        if index < 0 or index >= len(cells):
            raise DomainError("cell_not_found", f"Cell index out of range: {index}")

    for prev_index, next_index in zip(ordered_indexes, ordered_indexes[1:]):
        if next_index != prev_index + 1:
            raise DomainError(
                "invalid_request",
                "merge-cells requires adjacent cells.",
                details={"indexes": ordered_indexes},
            )

    target_cells = [cells[index] for index in ordered_indexes]
    cell_types = {cell.get("cell_type") for cell in target_cells}
    if len(cell_types) != 1:
        raise DomainError(
            "invalid_request",
            "merge-cells requires all cells to have the same type.",
            details={"indexes": ordered_indexes},
        )

    primary = target_cells[0]
    primary["source"] = _merge_sources([cell_source(cell) for cell in target_cells])
    if primary.get("cell_type") == "code":
        primary["execution_count"] = None
        primary["outputs"] = []

    for index in reversed(ordered_indexes[1:]):
        cells.pop(index)

    return {
        "merged_cell_ref": cell_ref(primary, ordered_indexes[0]),
        "merged_from_indexes": ordered_indexes,
        "cells": _ordering_snapshot(cells),
    }
