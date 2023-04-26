from typing import Any
import asyncio
from pathlib import Path
import tempfile
from time import time

from pydantic import BaseModel

from mario.orchestrator.data_storage import BASE_DATA_PATH
from mario.pipeline.pipeline import Pipeline
from mario.config import settings


D2_PATH = r"C:\Users\LQ6211\Downloads\d2.exe"
NEW_LINE = "\n"


async def _build_d2_graph(source: str, output_file: str) -> bool:
    f = tempfile.TemporaryFile(suffix=".d2", encoding="utf-8", mode="w", delete=False)

    f.write(source)
    f.close()

    output_file_path = BASE_DATA_PATH / "assets" / f"{output_file}.svg"

    proc = await asyncio.create_subprocess_shell(
        f"{D2_PATH} --layout elk {f.name} {output_file_path}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    success = proc.returncode == 0

    if not success:
        print("Error creating D2 graph", stderr.decode("utf-8"))
        print(f"See the source file at: {f.name}")
    else:
        Path(f.name).unlink()

    return success


def _pydantic_to_d2_uml(model: BaseModel, pipeline_name: str):
    schema = model.schema()
    params_name = schema.get("title", model.__name__)

    model_uml = []

    for key, prop in schema["properties"].items():
        model_uml.append(f'{key}: {prop.get("type", "Any")}')

    model_uml = f"""{params_name}: {{
        shape: class

        {NEW_LINE.join(model_uml)}
    }}"""

    return [
        model_uml,
        f"""{params_name} -> {pipeline_name}: params {{
            target-arrowhead.shape: diamond
        }}""",
    ]


async def build_pipeline_graph(pipeline: Pipeline):
    graph = ["direction: down"]

    if pipeline.params:
        graph.extend(_pydantic_to_d2_uml(pipeline.params, pipeline.name))

    # Generate tasks connected one to another
    connections = []
    for i, task in enumerate(pipeline.tasks):
        if task.description:
            connections.append(f"""{task.name} {{
                description: ||md
                    {task.description}
                ||
            }}""")
        else:
            connections.append(task.name)

        if i == len(pipeline.tasks) - 1:
            continue

        next_task = pipeline.tasks[i + 1]
        return_type = task.run.__annotations__.get("return", Any).__name__

        connections.append(f"{task.name} -> {next_task.name}: {return_type}")

    # Add tasks within the pipeline container
    graph.append(
        f"""{pipeline.name}: {{
            {NEW_LINE.join(connections)}
        }}"""
    )

    # Generate triggers
    triggers_graphs = []

    triggers_graphs.append(
        f"""Pipeline trigger: {{
        HTTP webhook: {{
                code: |md
                    ```
                    POST {settings.server_url}/api/pipelines/{pipeline.id}/run
                    ```
                |
                style {{
                    stroke-width: 0
                }}
            }}

            Manual run: {{
                link: {settings.frontend_url}/pipelines/{pipeline.id}/triggers/_manual
                icon: https://icons.terrastruct.com/tech%2Flaptop.svg
                style {{
                    stroke-width: 0
                }}
            }}
    }}"""
    )

    for trigger in pipeline.triggers:
        trigger_graphs = []

        if trigger.aps_trigger:
            trigger_graphs.append(
                f"""Schedule: {{
                    schedule_expr: |md
                        {trigger.aps_trigger}
                    |
                    icon: https://icons.terrastruct.com/essentials%2F226-alarm%20clock.svg
                    style {{
                        stroke-width: 0
                    }}
                }}"""
            )

        trigger_graphs.append(
            f"""HTTP webhook: {{
                    code: |md
                        ```
                        POST {settings.server_url}/api/pipelines/{pipeline.id}/triggers/{trigger.id}/run
                        ```
                    |
                    style {{
                        stroke-width: 0
                    }}
                }}

                Manual run: {{
                    link: {settings.frontend_url}/pipelines/{pipeline.id}/triggers/daily
                    icon: https://icons.terrastruct.com/tech%2Flaptop.svg
                    style {{
                        stroke-width: 0
                    }}
                }}"""
        )

        triggers_graphs.append(
            f"""{trigger.name}: {{
            {NEW_LINE.join(trigger_graphs)}
        }}"""
        )

    # Generate triggers container
    graph.append(f"""Triggers {{
        {NEW_LINE.join(triggers_graphs)}

        style {{
            stroke-dash: 5
            border-radius: 3
            fill: transparent
        }}
    }}""")

    # Connect triggers to pipeline
    graph.append(f"Triggers -> {pipeline.name}")

    t0 = time()
    await _build_d2_graph(NEW_LINE.join(graph), pipeline.id)
    print(f"Created {pipeline.id} graph in {time() - t0} s")
