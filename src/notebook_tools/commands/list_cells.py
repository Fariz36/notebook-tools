from notebook_tools.notebook.model import cell_snapshot


def run(notebook, request):
    max_items = int(request.get("max_items", 20))
    cells = [cell_snapshot(cell, index) for index, cell in enumerate(notebook["cells"])]
    truncated = len(cells) > max_items
    return (
        {
            "cells": cells[:max_items],
        },
        truncated,
        (str(max_items) if truncated else None),
    )
