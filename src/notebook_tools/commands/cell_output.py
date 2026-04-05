from notebook_tools.notebook.model import cell_outputs, cell_ref, summarize_output_item
from notebook_tools.notebook.selectors import resolve_single_target


def run(notebook, request):
    index, cell = resolve_single_target(
        notebook,
        cell_id=request.get("cell_id"),
        index=request.get("index"),
    )
    max_items = int(request.get("max_items", 20))
    max_chars = int(request.get("max_chars", 500))
    outputs = cell_outputs(cell)
    summarized = [
        summarize_output_item(output, max_chars=max_chars)
        for output in outputs[:max_items]
    ]
    traceback = None
    for output in outputs:
        if output.get("output_type") == "error":
            traceback = output.get("traceback", [])[:5]
            break

    truncated = len(outputs) > max_items or any(
        item.get("truncated") for item in summarized
    )
    return (
        {
            "cell_ref": cell_ref(cell, index),
            "output_count": len(outputs),
            "output_types": [
                output.get("output_type", "unknown") for output in outputs
            ],
            "outputs": summarized,
            "traceback": traceback,
            "artifact_references": [],
        },
        truncated,
        None,
    )
