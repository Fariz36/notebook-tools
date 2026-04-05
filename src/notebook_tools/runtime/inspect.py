import json
import textwrap

from notebook_tools.runtime.execute import execute_code
from notebook_tools.runtime.jupyter import connect_client, resolve_session
from notebook_tools.schemas.common import LIVE_SESSION_MODE
from notebook_tools.utils.errors import DomainError


def _extract_json_stream(outputs):
    text_parts = []
    for output in outputs:
        if output.get("output_type") != "stream":
            continue
        text = output.get("text", "")
        if text:
            text_parts.append(text)

    text = "".join(text_parts).strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise DomainError(
            "execution_failed",
            "Kernel inspection probe returned invalid JSON.",
            retryable=True,
            details={"raw_output": text[:500]},
        ) from exc


def _connect_for_request(request):
    session, created = resolve_session(
        request.get("notebook_ref"),
        session_id=request.get("kernel_session_id"),
        auto_start=bool(request.get("start_if_missing", False)),
        startup_timeout=int(request.get("startup_timeout", 30)),
    )
    warnings = []
    if created:
        warnings.append("Started a new kernel session for this notebook.")
    client = connect_client(
        session, startup_timeout=int(request.get("startup_timeout", 30))
    )
    return session, client, warnings


def _success_payload(data, *, warnings, session):
    if isinstance(data, dict):
        data = dict(data)
        data.pop("ok", None)
    return {
        "data": data,
        "warnings": warnings,
        "truncated": False,
        "next_cursor": None,
        "mode": LIVE_SESSION_MODE,
        "kernel_session_id": session["session_id"],
        "observability": {
            "source": "observed",
            "runtime": "observed",
        },
    }


def _raise_probe_error(payload):
    code = payload.get("error_code", "execution_failed")
    message = payload.get("message", "Kernel inspection probe failed.")
    raise DomainError(code, message, details=payload.get("details", {}))


def run_json_probe(request, code):
    session, client, warnings = _connect_for_request(request)
    try:
        result = execute_code(client, code, timeout=int(request.get("timeout", 30)))
    finally:
        client.stop_channels()

    if result["status"] == "error":
        raise DomainError(
            "execution_failed",
            "Kernel execution failed while inspecting runtime state.",
            details={
                "error": result.get("error"),
                "outputs": result.get("output_summary"),
            },
        )

    payload = _extract_json_stream(result["outputs"])
    if payload.get("ok") is False:
        _raise_probe_error(payload)
    return _success_payload(payload, warnings=warnings, session=session)


def list_variables_probe(max_items, max_chars):
    return textwrap.dedent(
        f"""
        def _nt_probe():
            def _nt_type_name(obj):
                obj_type = type(obj)
                return f"{{obj_type.__module__}}.{{obj_type.__qualname__}}"

            def _nt_shape_or_size(obj):
                try:
                    shape = getattr(obj, 'shape', None)
                    if shape is not None:
                        return list(shape)
                except Exception:
                    pass
                try:
                    return len(obj)
                except Exception:
                    return None

            def _nt_preview(obj, limit):
                try:
                    text = repr(obj)
                except Exception as exc:
                    text = f"<repr failed: {{exc}}>"
                if len(text) > limit:
                    return text[:limit - 3] + '...'
                return text

            variables = []
            for name, obj in sorted(globals().items()):
                if name.startswith('_'):
                    continue
                variables.append({{
                    'name': name,
                    'type': _nt_type_name(obj),
                    'shape_or_size': _nt_shape_or_size(obj),
                    'preview': _nt_preview(obj, {max_chars}),
                    'origin_cell_ref': None,
                }})
            return {{'ok': True, 'variables': variables[:{max_items}]}}

        print(__import__('json').dumps(_nt_probe()))
        del _nt_probe
        """
    )


