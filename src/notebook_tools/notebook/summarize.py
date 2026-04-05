from collections import Counter

from notebook_tools.notebook.dependencies import notebook_symbol_table
from notebook_tools.notebook.model import (
    cell_outputs,
    cell_snapshot,
    summarize_output_item,
)


def summarize_notebook(notebook, *, max_output_items=5):
    cells = [cell_snapshot(cell, index) for index, cell in enumerate(notebook["cells"])]
    symbol_entries, _ = notebook_symbol_table(notebook)

    sections = []
    for cell in cells:
        label = cell.get("section_label")
        if label and label not in sections:
            sections.append(label)

    defined_counter = Counter()
    for entry in symbol_entries:
        defined_counter.update(entry["defined"])

    key_variables = [name for name, _count in defined_counter.most_common(8)]

    key_outputs = []
    open_issues = []
    for index, cell in enumerate(notebook["cells"]):
        snapshot = cells[index]
        outputs = cell_outputs(cell)
        if outputs:
            for output in outputs[:max_output_items]:
                key_outputs.append(
                    {
                        "cell_ref": snapshot["cell_ref"],
                        "output": summarize_output_item(output),
                    }
                )
        if snapshot["status"] == "error":
            open_issues.append(
                {
                    "cell_ref": snapshot["cell_ref"],
                    "issue": "Cell has an execution error in stored outputs.",
                }
            )
        elif snapshot["cell_type"] == "code" and snapshot["execution_count"] is None:
            open_issues.append(
                {
                    "cell_ref": snapshot["cell_ref"],
                    "issue": "Code cell has not been executed yet.",
                }
            )

    code_cells = [cell for cell in cells if cell["cell_type"] == "code"]
    workflow_parts = []
    if sections:
        workflow_parts.append(f"Sections: {', '.join(sections)}.")
    workflow_parts.append(
        f"Notebook has {len(cells)} cells, including {len(code_cells)} code cells."
    )
    if key_variables:
        workflow_parts.append(f"Key variables include {', '.join(key_variables[:4])}.")
    if any(cell["status"] == "error" for cell in cells):
        workflow_parts.append("Stored outputs show at least one failing cell.")

    return {
        "workflow_summary": " ".join(workflow_parts),
        "major_sections": sections,
        "cell_count": len(cells),
        "code_cell_count": len(code_cells),
        "key_variables": key_variables,
        "key_outputs": key_outputs[:max_output_items],
        "open_issues": open_issues,
    }
