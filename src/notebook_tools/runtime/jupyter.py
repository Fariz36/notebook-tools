import json
import os
import signal
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from notebook_tools.utils.errors import DomainError


PROCESS_REGISTRY = {}


def require_jupyter_client():
    try:
        from jupyter_client import BlockingKernelClient
    except ModuleNotFoundError as exc:
        raise DomainError(
            "kernel_unavailable",
            "Live kernel support requires jupyter_client and ipykernel to be installed.",
            details={"missing_dependency": exc.name},
        ) from exc
    return BlockingKernelClient


def require_ipykernel():
    try:
        import ipykernel  # noqa: F401
    except ModuleNotFoundError as exc:
        raise DomainError(
            "kernel_unavailable",
            "Live kernel support requires ipykernel to be installed.",
            details={"missing_dependency": exc.name},
        ) from exc


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def runtime_root():
    configured_root = os.environ.get("NOTEBOOK_TOOLS_RUNTIME_DIR")
    if configured_root:
        root = Path(configured_root).expanduser().resolve()
    else:
        state_home = os.environ.get("XDG_STATE_HOME")
        if state_home:
            root = Path(state_home).expanduser().resolve() / "notebook-tools"
        else:
            root = Path.home() / ".local" / "state" / "notebook-tools"
    root.mkdir(parents=True, exist_ok=True)
    (root / "sessions").mkdir(exist_ok=True)
    (root / "connections").mkdir(exist_ok=True)
    return root


def session_file(session_id):
    return runtime_root() / "sessions" / f"{session_id}.json"


def connection_file(session_id):
    return runtime_root() / "connections" / f"{session_id}.json"


def _pick_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _connection_config():
    return {
        "ip": "127.0.0.1",
        "transport": "tcp",
        "shell_port": _pick_port(),
        "iopub_port": _pick_port(),
        "stdin_port": _pick_port(),
        "control_port": _pick_port(),
        "hb_port": _pick_port(),
        "signature_scheme": "hmac-sha256",
        "key": uuid.uuid4().hex,
    }


def _write_json(path, payload):
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def load_session(session_id):
    path = session_file(session_id)
    if not path.exists():
        raise DomainError(
            "kernel_unavailable",
            f"Kernel session not found: {session_id}",
            details={"kernel_session_id": session_id},
        )
    session = _read_json(path)
    if not is_pid_alive(session.get("pid")):
        raise DomainError(
            "kernel_session_stale",
            f"Kernel session is no longer alive: {session_id}",
            retryable=True,
            details={"kernel_session_id": session_id, "pid": session.get("pid")},
        )
    return session


def save_session(session):
    session["last_used_at"] = utc_now()
    _write_json(session_file(session["session_id"]), session)


def latest_session_for_notebook(notebook_ref):
    target = str(Path(notebook_ref).resolve())
    session_dir = runtime_root() / "sessions"
    candidates = []
    for path in session_dir.glob("*.json"):
        try:
            session = _read_json(path)
        except json.JSONDecodeError:
            continue
        if session.get("notebook_ref") != target:
            continue
        if not is_pid_alive(session.get("pid")):
            continue
        candidates.append(session)
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.get("last_used_at", ""), reverse=True)
    return candidates[0]


def connect_client(session, *, startup_timeout=30):
    BlockingKernelClient = require_jupyter_client()
    client = BlockingKernelClient(connection_file=session["connection_file"])
    client.load_connection_file()
    client.start_channels()
    try:
        client.wait_for_ready(timeout=startup_timeout)
    except Exception as exc:
        client.stop_channels()
        raise DomainError(
            "kernel_unavailable",
            f"Kernel did not become ready for session {session['session_id']}.",
            retryable=True,
        ) from exc
    return client


def _terminate_pid(pid, *, sig=signal.SIGTERM, wait_seconds=5):
    if not is_pid_alive(pid):
        return
    os.kill(pid, sig)
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if not is_pid_alive(pid):
            return
        time.sleep(0.1)
    if sig != signal.SIGKILL and is_pid_alive(pid):
        _terminate_pid(pid, sig=signal.SIGKILL, wait_seconds=1)


def _reap_registered_process(session_id):
    process = PROCESS_REGISTRY.pop(session_id, None)
    if process is None:
        return
    try:
        process.wait(timeout=1)
    except Exception:
        pass


def start_session(notebook_ref, *, session_id=None, startup_timeout=30):
    require_jupyter_client()
    require_ipykernel()
    notebook_path = Path(notebook_ref).resolve()
    session_id = session_id or uuid.uuid4().hex[:12]
    connection_path = connection_file(session_id)
    _write_json(connection_path, _connection_config())

    process = subprocess.Popen(
        [sys.executable, "-m", "ipykernel_launcher", "-f", str(connection_path)],
        cwd=str(notebook_path.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    PROCESS_REGISTRY[session_id] = process

    session = {
        "session_id": session_id,
        "notebook_ref": str(notebook_path),
        "connection_file": str(connection_path),
        "pid": process.pid,
        "cwd": str(notebook_path.parent),
        "started_at": utc_now(),
        "last_used_at": utc_now(),
        "kernel_name": "python3",
    }
    save_session(session)

    try:
        client = connect_client(session, startup_timeout=startup_timeout)
    except Exception:
        _terminate_pid(process.pid)
        _reap_registered_process(session_id)
        raise
    else:
        client.stop_channels()
    return session


def resolve_session(
    notebook_ref, *, session_id=None, auto_start=False, startup_timeout=30
):
    if session_id:
        session = load_session(session_id)
        save_session(session)
        return session, False

    if notebook_ref is None:
        raise DomainError(
            "kernel_unavailable",
            "A notebook_ref is required when no kernel session is provided.",
            retryable=True,
        )

    session = latest_session_for_notebook(notebook_ref)
    if session:
        save_session(session)
        return session, False

    if auto_start:
        return start_session(notebook_ref, startup_timeout=startup_timeout), True

    raise DomainError(
        "kernel_unavailable",
        "No active kernel session found for this notebook.",
        retryable=True,
        details={"notebook_ref": str(Path(notebook_ref).resolve())},
    )


def interrupt_session(session_id):
    session = load_session(session_id)
    os.kill(session["pid"], signal.SIGINT)
    save_session(session)
    return session


def restart_session(session_id, *, startup_timeout=30):
    old_session = load_session(session_id)
    _terminate_pid(old_session["pid"])
    _reap_registered_process(session_id)
    return start_session(
        old_session["notebook_ref"],
        session_id=session_id,
        startup_timeout=startup_timeout,
    )


def shutdown_session(session_id):
    session = load_session(session_id)
    _terminate_pid(session["pid"])
    _reap_registered_process(session_id)

    session_path = session_file(session_id)
    connection_path = connection_file(session_id)
    if session_path.exists():
        session_path.unlink()
    if connection_path.exists():
        connection_path.unlink()

    return session
