from typing import Dict

from plombery.schemas import PipelineRunStatus


_PIPELINE_STATUS_TO_VERB: Dict[PipelineRunStatus, str] = {
    PipelineRunStatus.RUNNING: "has started",
    PipelineRunStatus.COMPLETED: "has successfully completed",
    PipelineRunStatus.FAILED: "failed",
    PipelineRunStatus.CANCELLED: "was cancelled",
}


def get_pipeline_status_verb(run_status: PipelineRunStatus) -> str:
    return _PIPELINE_STATUS_TO_VERB[run_status]
