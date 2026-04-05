from notebook_tools.runtime.inspect import inspect_dataframe_probe, run_json_probe
from notebook_tools.utils.errors import DomainError


def run(_notebook, request):
    variable_name = request.get("variable_name")
    if not variable_name:
        raise DomainError(
            "invalid_request", "inspect-dataframe requires a variable_name."
        )

    code = inspect_dataframe_probe(
        variable_name,
        int(request.get("max_rows", 5)),
        int(request.get("max_chars", 120)),
    )
    return run_json_probe(request, code)
