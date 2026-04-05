from notebook_tools.runtime.jupyter import interrupt_session
from notebook_tools.schemas.common import LIVE_SESSION_MODE
from notebook_tools.utils.errors import DomainError


def run(_notebook, request):
    session_id = request.get("kernel_session_id")
    if not session_id:
        raise DomainError(
            "invalid_request", "interrupt requires --session or kernel_session_id."
        )
    session = interrupt_session(session_id)
    return {
        "data": {"interrupt_status": "sent"},
        "warnings": [],
        "truncated": False,
        "next_cursor": None,
        "mode": LIVE_SESSION_MODE,
        "kernel_session_id": session["session_id"],
        "observability": {
            "source": "observed",
            "runtime": "observed",
        },
    }
