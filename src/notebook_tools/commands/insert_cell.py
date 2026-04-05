from notebook_tools.notebook.mutations import insert_cell


def run(notebook, request):
    created_ref, ordering = insert_cell(
        notebook,
        position=int(request.get("position", 0)),
        cell_type=request.get("cell_type", "code"),
        content=request.get("content", ""),
    )
    return (
        {
            "created_cell_ref": created_ref,
            "cells": ordering,
        },
        False,
        None,
    )
