from fastapi.testclient import TestClient
import pytest

from plombery import _Plombery as Plombery
from plombery.api import app
from .pipeline_1 import pipeline1, pipeline1_serialized


client = TestClient(app)


@pytest.mark.asyncio
async def test_api_list_pipelines(app: Plombery):
    app.register_pipeline(pipeline1)

    response = client.get("/api/pipelines/")

    assert response.status_code == 200
    assert response.json() == [pipeline1_serialized]


@pytest.mark.asyncio
async def test_api_list_pipelines_with_auth(with_auth, authenticated, app: Plombery):
    app.register_pipeline(pipeline1)

    response = client.get("/api/pipelines/")

    assert response.status_code == 200
    assert response.json() == [pipeline1_serialized]


@pytest.mark.asyncio
async def test_api_get_pipeline(app: Plombery):
    app.register_pipeline(pipeline1)

    response = client.get("/api/pipelines/pipeline1")

    assert response.status_code == 200
    assert response.json() == pipeline1_serialized


@pytest.mark.asyncio
async def test_api_get_pipeline_with_auth(with_auth, authenticated, app: Plombery):
    app.register_pipeline(pipeline1)

    response = client.get("/api/pipelines/pipeline1")

    assert response.status_code == 200
    assert response.json() == pipeline1_serialized


@pytest.mark.asyncio
async def test_api_get_pipeline_not_existing(app: Plombery):
    app.register_pipeline(pipeline1)

    response = client.get("/api/pipelines/not-existing")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "The pipeline with ID not-existing doesn't exist"
    }


@pytest.mark.asyncio
@pytest.mark.skip
async def test_api_with_auth_when_not_authenticated(with_auth, app: Plombery):
    NOT_AUTH_MSG = {"detail": "You must be authenticated to access this API route"}

    response = client.get("/api/pipelines")
    assert response.status_code == 401
    assert response.json() == NOT_AUTH_MSG

    response = client.get("/api/pipelines/pipeid")
    assert response.status_code == 401
    assert response.json() == NOT_AUTH_MSG
