from notebook_tools.notebook.selectors import resolve_selector
from notebook_tools.runtime.execute import execute_code
from notebook_tools.runtime.jupyter import connect_client, resolve_session
from notebook_tools.schemas.common import LIVE_SESSION_MODE


def _selector_for_request(notebook, request):
    if request.get("run_all"):
        return [(index, cell) for index, cell in enumerate(notebook["cells"])]
    return resolve_selector(notebook, request.get("cell_selector"))


def run(notebook, request):
    timeout = int(request.get("timeout", 30))
    startup_timeout = int(request.get("startup_timeout", timeout))
    selected = _selector_for_request(notebook, request)
    session, created = resolve_session(
        request["notebook_ref"],
        session_id=request.get("kernel_session_id"),
        auto_start=True,
        startup_timeout=startup_timeout,
    )

    warnings = []
    if created:
        warnings.append("Started a new kernel session for this notebook.")

    client = connect_client(session, startup_timeout=startup_timeout)
    execution_cells = []
    try:
        for index, cell in selected:
            if cell.get("cell_type") != "code":
                execution_cells.append(
                    {
                        "cell_ref": {
                            "index": index,
                            **({"cell_id": cell["id"]} if cell.get("id") else {}),
                        },
                        "status": "skipped",
                        "reason": "non_code_cell",
                        "execution_count": cell.get("execution_count"),
                        "output_summary": [],
                        "error": None,
                    }
                )
                continue

            result = execute_code(client, cell.get("source", ""), timeout=timeout)
            cell["outputs"] = result["outputs"]
            cell["execution_count"] = result["execution_count"]
            execution_cells.append(
                {
                    "cell_ref": {
                        "index": index,
                        **({"cell_id": cell["id"]} if cell.get("id") else {}),
                    },
                    "status": result["status"],
                    "execution_count": result["execution_count"],
                    "output_summary": result["output_summary"],
                    "error": result["error"],
                }
            )
            if result["status"] == "error":
                break
    finally:
        client.stop_channels()

    overall_status = "completed"
    if any(item["status"] == "error" for item in execution_cells):
        overall_status = "error"

    return {
        "data": {
            "execution": {
                "status": overall_status,
                "cells": execution_cells,
                "stale_state_warning": False,
            }
        },
        "truncated": False,
        "next_cursor": None,
        "warnings": warnings,
        "mode": LIVE_SESSION_MODE,
        "kernel_session_id": session["session_id"],
        "observability": {
            "source": "observed",
            "runtime": "observed",
        },
    }
