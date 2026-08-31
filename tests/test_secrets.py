import pytest
from pydantic import SecretStr, ValidationError

from plombery import BaseSecrets


class WarehouseSecrets(BaseSecrets):
    WAREHOUSE_URI: SecretStr


def test_resolves_from_an_env_var_of_the_same_name(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WAREHOUSE_URI", "postgres://user:pass@host/db")

    secrets = WarehouseSecrets()

    assert secrets.WAREHOUSE_URI.get_secret_value() == "postgres://user:pass@host/db"


def test_value_is_masked_in_repr(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WAREHOUSE_URI", "postgres://user:pass@host/db")

    secrets = WarehouseSecrets()

    assert "pass" not in repr(secrets)
    assert "pass" not in str(secrets)


def test_a_missing_secret_fails_clearly(monkeypatch: pytest.MonkeyPatch):
    """A missing value must raise at construction, not resolve to None and
    fail later wherever the task happens to use it."""

    monkeypatch.delenv("WAREHOUSE_URI", raising=False)

    with pytest.raises(ValidationError):
        WarehouseSecrets()


@pytest.mark.asyncio
async def test_a_declared_secret_is_injected_into_the_task(
    app, monkeypatch: pytest.MonkeyPatch
):
    """A task argument annotated with a `BaseSecrets` subclass receives a
    validated instance, resolved from the environment, not upstream output."""

    from plombery import Pipeline, task
    from plombery.orchestrator import run_pipeline_now
    from plombery.database.repository import get_task_run_output_by_id
    from plombery.schemas import PipelineRunStatus

    from .conftest import wait_for_run

    monkeypatch.setenv("WAREHOUSE_URI", "postgres://user:pass@host/db")

    app.start()

    with Pipeline(id="secret_injection") as pipeline:

        @task
        def load(warehouse: WarehouseSecrets):
            # the argument's name is free: it's matched by its annotation
            return warehouse.WAREHOUSE_URI.get_secret_value()

    app.register_pipeline(pipeline)

    run = await wait_for_run((await run_pipeline_now(pipeline)).id)

    assert run.status == PipelineRunStatus.COMPLETED

    output = get_task_run_output_by_id(run.task_runs[0].task_output_id)
    assert output.data == "postgres://user:pass@host/db"


@pytest.mark.asyncio
async def test_a_missing_secret_is_stored_on_the_pipeline_at_startup(
    app, monkeypatch: pytest.MonkeyPatch
):
    """The secrets a registered pipeline needs are known from task signatures,
    so a missing one is recorded on the pipeline up front, scoped to the task
    that declares it, instead of surfacing only when the run fails."""

    from plombery import Pipeline, task, check_registered_pipelines

    monkeypatch.delenv("WAREHOUSE_URI", raising=False)

    app.start()

    with Pipeline(id="needs_secret") as pipeline:

        @task
        def load(warehouse: WarehouseSecrets):
            return warehouse.WAREHOUSE_URI.get_secret_value()

    check_registered_pipelines()

    assert pipeline.runnable is False
    assert len(pipeline.issues) == 1

    issue = pipeline.issues[0]
    assert issue.level == "error"
    assert issue.code == "missing_secret"
    assert issue.task_id == "load"
    assert "WAREHOUSE_URI" in issue.message


@pytest.mark.asyncio
async def test_a_pipeline_with_its_secrets_set_has_no_issues(
    app, monkeypatch: pytest.MonkeyPatch
):
    from plombery import Pipeline, task, check_registered_pipelines

    monkeypatch.setenv("WAREHOUSE_URI", "postgres://user:pass@host/db")

    app.start()

    with Pipeline(id="has_secret") as pipeline:

        @task
        def load(warehouse: WarehouseSecrets):
            return warehouse.WAREHOUSE_URI.get_secret_value()

    check_registered_pipelines()

    assert pipeline.issues == []
    assert pipeline.runnable is True


def test_a_secrets_annotated_argument_is_routed_to_injection():
    """A secrets-annotated argument is resolved by injection, kept out of the
    upstream-data arguments so it's never resolved from a task's output."""

    from plombery.orchestrator.executor import check_task_signature

    def load(rows, warehouse: WarehouseSecrets, params): ...

    signature = check_task_signature(load)

    assert signature.secret_args == {"warehouse": WarehouseSecrets}
    assert "warehouse" not in signature.input_arg_names
    assert "rows" in signature.input_arg_names
    assert signature.has_params_arg
