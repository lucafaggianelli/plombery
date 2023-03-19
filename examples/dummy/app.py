"""
# Run as:
```sh
cd examples
export PYTHONPATH=$(pwd)/..
uvicorn dummy.app:app --reload --reload-dir ..
```
"""

from mario import Mario

from .dummy_pipeline import DummyPipeline


app = Mario()

app.register_pipeline(DummyPipeline())
