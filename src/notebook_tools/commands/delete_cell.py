from notebook_tools.notebook.mutations import delete_cell
from notebook_tools.notebook.selectors import resolve_single_target


def run(notebook, request):
    index, _cell = resolve_single_target(
        notebook,
        cell_id=request.get("cell_id"),
        index=request.get("index"),
    )
    deleted_ref, ordering = delete_cell(
        notebook,
        index=index,
        confirmation_token=request.get("confirmation_token"),
    )
    return (
        {
            "deleted_cell_ref": deleted_ref,
            "cells": ordering,
        },
        False,
        None,
    )
