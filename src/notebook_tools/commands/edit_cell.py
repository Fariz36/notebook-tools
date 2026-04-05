from notebook_tools.notebook.model import cell_snapshot, cell_source
from notebook_tools.notebook.mutations import (
    apply_edit,
    ensure_cell_revision,
    minimal_diff_summary,
)
from notebook_tools.notebook.selectors import resolve_single_target


def run(notebook, request):
    index, cell = resolve_single_target(
        notebook,
        cell_id=request.get("cell_id"),
        index=request.get("index"),
    )
    ensure_cell_revision(cell, request.get("cell_source_revision"))
    before, after = apply_edit(
        cell,
        edit_mode=request.get("edit_mode", "replace"),
        new_content=request.get("new_content", ""),
    )
    payload = cell_snapshot(cell, index)
    payload["source"] = cell_source(cell)
    return (
        {
            "updated_cell": payload,
            "diff_summary": minimal_diff_summary(before, after),
        },
        False,
        None,
    )
