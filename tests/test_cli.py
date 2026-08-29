import sys
import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from plombery.cli import _load_pipelines, cli
from plombery.orchestrator import orchestrator


def _write_pipelines_package(root: Path, name: str = "pipelines") -> None:
    package = root / name
    package.mkdir()
    (package / "sales.py").write_text(
        textwrap.dedent(
            """
            from plombery import Pipeline, register_pipeline, task

            with Pipeline(id="sales_from_cli") as pipeline:
                @task
                def extract():
                    return 1

            register_pipeline(pipeline)
            """
        )
    )


def _reset(name: str = "pipelines") -> None:
    orchestrator._all_pipelines.clear()
    orchestrator._all_triggers.clear()

    for module_name in list(sys.modules):
        if module_name == name or module_name.startswith(f"{name}."):
            del sys.modules[module_name]


def test_load_pipelines_imports_a_package_and_registers_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A `pipelines/` folder is imported as a package and every submodule in it
    runs, so each file that registers a pipeline takes effect."""

    _write_pipelines_package(tmp_path)
    monkeypatch.chdir(tmp_path)
    _reset()

    _load_pipelines("pipelines")

    assert "sales_from_cli" in orchestrator.pipelines

    _reset()


def test_run_loads_the_pipelines_then_serves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _write_pipelines_package(tmp_path)
    monkeypatch.chdir(tmp_path)
    _reset()

    served = {}

    def fake_run(app, host, port):
        served.update(app=app, host=host, port=port)

    monkeypatch.setattr("uvicorn.run", fake_run)

    result = CliRunner().invoke(cli, ["run", "--host", "0.0.0.0", "--port", "9999"])

    assert result.exit_code == 0, result.output
    assert "sales_from_cli" in orchestrator.pipelines
    assert served["host"] == "0.0.0.0"
    assert served["port"] == 9999
    assert served["app"] is not None

    _reset()


def test_run_reports_a_clear_error_for_a_missing_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    _reset("does_not_exist")

    result = CliRunner().invoke(cli, ["run", "--pipelines", "does_not_exist"])

    assert result.exit_code != 0
    assert "Could not import 'does_not_exist'" in result.output
