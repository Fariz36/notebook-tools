import argparse

from notebook_tools.commands import (
    cell_output,
    delete_cell,
    edit_cell,
    get_dependencies,
    interrupt,
    inspect_dataframe,
    inspect_variable,
    insert_cell,
    kernel_state,
    list_cells,
    list_variables,
    merge_cells,
    move_cell,
    read_cells,
    restart_kernel,
    run_cells,
    search_cells,
    shutdown_kernel,
    skills,
    split_cell,
    summarize,
)
from notebook_tools.notebook.loader import load_notebook, save_notebook
from notebook_tools.schemas.common import (
    FILE_ONLY_MODE,
    LIVE_SESSION_MODE,
    response_envelope,
)
from notebook_tools.utils.errors import DomainError
from notebook_tools.utils.json_io import dump_json, load_json_request


COMMANDS = {
    "list-cells": {"handler": list_cells.run, "mutates": False, "loads_notebook": True},
    "read-cells": {"handler": read_cells.run, "mutates": False, "loads_notebook": True},
    "search-cells": {
        "handler": search_cells.run,
        "mutates": False,
        "loads_notebook": True,
    },
    "cell-output": {
        "handler": cell_output.run,
        "mutates": False,
        "loads_notebook": True,
    },
    "get-dependencies": {
        "handler": get_dependencies.run,
        "mutates": False,
        "loads_notebook": True,
    },
    "summarize": {
        "handler": summarize.run,
        "mutates": False,
        "loads_notebook": True,
    },
    "edit-cell": {"handler": edit_cell.run, "mutates": True, "loads_notebook": True},
    "insert-cell": {
        "handler": insert_cell.run,
        "mutates": True,
        "loads_notebook": True,
    },
    "delete-cell": {
        "handler": delete_cell.run,
        "mutates": True,
        "loads_notebook": True,
    },
    "move-cell": {
        "handler": move_cell.run,
        "mutates": True,
        "loads_notebook": True,
    },
    "split-cell": {
        "handler": split_cell.run,
        "mutates": True,
        "loads_notebook": True,
    },
    "merge-cells": {
        "handler": merge_cells.run,
        "mutates": True,
        "loads_notebook": True,
    },
    "run-cells": {"handler": run_cells.run, "mutates": True, "loads_notebook": True},
    "kernel-state": {
        "handler": kernel_state.run,
        "mutates": False,
        "loads_notebook": False,
    },
    "list-variables": {
        "handler": list_variables.run,
        "mutates": False,
        "loads_notebook": False,
    },
    "inspect-variable": {
        "handler": inspect_variable.run,
        "mutates": False,
        "loads_notebook": False,
    },
    "inspect-dataframe": {
        "handler": inspect_dataframe.run,
        "mutates": False,
        "loads_notebook": False,
    },
    "interrupt": {"handler": interrupt.run, "mutates": False, "loads_notebook": False},
    "restart-kernel": {
        "handler": restart_kernel.run,
        "mutates": False,
        "loads_notebook": False,
    },
    "shutdown-kernel": {
        "handler": shutdown_kernel.run,
        "mutates": False,
        "loads_notebook": False,
    },
    "skills": {
        "handler": skills.run,
        "mutates": False,
        "loads_notebook": False,
    },
}


