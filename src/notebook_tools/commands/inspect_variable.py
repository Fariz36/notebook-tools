from notebook_tools.runtime.inspect import inspect_variable_probe, run_json_probe
from notebook_tools.utils.errors import DomainError


def run(_notebook, request):
    variable_name = request.get("variable_name")
    if not variable_name:
        raise DomainError(
            "invalid_request", "inspect-variable requires a variable_name."
        )

    code = inspect_variable_probe(
        variable_name,
        int(request.get("max_chars", 240)),
        int(request.get("max_items", 5)),
    )
    return run_json_probe(request, code)
