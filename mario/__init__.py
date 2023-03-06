from .api import app
from .orchestrator import orchestrator


class Mario:
    def register_pipeline(self, pipeline):
        orchestrator.register_pipeline(pipeline)

    # Wrap FastAPI ASGI interface so the Mario object
    # can be served directly by uvicorn
    async def __call__(self, scope, receive, send):
        await app.__call__(scope, receive, send)
