import time

from notebook_tools.notebook.model import summarize_output_item
from notebook_tools.utils.errors import DomainError


def _remaining_seconds(deadline):
    return max(deadline - time.time(), 0.01)


def _matching_parent(message, msg_id):
    return message.get("parent_header", {}).get("msg_id") == msg_id


def _read_shell_reply(client, msg_id, deadline):
    while True:
        try:
            message = client.get_shell_msg(timeout=_remaining_seconds(deadline))
        except Exception as exc:
            raise DomainError(
                "execution_timeout",
                "Timed out waiting for shell reply from kernel.",
                retryable=True,
            ) from exc
        if _matching_parent(message, msg_id):
            return message


def execute_code(client, code, *, timeout=30):
    deadline = time.time() + timeout
    msg_id = client.execute(
        code,
        store_history=True,
        allow_stdin=False,
        stop_on_error=True,
    )

    outputs = []
    execution_count = None
    idle_seen = False

    while not idle_seen:
        try:
            message = client.get_iopub_msg(timeout=_remaining_seconds(deadline))
        except Exception as exc:
            raise DomainError(
                "execution_timeout",
                "Timed out waiting for kernel output.",
                retryable=True,
            ) from exc

        if not _matching_parent(message, msg_id):
            continue

        msg_type = message.get("msg_type")
        content = message.get("content", {})

        if msg_type == "status" and content.get("execution_state") == "idle":
            idle_seen = True
            continue

        if msg_type == "execute_input":
            execution_count = content.get("execution_count")
            continue

        if msg_type == "stream":
            outputs.append(
                {
                    "output_type": "stream",
                    "name": content.get("name", "stdout"),
                    "text": content.get("text", ""),
                }
            )
            continue

        if msg_type in {"display_data", "execute_result"}:
            outputs.append(
                {
                    "output_type": msg_type,
                    "data": content.get("data", {}),
                    "metadata": content.get("metadata", {}),
                    "execution_count": content.get("execution_count"),
                }
            )
            continue

        if msg_type == "error":
            outputs.append(
                {
                    "output_type": "error",
                    "ename": content.get("ename"),
                    "evalue": content.get("evalue"),
                    "traceback": content.get("traceback", []),
                }
            )
            continue

        if msg_type == "clear_output":
            outputs = []

    reply = _read_shell_reply(client, msg_id, deadline)
    reply_content = reply.get("content", {})
    status = "error" if reply_content.get("status") == "error" else "completed"
    if execution_count is None:
        execution_count = reply_content.get("execution_count")

    return {
        "status": status,
        "execution_count": execution_count,
        "outputs": outputs,
        "output_summary": [summarize_output_item(output) for output in outputs],
        "error": reply_content.get("ename") or reply_content.get("status")
        if status == "error"
        else None,
    }
