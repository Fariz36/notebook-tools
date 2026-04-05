import re

from notebook_tools.notebook.model import cell_ref, cell_source


def search_cells(notebook, *, query, cell_filter=None, max_items=20):
    compiled = re.compile(re.escape(query), flags=re.IGNORECASE)
    matches = []

    for index, cell in enumerate(notebook["cells"]):
        cell_type = cell.get("cell_type")
        if cell_filter == "code" and cell_type != "code":
            continue
        if cell_filter == "markdown" and cell_type != "markdown":
            continue

        source = cell_source(cell)
        match = compiled.search(source)
        if not match:
            continue

        start = max(match.start() - 40, 0)
        end = min(match.end() + 80, len(source))
        snippet = source[start:end].replace("\n", " ").strip()
        matches.append(
            {
                "cell_ref": cell_ref(cell, index),
                "match_type": "text",
                "query": query,
                "snippet": snippet,
                "score": 1.0,
            }
        )
        if len(matches) >= max_items:
            break

    return matches
