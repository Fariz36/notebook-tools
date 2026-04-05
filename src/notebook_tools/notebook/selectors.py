from notebook_tools.notebook.model import cell_ref
from notebook_tools.utils.errors import DomainError


def _single_target_from_index(cells, index):
    if index < 0 or index >= len(cells):
        raise DomainError(
            "cell_not_found",
            f"Cell index out of range: {index}",
            details={"index": index},
        )
    return index, cells[index]


def resolve_selector(notebook, selector):
    cells = notebook["cells"]
    selector = selector or {}
    indexes = set()

    for index in selector.get("indexes", []) or []:
        if index < 0 or index >= len(cells):
            raise DomainError(
                "cell_not_found",
                f"Cell index out of range: {index}",
                details={"index": index},
            )
        indexes.add(index)

    for cell_id in selector.get("cell_ids", []) or []:
        match = next(
            (i for i, cell in enumerate(cells) if cell.get("id") == cell_id), None
        )
        if match is None:
            raise DomainError(
                "cell_not_found",
                f"Cell ID not found: {cell_id}",
                details={"cell_id": cell_id},
            )
        indexes.add(match)

    range_selector = selector.get("range") or {}
    start = range_selector.get("start")
    end = range_selector.get("end")
    if start is not None or end is not None:
        if start is None or end is None:
            raise DomainError(
                "invalid_request", "Range selectors require both start and end."
            )
        if start < 0 or end < start:
            raise DomainError(
                "invalid_request",
                "Invalid cell range.",
                details={"start": start, "end": end},
            )
        for index in range(start, min(end + 1, len(cells))):
            indexes.add(index)

    ordered_indexes = sorted(indexes)
    if not ordered_indexes:
        raise DomainError("selection_empty", "No cells matched the requested selector.")
    return [(index, cells[index]) for index in ordered_indexes]


def resolve_single_target(notebook, *, cell_id=None, index=None):
    cells = notebook["cells"]
    if cell_id is not None:
        for idx, cell in enumerate(cells):
            if cell.get("id") == cell_id:
                return idx, cell
        raise DomainError(
            "cell_not_found",
            f"Cell ID not found: {cell_id}",
            details={"cell_id": cell_id},
        )
    if index is not None:
        return _single_target_from_index(cells, index)
    raise DomainError(
        "invalid_request", "A single target cell_id or index is required."
    )


def ref_details(index, cell):
    return cell_ref(cell, index)
