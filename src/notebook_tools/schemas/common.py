FILE_ONLY_MODE = "file_only"
LIVE_SESSION_MODE = "live_session"
SCHEMA_VERSION = 1


def response_envelope(
    *,
    command,
    ok,
    request_id=None,
    data=None,
    warnings=None,
    errors=None,
    notebook_ref=None,
    notebook_revision=None,
    truncated=False,
    next_cursor=None,
    mode=FILE_ONLY_MODE,
    kernel_session_id=None,
    observability=None,
):
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": ok,
        "command": command,
        "request_id": request_id,
        "mode": mode,
        "data": data or {},
        "warnings": warnings or [],
        "errors": errors or [],
        "meta": {
            "notebook_ref": notebook_ref,
            "notebook_revision": notebook_revision,
            "kernel_session_id": kernel_session_id,
            "truncated": truncated,
            "next_cursor": next_cursor,
            "observability": observability
            or {
                "source": "observed",
                "runtime": "unavailable",
            },
        },
    }
