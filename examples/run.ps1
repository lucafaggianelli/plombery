$env:PYTHONPATH="$(pwd)/.."
uvicorn "src.app:get_app" --reload --factory --reload-dir=".."