def inspect_variable_probe(variable_name, max_chars, max_items):
    return textwrap.dedent(
        f"""
        def _nt_probe():
            def _nt_type_name(obj):
                obj_type = type(obj)
                return f"{{obj_type.__module__}}.{{obj_type.__qualname__}}"

            def _nt_shape_or_size(obj):
                try:
                    shape = getattr(obj, 'shape', None)
                    if shape is not None:
                        return list(shape)
                except Exception:
                    pass
                try:
                    return len(obj)
                except Exception:
                    return None

            def _nt_preview(obj, limit):
                try:
                    text = repr(obj)
                except Exception as exc:
                    text = f"<repr failed: {{exc}}>"
                if len(text) > limit:
                    return text[:limit - 3] + '...'
                return text

            def _nt_sample(obj, limit, chars):
                if isinstance(obj, dict):
                    items = []
                    for index, (key, value) in enumerate(obj.items()):
                        if index >= limit:
                            break
                        items.append({{'key': _nt_preview(key, chars), 'value': _nt_preview(value, chars)}})
                    return {{'kind': 'dict_items', 'items': items}}
                if isinstance(obj, (list, tuple, set)):
                    values = []
                    for index, value in enumerate(obj):
                        if index >= limit:
                            break
                        values.append(_nt_preview(value, chars))
                    return {{'kind': type(obj).__name__, 'items': values}}
                return None

            name = {variable_name!r}
            if name not in globals():
                return {{'ok': False, 'error_code': 'variable_not_found', 'message': f"Variable not found: {{name}}", 'details': {{'variable_name': name}}}}

            obj = globals()[name]
            return {{
                'ok': True,
                'name': name,
                'type': _nt_type_name(obj),
                'shape_or_size': _nt_shape_or_size(obj),
                'preview': _nt_preview(obj, {max_chars}),
                'sample': _nt_sample(obj, {max_items}, {max_chars}),
                'is_callable': callable(obj),
                'has_len': hasattr(obj, '__len__'),
                'module': type(obj).__module__,
            }}

        print(__import__('json').dumps(_nt_probe()))
        del _nt_probe
        """
    )


def inspect_dataframe_probe(variable_name, max_rows, max_chars):
    return textwrap.dedent(
        f"""
        def _nt_probe():
            def _nt_clean(value):
                try:
                    if hasattr(value, 'item'):
                        value = value.item()
                except Exception:
                    pass
                if isinstance(value, float):
                    if value != value:
                        return None
                    if value == float('inf') or value == float('-inf'):
                        return str(value)
                if isinstance(value, (str, int, float, bool)) or value is None:
                    return value
                text = repr(value)
                if len(text) > {max_chars}:
                    return text[:{max_chars} - 3] + '...'
                return text

            name = {variable_name!r}
            if name not in globals():
                return {{'ok': False, 'error_code': 'variable_not_found', 'message': f"Variable not found: {{name}}", 'details': {{'variable_name': name}}}}

            obj = globals()[name]
            try:
                import pandas as pd
            except ModuleNotFoundError:
                return {{'ok': False, 'error_code': 'pandas_unavailable', 'message': 'inspect-dataframe requires pandas in the kernel environment.'}}

            if not isinstance(obj, pd.DataFrame):
                return {{'ok': False, 'error_code': 'not_a_dataframe', 'message': f"Variable '{{name}}' is not a pandas DataFrame.", 'details': {{'variable_name': name, 'actual_type': f"{{type(obj).__module__}}.{{type(obj).__qualname__}}"}}}}

            sample_rows = []
            for record in obj.head({max_rows}).to_dict(orient='records'):
                sample_rows.append({{str(key): _nt_clean(value) for key, value in record.items()}})

            null_counts = {{str(key): int(value) for key, value in obj.isnull().sum().to_dict().items()}}
            dtypes = {{str(key): str(value) for key, value in obj.dtypes.to_dict().items()}}
            memory_bytes = int(obj.memory_usage(deep=True).sum())
            numeric_summary = None
            numeric = obj.select_dtypes(include='number')
            if not numeric.empty:
                numeric_summary = {{}}
                for column, stats in numeric.describe().to_dict().items():
                    numeric_summary[str(column)] = {{str(key): _nt_clean(value) for key, value in stats.items()}}

            return {{
                'ok': True,
                'name': name,
                'shape': [int(obj.shape[0]), int(obj.shape[1])],
                'columns': [str(column) for column in obj.columns.tolist()],
                'dtypes': dtypes,
                'null_counts': null_counts,
                'sample_rows': sample_rows,
                'memory_bytes': memory_bytes,
                'numeric_summary': numeric_summary,
            }}

        print(__import__('json').dumps(_nt_probe()))
        del _nt_probe
        """
    )
