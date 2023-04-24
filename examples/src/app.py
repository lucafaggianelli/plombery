"""
# Run as:
```sh
cd examples
export PYTHONPATH=$(pwd)/..
uvicorn src.app:app --reload --reload-dir ..
```
"""

from mario import Mario

from .sales_pipeline import sales_pipeline
from .sync_pipeline import sync_pipeline


app = Mario()

app.register_pipeline(sales_pipeline)
app.register_pipeline(sync_pipeline)
