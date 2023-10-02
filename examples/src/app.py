#!/usr/bin/python3

"""
Run via the run.sh or run.ps1 script
"""

from plombery import get_app  # noqa: F401

from src import sales_pipeline, sync_pipeline, ssl_certificates  # noqa: F401


if __name__ == "__main__":
    import uvicorn

    # `reload_dirs` is used to reload when the plombery package itself changes
    # this is useful during development of the plombery package, normally shouldn't
    # be used
    uvicorn.run("plombery:get_app", reload=True, factory=True, reload_dirs="..")
