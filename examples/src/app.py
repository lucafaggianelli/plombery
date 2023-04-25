"""
Run via the run.sh or run.ps1 script
"""

from mario import get_app  # noqa: F401

from examples.src import sales_pipeline, sync_pipeline  # noqa: F401


if __name__ == "__main__":
    import uvicorn

    # `reload_dirs` is used to reload when the mario package itself changes
    # this is useful during development of the mario package, normally shouldn't
    # be used
    uvicorn.run("mario:get_app", reload=True, factory=True, reload_dirs="..")
