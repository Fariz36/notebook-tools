from notebook_tools.notebook.summarize import summarize_notebook


def run(notebook, request):
    max_output_items = int(request.get("max_items", 5))
    return summarize_notebook(notebook, max_output_items=max_output_items), False, None
