import importlib
import importlib.util
import os
import pkgutil
import sys
import traceback
from pathlib import Path

import click

from ._version import __version__


def _ensure_cwd_importable() -> None:
    """Make the folder the command was run from importable.

    That is where a user's pipelines live, and it is not on the import path
    when the CLI is an installed script.
    """

    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)


def _missing_target(target: str) -> click.ClickException:
    return click.ClickException(
        f"Could not import '{target}'. Put your pipelines in a '{target}' "
        f"package (a '{target}/' folder next to where you run the command), "
        f"or point at a different module with --pipelines."
    )


def _report_broken_module(name: str) -> None:
    """Report a file that could not be imported, and carry on.

    Only used while reloading: a file that does not parse is the normal state
    of one being written, and it should cost its author the pipelines in that
    file, not the whole app.
    """

    traceback.print_exc()
    click.secho(f"\nCould not import {name}, skipping it.\n", fg="red")


def _load_pipelines(target: str, tolerate_errors: bool = False) -> None:
    """Import the module or package that registers the pipelines.

    The current working directory is put on the import path first, then
    `target` is imported. When `target` is a package — a `pipelines/` folder,
    with or without an `__init__.py` — every submodule in it is imported too,
    so each file that registers a pipeline runs.

    With `tolerate_errors` a file that fails to import is reported and
    skipped, instead of bringing the command down with it.
    """

    _ensure_cwd_importable()

    try:
        module = importlib.import_module(target)
    except ModuleNotFoundError as error:
        if tolerate_errors:
            _report_broken_module(target)
            return

        raise _missing_target(target) from error
    except Exception:
        if not tolerate_errors:
            raise

        _report_broken_module(target)
        return

    package_path = getattr(module, "__path__", None)
    if package_path is not None:
        for submodule in pkgutil.iter_modules(
            package_path, prefix=f"{module.__name__}."
        ):
            try:
                importlib.import_module(submodule.name)
            except Exception:
                if not tolerate_errors:
                    raise

                _report_broken_module(submodule.name)


def _has_watchfiles() -> bool:
    """Whether uvicorn will get its fast, event-driven reloader.

    Without it uvicorn polls every Python file under the working directory
    instead, which is slow next to a virtualenv and only ever notices files
    it has already seen.
    """

    return importlib.util.find_spec("watchfiles") is not None


def _is_importable(target: str) -> bool:
    _ensure_cwd_importable()

    try:
        return importlib.util.find_spec(target) is not None
    except (ImportError, ValueError):
        # A dotted target whose parent package is itself missing or broken
        return False


# How the reloader subprocess learns what to import: uvicorn re-runs the app
# factory in a fresh process, which never sees the command line arguments
PIPELINES_ENV_VAR = "PLOMBERY_CLI_PIPELINES"


def app_factory():
    """Build the app for uvicorn, loading the pipelines first.

    Only used with `--reload`: the reloader imports this by name in every
    worker process, so the pipelines have to be registered there rather than
    in the process that ran the command.

    A file that does not import is skipped rather than fatal, so that a typo
    costs you that file and not the app you are looking at. Serving without
    them would be the wrong call outside development, which is why the plain
    `run` path still stops at the first failure.
    """

    from plombery import get_app

    _load_pipelines(os.environ[PIPELINES_ENV_VAR], tolerate_errors=True)

    return get_app()


@click.group()
@click.version_option(__version__, prog_name="plombery")
def cli() -> None:
    """Plombery — run your pipelines."""


@cli.command()
@click.option(
    "--pipelines",
    "target",
    default="pipelines",
    show_default=True,
    help="Module or package that registers the pipelines.",
)
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind host.")
@click.option("--port", default=8000, show_default=True, type=int, help="Bind port.")
@click.option(
    "--reload",
    "reload",
    is_flag=True,
    help="Restart when a file changes. For development, never for production.",
)
@click.option(
    "--reload-dir",
    "reload_dirs",
    multiple=True,
    type=click.Path(exists=True, file_okay=False),
    help=(
        "Watch this folder too, on top of the one you run from. Repeatable, "
        "and useful to watch Plombery itself while working on it."
    ),
)
def run(target: str, host: str, port: int, reload: bool, reload_dirs: tuple) -> None:
    """Load the pipelines and serve the web app."""

    import uvicorn

    from plombery import get_app

    if reload_dirs and not reload:
        click.secho("--reload-dir does nothing without --reload.", fg="yellow")

    if reload:
        click.secho(
            "Reloading is meant for developing pipelines, not for running "
            "them in production.",
            fg="yellow",
        )

        if not _has_watchfiles():
            click.secho(
                "watchfiles is not installed, so reloading falls back to "
                "polling: a file you add is only picked up once you also "
                "edit one that already existed, and polling gets slow when a "
                "virtualenv sits in a watched folder. Install it with: pip "
                "install watchfiles",
                fg="yellow",
            )

        # Checked here rather than in the worker, where a mistyped target
        # would come back as a restart loop instead of an error
        if not _is_importable(target):
            raise _missing_target(target)

        # The app has to be an import string for uvicorn to be able to rebuild
        # it in the reloader's worker process, and the pipelines are loaded
        # there too, so that editing one takes effect
        os.environ[PIPELINES_ENV_VAR] = target

        # The folder the pipelines live in is always watched, the extra ones
        # are added to it rather than replacing it
        watched = [str(Path.cwd())]
        for directory in reload_dirs:
            resolved = str(Path(directory).resolve())
            if resolved not in watched:
                watched.append(resolved)

        uvicorn.run(
            "plombery.cli:app_factory",
            factory=True,
            host=host,
            port=port,
            reload=True,
            reload_dirs=watched,
        )

        return

    _load_pipelines(target)

    uvicorn.run(get_app(), host=host, port=port)


def main() -> None:
    cli()
