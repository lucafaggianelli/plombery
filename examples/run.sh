export PYTHONPATH=$(pwd)/..
uvicorn dummy.app:app --reload --reload-dir ..