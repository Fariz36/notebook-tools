from notebook_tools.runtime.inspect import list_variables_probe, run_json_probe


def run(_notebook, request):
    code = list_variables_probe(
        int(request.get("max_items", 50)),
        int(request.get("max_chars", 120)),
    )
    return run_json_probe(request, code)
