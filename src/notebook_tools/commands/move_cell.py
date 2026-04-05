from notebook_tools.notebook.mutations import move_cell
from notebook_tools.notebook.selectors import resolve_single_target


def run(notebook, request):
    index, _cell = resolve_single_target(
        notebook,
        cell_id=request.get("cell_id"),
        index=request.get("index"),
    )
    moved_ref, ordering = move_cell(
        notebook,
        index=index,
        position=int(request.get("position")),
    )
    return (
        {
            "moved_cell_ref": moved_ref,
            "cells": ordering,
        },
        False,
        None,
    )
