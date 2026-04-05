from notebook_tools.notebook.dependencies import build_dependency_report
from notebook_tools.notebook.selectors import resolve_selector


def run(notebook, request):
    selected = resolve_selector(notebook, request.get("cell_selector"))
    selected_indexes = [index for index, _cell in selected]
    mode = request.get("mode", "full")
    return build_dependency_report(notebook, selected_indexes, mode=mode), False, None
