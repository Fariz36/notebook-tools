import re

from notebook_tools.notebook.revisions import output_revision, source_revision


def cell_ref(cell, index):
    ref = {"index": index}
    if cell.get("id"):
        ref["cell_id"] = cell["id"]
    return ref


def cell_source(cell):
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return source


def cell_outputs(cell):
    return cell.get("outputs", []) if cell.get("cell_type") == "code" else []


def cell_status(cell):
    if cell.get("cell_type") != "code":
        return "idle"
    if any(output.get("output_type") == "error" for output in cell_outputs(cell)):
        return "error"
    if cell.get("execution_count") is not None or cell_outputs(cell):
        return "completed"
    return "idle"


def dirty_output(cell):
    outputs = cell_outputs(cell)
    execution_count = cell.get("execution_count")
    if cell.get("cell_type") != "code":
        return False
    if execution_count is None and outputs:
        return True
    return False


def first_non_empty_line(text):
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def infer_section_label(cell):
    text = cell_source(cell).lower()
    if cell.get("cell_type") == "markdown":
        if any(word in text for word in ("load", "dataset", "data source")):
            return "data_loading"
        if any(word in text for word in ("clean", "preprocess", "wrangle")):
            return "cleaning"
        if any(word in text for word in ("train", "model", "baseline")):
            return "modeling"
        if any(word in text for word in ("plot", "chart", "visual")):
            return "visualization"
        if any(word in text for word in ("result", "conclusion", "summary")):
            return "conclusion"
    else:
        if re.search(r"read_(csv|parquet|json)|load_", text):
            return "data_loading"
        if re.search(r"dropna|fillna|astype|merge|groupby", text):
            return "cleaning"
        if re.search(r"fit\(|predict\(|score\(|xgboost|sklearn|model", text):
            return "modeling"
        if re.search(r"plot\(|scatter\(|hist\(|bar\(|imshow\(", text):
            return "visualization"
    return None


def summarize_code(text):
    stripped = text.strip()
    if not stripped:
        return "Empty code cell."

    if re.search(r"^import\s+|^from\s+", stripped, flags=re.MULTILINE):
        return "Imports modules or symbols."
    if re.search(r"read_(csv|parquet|json)|open\(", stripped):
        return "Loads data from a file or external source."
    if re.search(r"plot\(|scatter\(|hist\(|bar\(|imshow\(", stripped):
        return "Builds a visualization."
    if re.search(r"fit\(|predict\(|score\(|cross_val", stripped):
        return "Trains or evaluates a model."
    if re.search(r"groupby|agg\(|merge\(|join\(", stripped):
        return "Transforms or aggregates tabular data."
    if re.search(r"^[A-Za-z_][A-Za-z0-9_]*\s*=", stripped, flags=re.MULTILINE):
        return "Defines variables or intermediate results."

    first_line = first_non_empty_line(stripped)
    if len(first_line) > 96:
        first_line = f"{first_line[:93]}..."
    return f"Runs code starting with: {first_line}"


def summarize_markdown(text):
    first_line = first_non_empty_line(text).lstrip("# ")
    if not first_line:
        return "Empty markdown cell."
    if len(first_line) > 96:
        first_line = f"{first_line[:93]}..."
    return first_line


def summarize_cell(cell):
    text = cell_source(cell)
    if cell.get("cell_type") == "markdown":
        return summarize_markdown(text)
    if cell.get("cell_type") == "raw":
        return "Raw cell."
    return summarize_code(text)


def present_source(text, *, cell_type=None, summary_mode="compact", max_chars=4000):
    summary = (
        summarize_markdown(text) if cell_type == "markdown" else summarize_code(text)
    )
    payload = {
        "source_summary": summary,
        "source_length": len(text),
        "source_truncated": False,
    }

    if summary_mode == "compact":
        excerpt = text[: min(max_chars, 500)]
        payload["source_excerpt"] = excerpt
        payload["source_truncated"] = len(text) > len(excerpt)
        return payload

    excerpt = text[:max_chars]
    payload["source"] = excerpt
    payload["source_truncated"] = len(text) > len(excerpt)
    return payload


def summarize_output_item(output, *, max_chars=500):
    output_type = output.get("output_type", "unknown")
    if output_type == "error":
        traceback = output.get("traceback", [])
        return {
            "output_type": output_type,
            "summary": output.get("evalue") or "Execution error.",
            "traceback_preview": traceback[:5],
        }
    if output_type == "stream":
        text = output.get("text", "")
        if isinstance(text, list):
            text = "".join(text)
        preview = text[:max_chars]
        return {
            "output_type": output_type,
            "summary": preview.strip() or "Stream output.",
            "truncated": len(text) > len(preview),
        }

    data = output.get("data", {})
    text_value = data.get("text/plain")
    if isinstance(text_value, list):
        text_value = "".join(text_value)
    if isinstance(text_value, str):
        preview = text_value[:max_chars]
        return {
            "output_type": output_type,
            "summary": preview.strip() or "Rich display output.",
            "truncated": len(text_value) > len(preview),
            "mime_types": sorted(data.keys()),
        }

    return {
        "output_type": output_type,
        "summary": "Non-text output available.",
        "mime_types": sorted(data.keys()),
    }


def cell_snapshot(cell, index):
    return {
        "cell_ref": cell_ref(cell, index),
        "cell_type": cell.get("cell_type"),
        "execution_count": cell.get("execution_count"),
        "status": cell_status(cell),
        "summary": summarize_cell(cell),
        "dirty_source": False,
        "dirty_output": dirty_output(cell),
        "source_revision": source_revision(cell_source(cell)),
        "output_revision": output_revision(cell_outputs(cell)),
        "section_label": infer_section_label(cell),
    }
