import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from notebook_tools.cli import main
from notebook_tools.runtime.jupyter import runtime_root


FIXTURE = Path(__file__).parent / "fixtures" / "demo.ipynb"
LIVE_FIXTURE = Path(__file__).parent / "fixtures" / "live_demo.ipynb"


def live_runtime_available():
    try:
        import ipykernel  # noqa: F401
        import jupyter_client  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


class CLITestCase(unittest.TestCase):
    def run_cli(self, *argv):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(list(argv))
        self.assertEqual(exit_code, 0)
        return json.loads(buffer.getvalue())

    def test_list_cells(self):
        payload = self.run_cli("list-cells", "--notebook", str(FIXTURE))
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "list-cells")
        self.assertEqual(len(payload["data"]["cells"]), 4)
        self.assertEqual(payload["data"]["cells"][0]["cell_ref"]["cell_id"], "intro001")
        self.assertFalse(payload["data"]["cells"][1]["dirty_output"])

    def test_read_cells_with_outputs(self):
        payload = self.run_cli(
            "read-cells",
            "--notebook",
            str(FIXTURE),
            "--index",
            "2",
            "--include-outputs",
        )
        self.assertTrue(payload["ok"])
        cell = payload["data"]["cells"][0]
        self.assertEqual(cell["cell_ref"]["index"], 2)
        self.assertIn("outputs", cell)
        self.assertEqual(cell["outputs"][0]["output_type"], "stream")

    def test_search_cells(self):
        payload = self.run_cli(
            "search-cells", "--notebook", str(FIXTURE), "--query", "revenue"
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["data"]["matches"][0]["cell_ref"]["cell_id"], "code003"
        )

    def test_cell_output(self):
        payload = self.run_cli(
            "cell-output",
            "--notebook",
            str(FIXTURE),
            "--index",
            "1",
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["cell_ref"]["cell_id"], "code001")
        self.assertIn("error", payload["data"]["output_types"])
        self.assertIsNotNone(payload["data"]["traceback"])

    def test_get_dependencies(self):
        payload = self.run_cli(
            "get-dependencies",
            "--notebook",
            str(FIXTURE),
            "--index",
            "3",
        )
        self.assertTrue(payload["ok"])
        selected = payload["data"]["selected_cells"][0]
        self.assertEqual(selected["cell_ref"]["cell_id"], "code003")
        self.assertIn("df", selected["referenced_symbols"])
        upstream_ids = {item["cell_id"] for item in payload["data"]["direct_upstream"]}
        self.assertIn("code002", upstream_ids)

    def test_summarize(self):
        payload = self.run_cli("summarize", "--notebook", str(FIXTURE))
        self.assertTrue(payload["ok"])
        self.assertIn("Notebook has 4 cells", payload["data"]["workflow_summary"])
        self.assertIn("data_loading", payload["data"]["major_sections"])
        self.assertTrue(payload["data"]["open_issues"])

    def test_runtime_root_uses_env_override(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_root = Path(tmpdir) / "runtime-store"
            with patch.dict(
                os.environ,
                {"NOTEBOOK_TOOLS_RUNTIME_DIR": str(custom_root)},
                clear=False,
            ):
                root = runtime_root()
            self.assertEqual(root, custom_root.resolve())
            self.assertTrue((root / "sessions").exists())
            self.assertTrue((root / "connections").exists())

    def test_edit_and_insert_mutate_copy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = Path(tmpdir) / "demo.ipynb"
            shutil.copyfile(FIXTURE, notebook_path)

            edit_payload = self.run_cli(
                "edit-cell",
                "--notebook",
                str(notebook_path),
                "--index",
                "3",
                "--edit-mode",
                "append",
                "--content",
                "# comment",
            )
            self.assertTrue(edit_payload["ok"])
            self.assertIn("# comment", edit_payload["data"]["updated_cell"]["source"])

            insert_payload = self.run_cli(
                "insert-cell",
                "--notebook",
                str(notebook_path),
                "--position",
                "1",
                "--cell-type",
                "markdown",
                "--content",
                "## Note",
            )
            self.assertTrue(insert_payload["ok"])
            self.assertEqual(insert_payload["data"]["created_cell_ref"]["index"], 1)

    def test_structural_edits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = Path(tmpdir) / "demo.ipynb"
            shutil.copyfile(FIXTURE, notebook_path)

            delete_payload = self.run_cli(
                "delete-cell",
                "--notebook",
                str(notebook_path),
                "--index",
                "0",
                "--confirmation-token",
                "confirm",
            )
            self.assertTrue(delete_payload["ok"])
            self.assertEqual(
                delete_payload["data"]["deleted_cell_ref"]["cell_id"], "intro001"
            )
            self.assertEqual(len(delete_payload["data"]["cells"]), 3)

            move_payload = self.run_cli(
                "move-cell",
                "--notebook",
                str(notebook_path),
                "--cell-id",
                "code003",
                "--position",
                "1",
            )
            self.assertTrue(move_payload["ok"])
            self.assertEqual(move_payload["data"]["moved_cell_ref"]["index"], 1)
            self.assertEqual(
                move_payload["data"]["cells"][1]["cell_ref"]["cell_id"], "code003"
            )

            split_payload = self.run_cli(
                "split-cell",
                "--notebook",
                str(notebook_path),
                "--cell-id",
                "code001",
                "--split-at",
                "1",
            )
            self.assertTrue(split_payload["ok"])
            self.assertEqual(
                split_payload["data"]["updated_cell_ref"]["cell_id"], "code001"
            )
            self.assertEqual(len(split_payload["data"]["created_cell_refs"]), 1)

            merge_payload = self.run_cli(
                "merge-cells",
                "--notebook",
                str(notebook_path),
                "--index",
                "0",
                "--index",
                "1",
            )
            self.assertTrue(merge_payload["ok"])
            self.assertEqual(
                merge_payload["data"]["merged_cell_ref"]["cell_id"], "code001"
            )
            self.assertEqual(merge_payload["data"]["merged_from_indexes"], [0, 1])

    def test_run_cells_dependency_error_or_live_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = Path(tmpdir) / "live.ipynb"
            shutil.copyfile(LIVE_FIXTURE, notebook_path)

            payload = self.run_cli(
                "run-cells",
                "--notebook",
                str(notebook_path),
                "--index",
                "0",
                "--timeout",
                "15",
                "--startup-timeout",
                "15",
            )

            if live_runtime_available():
                self.assertTrue(payload["ok"])
                self.assertEqual(payload["mode"], "live_session")
                session_id = payload["meta"]["kernel_session_id"]
                self.assertIsNotNone(session_id)
                self.assertEqual(payload["data"]["execution"]["status"], "completed")
                shutdown_payload = self.run_cli(
                    "shutdown-kernel",
                    "--notebook",
                    str(notebook_path),
                    "--session",
                    session_id,
                    "--confirmation-token",
                    "confirm",
                )
                self.assertTrue(shutdown_payload["ok"])
            else:
                self.assertFalse(payload["ok"])
                self.assertEqual(payload["errors"][0]["code"], "kernel_unavailable")

    def test_runtime_variable_inspection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook_path = Path(tmpdir) / "live.ipynb"
            shutil.copyfile(LIVE_FIXTURE, notebook_path)

            run_payload = self.run_cli(
                "run-cells",
                "--notebook",
                str(notebook_path),
                "--index",
                "0",
                "--timeout",
                "15",
                "--startup-timeout",
                "15",
            )

            if not live_runtime_available():
                self.assertFalse(run_payload["ok"])
                self.assertEqual(run_payload["errors"][0]["code"], "kernel_unavailable")
                return

            session_id = run_payload["meta"]["kernel_session_id"]
            try:
                list_payload = self.run_cli(
                    "list-variables",
                    "--session",
                    session_id,
                    "--notebook",
                    str(notebook_path),
                )
                self.assertTrue(list_payload["ok"])
                variable_names = {
                    item["name"] for item in list_payload["data"]["variables"]
                }
                self.assertIn("value", variable_names)
                self.assertIn("items", variable_names)

                inspect_payload = self.run_cli(
                    "inspect-variable",
                    "--session",
                    session_id,
                    "--notebook",
                    str(notebook_path),
                    "--variable-name",
                    "record",
                )
                self.assertTrue(inspect_payload["ok"])
                self.assertEqual(inspect_payload["data"]["name"], "record")
                self.assertEqual(inspect_payload["data"]["type"], "builtins.dict")

                dataframe_payload = self.run_cli(
                    "inspect-dataframe",
                    "--session",
                    session_id,
                    "--notebook",
                    str(notebook_path),
                    "--variable-name",
                    "record",
                )
                self.assertFalse(dataframe_payload["ok"])
                self.assertIn(
                    dataframe_payload["errors"][0]["code"],
                    {"pandas_unavailable", "not_a_dataframe"},
                )
            finally:
                shutdown_payload = self.run_cli(
                    "shutdown-kernel",
                    "--session",
                    session_id,
                    "--confirmation-token",
                    "confirm",
                )
                self.assertTrue(shutdown_payload["ok"])


if __name__ == "__main__":
    unittest.main()
