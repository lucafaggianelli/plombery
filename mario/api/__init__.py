from datetime import datetime

from apscheduler.job import Job
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.date import DateTrigger
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from mario.orchestrator import orchestrator
from mario.pipeline.pipeline import Pipeline, Trigger, Task
from mario.orchestrator.executor import (
    get_pipeline_run_logs,
    get_pipeline_run_data,
    run,
)
from mario.database.models import PipelineRun
from mario.database.repository import (
    list_pipeline_runs,
    get_pipeline_run,
)
from mario.websocket import manager
from .middlewares import FRONTEND_FOLDER, SPAStaticFiles


app = FastAPI()

api = FastAPI()
app.mount("/api", api)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize_trigger(trigger: Trigger):
    return dict(
        id=trigger.id,
        name=trigger.name,
        description=trigger.description,
        interval=str(trigger.aps_trigger),
        next_fire_time=trigger.aps_trigger.get_next_fire_time(
            datetime.now(), datetime.now()
        ),
        paused=trigger.paused,
    )


def _serialize_task(task: Task):
    print(task.uuid, task.description)
    return {
        "id": task.uuid,
        "name": task.uuid,
        "description": task.description,
    }


def _serialize_pipeline(pipeline: Pipeline):
    return dict(
        id=pipeline.uuid,
        name=pipeline.uuid,
        description=pipeline.description,
        tasks=[_serialize_task(task) for task in pipeline.tasks],
        triggers=[_serialize_trigger(trigger) for trigger in pipeline.triggers],
    )


@api.get("/pipelines")
def list_pipelines():
    return [
        _serialize_pipeline(pipeline) for pipeline in orchestrator.pipelines.values()
    ]


@api.get("/pipelines/{pipeline_id}")
def get_pipelines(pipeline_id: str):
    pipeline = orchestrator.get_pipeline(pipeline_id)
    return _serialize_pipeline(pipeline)


@api.get("/pipelines/{pipeline_id}/input-schema")
def get_pipeline_input_schema(pipeline_id: str):
    pipeline = orchestrator.get_pipeline(pipeline_id)
    return pipeline.params.schema() if pipeline.params else dict()


@api.get("/pipelines/{pipeline_id}/triggers/{trigger_id}/runs")
def get_runs(pipeline_id: str, trigger_id: str):
    return list_pipeline_runs(pipeline_id, trigger_id)


@api.get("/pipelines/{pipeline_id}/triggers/{trigger_id}/runs/{run_id}")
def get_run(pipeline_id: str, trigger_id: str, run_id: int):
    return get_pipeline_run(run_id)


@api.get("/pipelines/{pipeline_id}/triggers/{trigger_id}/runs/{run_id}/logs")
def get_logs(pipeline_id: str, trigger_id: str, run_id: int):
    return get_pipeline_run_logs(PipelineRun(pipeline_id=pipeline_id, id=run_id))


@api.get("/pipelines/{pipeline_id}/triggers/{trigger_id}/runs/{run_id}/data/{task}")
def get_data(pipeline_id: str, trigger_id: str, run_id: int, task: str):
    return get_pipeline_run_data(PipelineRun(pipeline_id=pipeline_id, id=run_id), task)


@api.post("/pipelines/{pipeline_id}/triggers/{trigger_id}/run")
async def run_trigger(pipeline_id: str, trigger_id: str):
    pipeline = orchestrator.get_pipeline(pipeline_id)

    triggers = [trigger for trigger in pipeline.triggers if trigger.id == trigger_id]

    if len(triggers) == 0:
        raise HTTPException(status_code=404, detail=f"Trigger {trigger_id} not found")

    trigger = triggers[0]

    executor: AsyncIOExecutor = orchestrator.scheduler._lookup_executor("default")
    executor.submit_job(
        Job(
            orchestrator.scheduler,
            id=f"{pipeline.uuid}: {trigger.id}",
            func=run,
            args=[],
            kwargs={"pipeline": pipeline, "trigger": trigger},
            max_instances=1,
            misfire_grace_time=None,
            trigger=DateTrigger(),
        ),
        [datetime.now()],
    )


@api.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


app.mount("/", SPAStaticFiles(directory=FRONTEND_FOLDER, html=True))
