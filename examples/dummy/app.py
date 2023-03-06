from mario import Mario

from .dummy_pipeline import DummyPipeline


app = Mario()

app.register_pipeline(DummyPipeline())
