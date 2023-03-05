from mario.api import app
from mario.orchestrator import orchestrator

from .dummy_pipeline import DummyPipeline


orchestrator.register_pipeline(DummyPipeline())
