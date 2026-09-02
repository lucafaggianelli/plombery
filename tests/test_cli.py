import os
import sys
import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from plombery.cli import PIPELINES_ENV_VAR, _load_pipelines, app_factory, cli
from plombery.orchestrator import orchestrator


def _write_pipelines_package(root: Path, name: str = "pipelines") -> None:
    package = root / name
    package.mkdir()
    (package / "sales.py").write_text(
        textwrap.dedent(
            """
            from plombery import Pipeline, task

            with Pipeline(id="sales_from_cli") as pipeline:
                @task
                def extract():
                    return 1
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


def test_run_with_reload_serves_an_import_string(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Reloading restarts the app in a new process, which can only rebuild it
    from an import string, and has to load the pipelines there itself."""

    _write_pipelines_package(tmp_path)
    monkeypatch.chdir(tmp_path)
    _reset()

    served = {}

    def fake_run(app, **kwargs):
        served.update(app=app, **kwargs)

    monkeypatch.setattr("uvicorn.run", fake_run)
    # Set through monkeypatch so that the value the command writes over it is
    # rolled back with the fixture
    monkeypatch.setenv(PIPELINES_ENV_VAR, "")

    result = CliRunner().invoke(cli, ["run", "--reload"])

    assert result.exit_code == 0, result.output
    assert "not for running them in production" in result.output
    assert served["app"] == "plombery.cli:app_factory"
    assert served["factory"] is True
    assert served["reload"] is True
    assert served["reload_dirs"] == [str(tmp_path)]

    # The worker process gets the target this way, as it never sees the
    # command line arguments
    assert os.environ[PIPELINES_ENV_VAR] == "pipelines"

    _reset()


def test_reload_dir_adds_to_the_folder_it_runs_from(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Watching Plombery itself is the reason this exists, and it must not
    cost you the pipelines you are editing at the same time."""

    _write_pipelines_package(tmp_path)
    extra = tmp_path / "library"
    extra.mkdir()
    monkeypatch.chdir(tmp_path)
    _reset()

    served = {}
    monkeypatch.setattr("uvicorn.run", lambda app, **kwargs: served.update(kwargs))
    monkeypatch.setenv(PIPELINES_ENV_VAR, "")

    result = CliRunner().invoke(cli, ["run", "--reload", "--reload-dir", str(extra)])

    assert result.exit_code == 0, result.output
    assert served["reload_dirs"] == [str(tmp_path), str(extra.resolve())]

    _reset()


def test_reload_dir_without_reload_says_it_does_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _write_pipelines_package(tmp_path)
    monkeypatch.chdir(tmp_path)
    _reset()

    monkeypatch.setattr("uvicorn.run", lambda app, **kwargs: None)

    result = CliRunner().invoke(cli, ["run", "--reload-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "--reload-dir does nothing without --reload" in result.output

    _reset()


def test_run_with_reload_points_at_watchfiles_when_it_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The fallback reloader is slow and misses new files, so say so rather
    than letting it look like reloading is simply broken."""

    _write_pipelines_package(tmp_path)
    monkeypatch.chdir(tmp_path)
    _reset()

    monkeypatch.setattr("uvicorn.run", lambda app, **kwargs: None)
    monkeypatch.setenv(PIPELINES_ENV_VAR, "")

    monkeypatch.setattr("plombery.cli._has_watchfiles", lambda: False)
    missing = CliRunner().invoke(cli, ["run", "--reload"])

    monkeypatch.setattr("plombery.cli._has_watchfiles", lambda: True)
    installed = CliRunner().invoke(cli, ["run", "--reload"])

    assert "watchfiles is not installed" in missing.output
    assert "watchfiles" not in installed.output

    _reset()


def test_app_factory_registers_the_pipelines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """What the reloader's worker process runs: it has to end up with the same
    pipelines the parent would have loaded."""

    _write_pipelines_package(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(PIPELINES_ENV_VAR, "pipelines")
    _reset()

    app = app_factory()

    assert app is not None
    assert "sales_from_cli" in orchestrator.pipelines

    _reset()


def test_app_factory_skips_a_file_that_does_not_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A half-written file is the normal state of one being edited: while
    reloading it should cost its own pipelines, not the whole app."""

    _write_pipelines_package(tmp_path)
    (tmp_path / "pipelines" / "broken.py").write_text("this is not python (((")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(PIPELINES_ENV_VAR, "pipelines")
    _reset()

    app = app_factory()

    assert app is not None
    assert "sales_from_cli" in orchestrator.pipelines

    _reset()


def test_loading_pipelines_outside_reload_stops_at_a_broken_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Serving without the pipelines that failed would be the wrong default
    for anything but development, so the plain path still raises."""

    _write_pipelines_package(tmp_path)
    (tmp_path / "pipelines" / "broken.py").write_text("this is not python (((")
    monkeypatch.chdir(tmp_path)
    _reset()

    with pytest.raises(SyntaxError):
        _load_pipelines("pipelines")

    _reset()


def test_run_with_reload_rejects_a_missing_module_before_serving(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Caught in the command, as the reloader's worker would only turn it into
    a restart loop."""

    monkeypatch.chdir(tmp_path)
    _reset("does_not_exist")

    served = {}
    monkeypatch.setattr("uvicorn.run", lambda app, **kwargs: served.update(app=app))

    result = CliRunner().invoke(
        cli, ["run", "--pipelines", "does_not_exist", "--reload"]
    )

    assert result.exit_code != 0
    assert "Could not import 'does_not_exist'" in result.output
    assert served == {}


def test_run_reports_a_clear_error_for_a_missing_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    _reset("does_not_exist")

    result = CliRunner().invoke(cli, ["run", "--pipelines", "does_not_exist"])

    assert result.exit_code != 0
    assert "Could not import 'does_not_exist'" in result.output
