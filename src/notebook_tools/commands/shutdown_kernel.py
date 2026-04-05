from notebook_tools.runtime.jupyter import shutdown_session
from notebook_tools.schemas.common import LIVE_SESSION_MODE
from notebook_tools.utils.errors import DomainError


def run(_notebook, request):
    session_id = request.get("kernel_session_id")
    if not session_id:
        raise DomainError(
            "invalid_request",
            "shutdown-kernel requires --session or kernel_session_id.",
        )
    if request.get("confirmation_token") != "confirm":
        raise DomainError(
            "confirmation_required",
            "shutdown-kernel requires confirmation_token='confirm'.",
            details={"required_token": "confirm"},
        )
    session = shutdown_session(session_id)
    return {
        "data": {"kernel_shutdown_status": "stopped"},
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
