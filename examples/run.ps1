$env:PYTHONPATH="$(pwd)/.."
uvicorn src.app:app --reload --reload-dir ..