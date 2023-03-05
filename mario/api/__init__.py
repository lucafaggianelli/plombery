import asyncio
from datetime import datetime
import json
from time import sleep

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.events import (
    JobEvent,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_SUBMITTED,
)

from mario.orchestrator import orchestrator
from mario.pipeline.pipeline import Pipeline, Trigger
from mario.orchestrator.executor import get_pipeline_run_logs, get_pipeline_run_data
from mario.database.models import PipelineRun
from mario.database.repository import (
    list_pipeline_runs,
    get_latest_pipeline_run,
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
        name=trigger.name,
        interval=str(trigger.aps_trigger),
        next_fire_time=trigger.aps_trigger.get_next_fire_time(
            datetime.now(), datetime.now()
        ),
        paused=trigger.paused,
    )


def _serialize_pipeline(pipeline: Pipeline):
    return dict(
        id=pipeline.uuid,
        name=pipeline.uuid,
        tasks=[task.uuid for task in pipeline.tasks],
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
    print("------", pipeline_id, pipeline)
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


@api.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def _on_job_completed(event: JobEvent):
    pipeline = orchestrator.get_pipeline_from_job_id(event.job_id)
    trigger = orchestrator.get_trigger_from_job_id(event.job_id)

    sleep(0.5)

    status = None

    if event.code == EVENT_JOB_EXECUTED:
        status = "success"
    elif event.code == EVENT_JOB_ERROR:
        status = "fail"
    elif event.code == EVENT_JOB_SUBMITTED:
        status = "new"
    else:
        print("Unhandled job event", event)

    # if status == "new":
    #     run = dict(
    #         id=0,
    #         status=status,
    #         start_time=datetime.now().isoformat(),
    #         duration=0,
    #     )
    # else:
    run = get_latest_pipeline_run(pipeline.uuid, trigger.name)
    run = dict(
        id=run.id,
        status=run.status,
        start_time=run.start_time.isoformat(),
        duration=run.duration,
    )

    awaitable = manager.broadcast(
        json.dumps(
            dict(
                type="run-update",
                data=dict(
                    run=run,
                    pipeline=pipeline.uuid,
                    trigger=trigger.name,
                ),
            )
        )
    )

    asyncio.ensure_future(awaitable)


orchestrator.scheduler.add_listener(
    _on_job_completed,
    EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_SUBMITTED,
)

app.mount("/", SPAStaticFiles(directory=FRONTEND_FOLDER, html=True))
