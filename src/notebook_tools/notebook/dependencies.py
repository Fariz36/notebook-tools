import ast

from notebook_tools.notebook.model import cell_ref, cell_source


class SymbolCollector(ast.NodeVisitor):
    def __init__(self):
        self.defined = set()
        self.referenced = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.defined.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.referenced.add(node.id)

    def visit_FunctionDef(self, node):
        self.defined.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.defined.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.defined.add(node.name)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.defined.add(alias.asname or alias.name.split(".")[0])

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.defined.add(alias.asname or alias.name)


def analyze_cell_symbols(cell):
    if cell.get("cell_type") != "code":
        return {"defined": set(), "referenced": set(), "confidence": "heuristic"}

    source = cell_source(cell)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"defined": set(), "referenced": set(), "confidence": "heuristic"}

    collector = SymbolCollector()
    collector.visit(tree)
    referenced = collector.referenced - collector.defined
    return {
        "defined": collector.defined,
        "referenced": referenced,
        "confidence": "derived",
    }


def notebook_symbol_table(notebook):
    entries = []
    last_definition = {}
    for index, cell in enumerate(notebook["cells"]):
        symbols = analyze_cell_symbols(cell)
        entries.append(
            {
                "index": index,
                "cell": cell,
                "cell_ref": cell_ref(cell, index),
                "defined": symbols["defined"],
                "referenced": symbols["referenced"],
                "confidence": symbols["confidence"],
                "upstream_indexes": set(),
            }
        )

        for symbol in symbols["referenced"]:
            defining_index = last_definition.get(symbol)
            if defining_index is not None:
                entries[-1]["upstream_indexes"].add(defining_index)

        for symbol in symbols["defined"]:
            last_definition[symbol] = index

    downstream_map = {entry["index"]: set() for entry in entries}
    for entry in entries:
        for upstream_index in entry["upstream_indexes"]:
            downstream_map[upstream_index].add(entry["index"])

    return entries, downstream_map


def _transitive_closure(seed_indexes, adjacency):
    visited = set()
    stack = list(seed_indexes)
    while stack:
        current = stack.pop()
        for next_index in adjacency.get(current, set()):
            if next_index in visited:
                continue
            visited.add(next_index)
            stack.append(next_index)
    return visited


def build_dependency_report(notebook, selected_indexes, *, mode="full"):
    entries, downstream_map = notebook_symbol_table(notebook)
    entry_by_index = {entry["index"]: entry for entry in entries}

    direct_edges = []
    for target_index in selected_indexes:
        target = entry_by_index[target_index]
        for upstream_index in sorted(target["upstream_indexes"]):
            upstream = entry_by_index[upstream_index]
            shared_symbols = sorted(upstream["defined"] & target["referenced"])
            direct_edges.append(
                {
                    "source_cell_ref": upstream["cell_ref"],
                    "target_cell_ref": target["cell_ref"],
                    "relationship": "depends_on",
                    "symbols": shared_symbols,
                    "confidence": target["confidence"],
                }
            )

    upstream_graph = {entry["index"]: entry["upstream_indexes"] for entry in entries}
    direct_upstream = set()
    direct_downstream = set()
    for index in selected_indexes:
        direct_upstream.update(entry_by_index[index]["upstream_indexes"])
        direct_downstream.update(downstream_map[index])

    transitive_upstream = _transitive_closure(selected_indexes, upstream_graph)
    transitive_downstream = _transitive_closure(selected_indexes, downstream_map)

    report = {
        "dependencies": direct_edges,
        "selected_cells": [],
        "direct_upstream": [
            entry_by_index[index]["cell_ref"] for index in sorted(direct_upstream)
        ],
        "direct_downstream": [
            entry_by_index[index]["cell_ref"] for index in sorted(direct_downstream)
        ],
        "transitive_upstream": [
            entry_by_index[index]["cell_ref"] for index in sorted(transitive_upstream)
        ],
        "transitive_downstream": [
            entry_by_index[index]["cell_ref"] for index in sorted(transitive_downstream)
        ],
    }

    for index in selected_indexes:
        entry = entry_by_index[index]
        report["selected_cells"].append(
            {
                "cell_ref": entry["cell_ref"],
                "defined_symbols": sorted(entry["defined"]),
                "referenced_symbols": sorted(entry["referenced"]),
                "confidence": entry["confidence"],
            }
        )

    if mode == "upstream":
        report.pop("direct_downstream", None)
        report.pop("transitive_downstream", None)
    elif mode == "downstream":
        report.pop("direct_upstream", None)
        report.pop("transitive_upstream", None)

    return report
