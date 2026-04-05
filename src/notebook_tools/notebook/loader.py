import json
from pathlib import Path

from notebook_tools.notebook.revisions import stable_hash
from notebook_tools.utils.errors import DomainError


def load_notebook(notebook_ref):
    path = Path(notebook_ref)
    if not path.exists():
        raise DomainError("notebook_not_found", f"Notebook not found: {notebook_ref}")

    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DomainError(
            "invalid_request", f"Notebook is not valid JSON: {exc}"
        ) from exc

    if not isinstance(notebook, dict) or not isinstance(notebook.get("cells"), list):
        raise DomainError(
            "invalid_request", "Notebook JSON must contain a top-level 'cells' list."
        )

    return path, notebook, stable_hash(notebook)


def save_notebook(path, notebook):
    text = json.dumps(notebook, indent=1, ensure_ascii=True)
    path.write_text(f"{text}\n", encoding="utf-8")
