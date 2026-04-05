from notebook_tools.notebook.model import (
    cell_outputs,
    cell_snapshot,
    cell_source,
    present_source,
    summarize_output_item,
)
from notebook_tools.notebook.selectors import resolve_selector


def run(notebook, request):
    selector = request.get("cell_selector")
    selected = resolve_selector(notebook, selector)
    summary_mode = request.get("summary_mode", "compact")
    max_chars = int(request.get("max_chars", 4000))
    include_outputs = bool(request.get("include_outputs", False))

    cells = []
    truncated = False
    for index, cell in selected:
        payload = cell_snapshot(cell, index)
        payload.update(
            present_source(
                cell_source(cell),
                cell_type=cell.get("cell_type"),
                summary_mode=summary_mode,
                max_chars=max_chars,
            )
        )
        if payload.get("source_truncated"):
            truncated = True
        if include_outputs:
            outputs = [summarize_output_item(output) for output in cell_outputs(cell)]
            payload["outputs"] = outputs
            if any(output.get("truncated") for output in outputs):
                truncated = True
        cells.append(payload)

    return {"cells": cells}, truncated, None
