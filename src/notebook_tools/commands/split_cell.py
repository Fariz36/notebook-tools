from notebook_tools.notebook.mutations import split_cell
from notebook_tools.notebook.selectors import resolve_single_target


def run(notebook, request):
    index, _cell = resolve_single_target(
        notebook,
        cell_id=request.get("cell_id"),
        index=request.get("index"),
    )
    return (
        split_cell(
            notebook,
            index=index,
            split_points=[int(point) for point in request.get("split_points", [])],
        ),
        False,
        None,
    )
