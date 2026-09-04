import { Metric, Title } from '@tremor/react'

import StatusBadge from './StatusBadge'
import TimeRange from './TimeRange'
import Timer from './Timer'
import { MANUAL_TRIGGER } from '@/constants'
import { Pipeline, PipelineRun } from '@/types'
import { countByStatus, formatDuration } from '@/utils'

interface Props {
  pipeline: Pipeline
  run: PipelineRun
}

const RUN_REASONS: Record<string, string> = {
  scheduled: 'by its schedule',
  web: 'from the web UI',
  api: 'via the API',
}

export default function PipelineRunDetails({ pipeline, run }: Props) {
  const trigger =
    run.trigger_id === MANUAL_TRIGGER.id
      ? MANUAL_TRIGGER
      : pipeline.triggers.find((trigger) => trigger.id === run.trigger_id)

  // Every instance of a mapped task counts here: the interesting number while
  // a run is going is how much work is left, not how many tasks are declared
  const taskStatusCounts = countByStatus(run.task_runs)
  const completedTaskRuns = taskStatusCounts.completed ?? 0

  return (
    <>
      <header className="flex items-start gap-4 justify-between">
        <div className="min-w-0">
          <Title className="truncate" title={pipeline.name}>
            {pipeline.name}
          </Title>

          <p className="font-mono text-xs truncate text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
            Run #{run.id}
          </p>
        </div>

        <StatusBadge status={run.status} />
      </header>

      <div className="mt-4">
        <div className="text-xs">Duration</div>
        <Metric className="tabular-nums text-lg">
          {run.status !== 'running' ? (
            formatDuration(run.duration)
          ) : run.start_time ? (
            <Timer startTime={run.start_time} />
          ) : (
            '-'
          )}
        </Metric>

        {run.task_runs.length > 0 && (
          <div className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
            {completedTaskRuns} of {run.task_runs.length} task runs completed
          </div>
        )}
      </div>

      <div className="space-y-4 mt-4">
        <TimeRange start={run.start_time} end={run.end_time} />

        <div>
          <div className="text-xs">Triggered</div>

          <p className="truncate" title={run.trigger_id}>
            {trigger?.name ?? run.trigger_id}
            {run.reason && (
              <span className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                {' '}
                {RUN_REASONS[run.reason] ?? run.reason}
              </span>
            )}
          </p>
        </div>

        {run.pipeline_version && (
          <div>
            <div className="text-xs">Pipeline version</div>

            <p
              className="font-mono text-sm truncate"
              title={
                run.pipeline_version === pipeline.version
                  ? 'Matches the pipeline as it is defined now'
                  : 'The pipeline has changed since this run'
              }
            >
              {run.pipeline_version}
              {pipeline.version &&
                run.pipeline_version !== pipeline.version && (
                  <span className="ml-2 text-xs text-amber-600 dark:text-amber-500">
                    outdated
                  </span>
                )}
            </p>
          </div>
        )}
      </div>

      <p className="mt-4 text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
        Select a node to see its details
      </p>
    </>
  )
}