def add_common_args(parser):
    parser.add_argument("--notebook")
    parser.add_argument("--session")
    parser.add_argument("--input")
    parser.add_argument("--stdin-json", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--request-id")


def build_parser():
    parser = argparse.ArgumentParser(prog="notebook-tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-cells")
    add_common_args(list_parser)
    list_parser.add_argument("--max-items", type=int, default=20)

    read_parser = subparsers.add_parser("read-cells")
    add_common_args(read_parser)
    read_parser.add_argument("--cell-id", action="append")
    read_parser.add_argument("--index", action="append", type=int)
    read_parser.add_argument("--range-start", type=int)
    read_parser.add_argument("--range-end", type=int)
    read_parser.add_argument("--summary-mode", default="compact")
    read_parser.add_argument("--max-chars", type=int, default=4000)
    read_parser.add_argument("--include-outputs", action="store_true")

    search_parser = subparsers.add_parser("search-cells")
    add_common_args(search_parser)
    search_parser.add_argument("--query")
    search_parser.add_argument("--filter", choices=["code", "markdown"])
    search_parser.add_argument("--max-items", type=int, default=20)

    cell_output_parser = subparsers.add_parser("cell-output")
    add_common_args(cell_output_parser)
    cell_output_parser.add_argument("--cell-id")
    cell_output_parser.add_argument("--index", type=int)
    cell_output_parser.add_argument("--max-items", type=int, default=20)
    cell_output_parser.add_argument("--max-chars", type=int, default=500)

    dependencies_parser = subparsers.add_parser("get-dependencies")
    add_common_args(dependencies_parser)
    dependencies_parser.add_argument("--cell-id", action="append")
    dependencies_parser.add_argument("--index", action="append", type=int)
    dependencies_parser.add_argument("--range-start", type=int)
    dependencies_parser.add_argument("--range-end", type=int)
    dependencies_parser.add_argument("--mode", choices=["upstream", "downstream", "full"], default="full")

    summarize_parser = subparsers.add_parser("summarize")
    add_common_args(summarize_parser)
    summarize_parser.add_argument("--max-items", type=int, default=5)

    edit_parser = subparsers.add_parser("edit-cell")
    add_common_args(edit_parser)
    edit_parser.add_argument("--cell-id")
    edit_parser.add_argument("--index", type=int)
    edit_parser.add_argument("--edit-mode", choices=["replace", "append", "prepend"], default="replace")
    edit_parser.add_argument("--content")
    edit_parser.add_argument("--cell-source-revision")

    insert_parser = subparsers.add_parser("insert-cell")
    add_common_args(insert_parser)
    insert_parser.add_argument("--position", type=int, required=False)
    insert_parser.add_argument("--cell-type", choices=["code", "markdown", "raw"], default="code")
    insert_parser.add_argument("--content")

    delete_parser = subparsers.add_parser("delete-cell")
    add_common_args(delete_parser)
    delete_parser.add_argument("--cell-id")
    delete_parser.add_argument("--index", type=int)
    delete_parser.add_argument("--confirmation-token")

    move_parser = subparsers.add_parser("move-cell")
    add_common_args(move_parser)
    move_parser.add_argument("--cell-id")
    move_parser.add_argument("--index", type=int)
    move_parser.add_argument("--position", type=int)

    split_parser = subparsers.add_parser("split-cell")
    add_common_args(split_parser)
    split_parser.add_argument("--cell-id")
    split_parser.add_argument("--index", type=int)
    split_parser.add_argument("--split-at", action="append", type=int)

    merge_parser = subparsers.add_parser("merge-cells")
    add_common_args(merge_parser)
    merge_parser.add_argument("--cell-id", action="append")
    merge_parser.add_argument("--index", action="append", type=int)

    run_parser = subparsers.add_parser("run-cells")
    add_common_args(run_parser)
    run_parser.add_argument("--cell-id", action="append")
    run_parser.add_argument("--index", action="append", type=int)
    run_parser.add_argument("--range-start", type=int)
    run_parser.add_argument("--range-end", type=int)
    run_parser.add_argument("--all", action="store_true")
    run_parser.add_argument("--timeout", type=int, default=30)
    run_parser.add_argument("--startup-timeout", type=int, default=30)

    kernel_state_parser = subparsers.add_parser("kernel-state")
    add_common_args(kernel_state_parser)
    kernel_state_parser.add_argument("--timeout", type=int, default=30)
    kernel_state_parser.add_argument("--startup-timeout", type=int, default=30)
    kernel_state_parser.add_argument("--start-if-missing", action="store_true")

    list_variables_parser = subparsers.add_parser("list-variables")
    add_common_args(list_variables_parser)
    list_variables_parser.add_argument("--timeout", type=int, default=30)
    list_variables_parser.add_argument("--startup-timeout", type=int, default=30)
    list_variables_parser.add_argument("--start-if-missing", action="store_true")
    list_variables_parser.add_argument("--max-items", type=int, default=50)
    list_variables_parser.add_argument("--max-chars", type=int, default=120)

    inspect_variable_parser = subparsers.add_parser("inspect-variable")
    add_common_args(inspect_variable_parser)
    inspect_variable_parser.add_argument("--variable-name")
    inspect_variable_parser.add_argument("--timeout", type=int, default=30)
    inspect_variable_parser.add_argument("--startup-timeout", type=int, default=30)
    inspect_variable_parser.add_argument("--max-items", type=int, default=5)
    inspect_variable_parser.add_argument("--max-chars", type=int, default=240)

    inspect_dataframe_parser = subparsers.add_parser("inspect-dataframe")
    add_common_args(inspect_dataframe_parser)
    inspect_dataframe_parser.add_argument("--variable-name")
    inspect_dataframe_parser.add_argument("--timeout", type=int, default=30)
    inspect_dataframe_parser.add_argument("--startup-timeout", type=int, default=30)
    inspect_dataframe_parser.add_argument("--max-rows", type=int, default=5)
    inspect_dataframe_parser.add_argument("--max-chars", type=int, default=120)

    interrupt_parser = subparsers.add_parser("interrupt")
    add_common_args(interrupt_parser)

    restart_parser = subparsers.add_parser("restart-kernel")
    add_common_args(restart_parser)
    restart_parser.add_argument("--confirmation-token")
    restart_parser.add_argument("--startup-timeout", type=int, default=30)

    shutdown_parser = subparsers.add_parser("shutdown-kernel")
    add_common_args(shutdown_parser)
    shutdown_parser.add_argument("--confirmation-token")

    skills_parser = subparsers.add_parser("skills")
    add_common_args(skills_parser)
    skills_parser.add_argument("--raw", action="store_true", help="Return raw skills.md content")
    skills_parser.add_argument("--skill", help="Return a specific skill by name")

    return parser


def request_from_args(args):
    request = load_json_request(args)

    if args.command == "list-cells":
        request.setdefault("max_items", args.max_items)
    elif args.command == "read-cells":
        selector = request.setdefault("cell_selector", {})
        if args.cell_id:
            selector.setdefault("cell_ids", args.cell_id)
        if args.index:
            selector.setdefault("indexes", args.index)
        if args.range_start is not None or args.range_end is not None:
            selector.setdefault("range", {"start": args.range_start, "end": args.range_end})
        request.setdefault("summary_mode", args.summary_mode)
        request.setdefault("max_chars", args.max_chars)
        request.setdefault("include_outputs", args.include_outputs)
    elif args.command == "search-cells":
        if args.query is not None:
            request.setdefault("query", args.query)
        if args.filter is not None:
            request.setdefault("filter", args.filter)
        request.setdefault("max_items", args.max_items)
    elif args.command == "cell-output":
        if args.cell_id is not None:
            request.setdefault("cell_id", args.cell_id)
        if args.index is not None:
            request.setdefault("index", args.index)
        request.setdefault("max_items", args.max_items)
        request.setdefault("max_chars", args.max_chars)
    elif args.command == "get-dependencies":
        selector = request.setdefault("cell_selector", {})
        if args.cell_id:
            selector.setdefault("cell_ids", args.cell_id)
        if args.index:
            selector.setdefault("indexes", args.index)
        if args.range_start is not None or args.range_end is not None:
            selector.setdefault("range", {"start": args.range_start, "end": args.range_end})
        request.setdefault("mode", args.mode)
    elif args.command == "summarize":
        request.setdefault("max_items", args.max_items)
    elif args.command == "edit-cell":
        if args.cell_id is not None:
            request.setdefault("cell_id", args.cell_id)
        if args.index is not None:
            request.setdefault("index", args.index)
        request.setdefault("edit_mode", args.edit_mode)
        if args.content is not None:
            request.setdefault("new_content", args.content)
        if args.cell_source_revision is not None:
            request.setdefault("cell_source_revision", args.cell_source_revision)
    elif args.command == "insert-cell":
        if args.position is not None:
            request.setdefault("position", args.position)
        request.setdefault("cell_type", args.cell_type)
        if args.content is not None:
            request.setdefault("content", args.content)
    elif args.command == "delete-cell":
        if args.cell_id is not None:
            request.setdefault("cell_id", args.cell_id)
        if args.index is not None:
            request.setdefault("index", args.index)
        if args.confirmation_token is not None:
            request.setdefault("confirmation_token", args.confirmation_token)
    elif args.command == "move-cell":
        if args.cell_id is not None:
            request.setdefault("cell_id", args.cell_id)
        if args.index is not None:
            request.setdefault("index", args.index)
        if args.position is not None:
            request.setdefault("position", args.position)
    elif args.command == "split-cell":
        if args.cell_id is not None:
            request.setdefault("cell_id", args.cell_id)
        if args.index is not None:
            request.setdefault("index", args.index)
        request.setdefault("split_points", args.split_at or [])
    elif args.command == "merge-cells":
        selector = request.setdefault("cell_selector", {})
        if args.cell_id:
            selector.setdefault("cell_ids", args.cell_id)
        if args.index:
            selector.setdefault("indexes", args.index)
    elif args.command == "run-cells":
        selector = request.setdefault("cell_selector", {})
        if args.cell_id:
            selector.setdefault("cell_ids", args.cell_id)
        if args.index:
            selector.setdefault("indexes", args.index)
        if args.range_start is not None or args.range_end is not None:
            selector.setdefault("range", {"start": args.range_start, "end": args.range_end})
        request.setdefault("run_all", args.all)
        request.setdefault("timeout", args.timeout)
        request.setdefault("startup_timeout", args.startup_timeout)
    elif args.command == "kernel-state":
        request.setdefault("timeout", args.timeout)
        request.setdefault("startup_timeout", args.startup_timeout)
        request.setdefault("start_if_missing", args.start_if_missing)
    elif args.command == "restart-kernel":
        if args.confirmation_token is not None:
            request.setdefault("confirmation_token", args.confirmation_token)
        request.setdefault("startup_timeout", args.startup_timeout)
    elif args.command == "shutdown-kernel":
        if args.confirmation_token is not None:
            request.setdefault("confirmation_token", args.confirmation_token)
    elif args.command == "list-variables":
        request.setdefault("timeout", args.timeout)
        request.setdefault("startup_timeout", args.startup_timeout)
        request.setdefault("start_if_missing", args.start_if_missing)
        request.setdefault("max_items", args.max_items)
        request.setdefault("max_chars", args.max_chars)
    elif args.command == "inspect-variable":
        if args.variable_name is not None:
            request.setdefault("variable_name", args.variable_name)
        request.setdefault("timeout", args.timeout)
        request.setdefault("startup_timeout", args.startup_timeout)
        request.setdefault("max_items", args.max_items)
        request.setdefault("max_chars", args.max_chars)
    elif args.command == "inspect-dataframe":
        if args.variable_name is not None:
            request.setdefault("variable_name", args.variable_name)
        request.setdefault("timeout", args.timeout)
        request.setdefault("startup_timeout", args.startup_timeout)
        request.setdefault("max_rows", args.max_rows)
        request.setdefault("max_chars", args.max_chars)
    elif args.command == "skills":
        request.setdefault("raw", getattr(args, "raw", False))
        if getattr(args, "skill", None):
            request.setdefault("skill", args.skill)

    if args.notebook is not None:
        request.setdefault("notebook_ref", args.notebook)
    if args.session is not None:
        request.setdefault("kernel_session_id", args.session)
    if args.request_id is not None:
        request.setdefault("request_id", args.request_id)

    return request


def validate_request(command, request):
    requires_notebook = COMMANDS[command]["loads_notebook"] or (
        command == "kernel-state" and request.get("start_if_missing")
    )

    if requires_notebook and not request.get("notebook_ref"):
        raise DomainError("invalid_request", "A notebook_ref or --notebook path is required.")

    if command == "read-cells" and not request.get("cell_selector"):
        raise DomainError("invalid_request", "read-cells requires a cell selector.")

    if command == "search-cells" and not request.get("query"):
        raise DomainError("invalid_request", "search-cells requires a query.")

    if command == "cell-output":
        if request.get("cell_id") is None and request.get("index") is None:
            raise DomainError("invalid_request", "cell-output requires --cell-id or --index.")

    if command == "get-dependencies" and not request.get("cell_selector"):
        raise DomainError("invalid_request", "get-dependencies requires a cell selector.")

    if command == "edit-cell":
        if request.get("cell_id") is None and request.get("index") is None:
            raise DomainError("invalid_request", "edit-cell requires --cell-id or --index.")
        if request.get("new_content") is None:
            raise DomainError("invalid_request", "edit-cell requires new content.")

    if command == "insert-cell" and request.get("position") is None:
        raise DomainError("invalid_request", "insert-cell requires --position.")

    if command == "delete-cell":
        if request.get("cell_id") is None and request.get("index") is None:
            raise DomainError("invalid_request", "delete-cell requires --cell-id or --index.")

    if command == "move-cell":
        if request.get("cell_id") is None and request.get("index") is None:
            raise DomainError("invalid_request", "move-cell requires --cell-id or --index.")
        if request.get("position") is None:
            raise DomainError("invalid_request", "move-cell requires --position.")

    if command == "split-cell":
        if request.get("cell_id") is None and request.get("index") is None:
            raise DomainError("invalid_request", "split-cell requires --cell-id or --index.")
        if not request.get("split_points"):
            raise DomainError("invalid_request", "split-cell requires at least one --split-at value.")

    if command == "merge-cells" and not request.get("cell_selector"):
        raise DomainError("invalid_request", "merge-cells requires at least two target cells.")

    if command == "run-cells" and not request.get("run_all") and not request.get("cell_selector"):
        raise DomainError("invalid_request", "run-cells requires a cell selector or --all.")

    if command == "kernel-state" and not request.get("kernel_session_id") and not request.get("start_if_missing"):
        raise DomainError(
            "invalid_request",
            "kernel-state requires --session unless --start-if-missing is set.",
        )

    if command == "list-variables" and not request.get("kernel_session_id") and not request.get("notebook_ref"):
        raise DomainError(
            "invalid_request",
            "list-variables requires --session or --notebook.",
        )

    if command in {"inspect-variable", "inspect-dataframe"}:
        if not request.get("variable_name"):
            raise DomainError("invalid_request", f"{command} requires --variable-name.")
        if not request.get("kernel_session_id") and not request.get("notebook_ref"):
            raise DomainError(
                "invalid_request",
                f"{command} requires --session or --notebook.",
            )


def normalize_result(result):
    if isinstance(result, tuple):
        data, truncated, next_cursor = result
        return {
            "data": data,
            "truncated": truncated,
            "next_cursor": next_cursor,
            "warnings": [],
            "mode": None,
            "kernel_session_id": None,
            "observability": None,
        }
    return {
        "data": result.get("data", {}),
        "truncated": result.get("truncated", False),
        "next_cursor": result.get("next_cursor"),
        "warnings": result.get("warnings", []),
        "mode": result.get("mode"),
        "kernel_session_id": result.get("kernel_session_id"),
        "observability": result.get("observability"),
    }


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    request = {}

    try:
        request = request_from_args(args)
        validate_request(args.command, request)
        command_info = COMMANDS[args.command]
        path = None
        notebook = None
        notebook_revision = None
        if command_info["loads_notebook"]:
            path, notebook, notebook_revision = load_notebook(request["notebook_ref"])
        result = normalize_result(command_info["handler"](notebook, request))
        if command_info["mutates"]:
            save_notebook(path, notebook)
            _, _, notebook_revision = load_notebook(request["notebook_ref"])
        response = response_envelope(
            command=args.command,
            ok=True,
            request_id=request.get("request_id"),
            data=result["data"],
            warnings=result["warnings"],
            notebook_ref=request.get("notebook_ref"),
            notebook_revision=notebook_revision,
            truncated=result["truncated"],
            next_cursor=result["next_cursor"],
            mode=result["mode"] or FILE_ONLY_MODE,
            kernel_session_id=result["kernel_session_id"],
            observability=result["observability"],
        )
        dump_json(response, pretty=args.pretty)
        return 0
    except DomainError as exc:
        error_mode = LIVE_SESSION_MODE if request.get("kernel_session_id") else FILE_ONLY_MODE
        response = response_envelope(
            command=getattr(args, "command", None),
            ok=False,
            request_id=request.get("request_id") or getattr(args, "request_id", None),
            errors=[exc.to_dict()],
            notebook_ref=request.get("notebook_ref") or getattr(args, "notebook", None),
            mode=error_mode,
            kernel_session_id=request.get("kernel_session_id"),
            observability={
                "source": "observed",
                "runtime": "observed" if request.get("kernel_session_id") else "unavailable",
            },
        )
        dump_json(response, pretty=getattr(args, "pretty", False))
        return 0
    except ValueError as exc:
        error_mode = LIVE_SESSION_MODE if request.get("kernel_session_id") else FILE_ONLY_MODE
        response = response_envelope(
            command=getattr(args, "command", None),
            ok=False,
            request_id=request.get("request_id") or getattr(args, "request_id", None),
            errors=[DomainError("invalid_request", str(exc)).to_dict()],
            notebook_ref=request.get("notebook_ref") or getattr(args, "notebook", None),
            mode=error_mode,
            kernel_session_id=request.get("kernel_session_id"),
            observability={
                "source": "observed",
                "runtime": "observed" if request.get("kernel_session_id") else "unavailable",
            },
        )
        dump_json(response, pretty=getattr(args, "pretty", False))
        return 0
