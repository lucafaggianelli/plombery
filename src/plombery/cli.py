import importlib
import pkgutil
import sys
from pathlib import Path

import click

from ._version import __version__


def _load_pipelines(target: str) -> None:
    """Import the module or package that registers the pipelines.

    The current working directory is put on the import path first, then
    `target` is imported. When `target` is a package — a `pipelines/` folder,
    with or without an `__init__.py` — every submodule in it is imported too,
    so each file that registers a pipeline runs.
    """

    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    try:
        module = importlib.import_module(target)
    except ModuleNotFoundError as error:
        raise click.ClickException(
            f"Could not import '{target}'. Put your pipelines in a '{target}' "
            f"package (a '{target}/' folder next to where you run the command), "
            f"or point at a different module with --pipelines."
        ) from error

    package_path = getattr(module, "__path__", None)
    if package_path is not None:
        for submodule in pkgutil.iter_modules(
            package_path, prefix=f"{module.__name__}."
        ):
            importlib.import_module(submodule.name)


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
def run(target: str, host: str, port: int) -> None:
    """Load the pipelines and serve the web app."""

    import uvicorn

    from plombery import get_app

    _load_pipelines(target)

    uvicorn.run(get_app(), host=host, port=port)


def main() -> None:
    cli()
