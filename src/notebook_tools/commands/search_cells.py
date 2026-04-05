from notebook_tools.notebook.search import search_cells


def run(notebook, request):
    query = request.get("query")
    if not query:
        raise ValueError("query is required")

    max_items = int(request.get("max_items", 20))
    matches = search_cells(
        notebook,
        query=query,
        cell_filter=request.get("filter"),
        max_items=max_items,
    )
    return {"matches": matches}, False, None
