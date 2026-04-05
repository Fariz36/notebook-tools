from notebook_tools.notebook.mutations import merge_cells
from notebook_tools.notebook.selectors import resolve_selector


def run(notebook, request):
    selected = resolve_selector(notebook, request.get("cell_selector"))
    indexes = [index for index, _cell in selected]
    return merge_cells(notebook, indexes=indexes), False, None
