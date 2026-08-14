import { Card, Metric, Title } from '@tremor/react'

import StatusBadge from './StatusBadge'
import { Pipeline, PipelineRun } from '@/types'
import { formatDate, formatDateTime, formatDuration, formatTime } from '@/utils'
import Timer from './Timer'
import { addMilliseconds, isSameDay } from 'date-fns'

interface Props {
  pipeline: Pipeline
  run: PipelineRun
}

export default function PipelineRunDetails({ pipeline, run }: Props) {
  return (
    <Card className="p-3 max-w-[350px]">
      <header className="flex items-start gap-4 justify-between">
        <Title className="mb-4">{pipeline.name}</Title>
        <StatusBadge status={run.status} />
      </header>

      <div>
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
      </div>

      <div className="space-y-4 mt-4">
        <div>
          <div className="text-xs">Started at</div>

          <div className="flex gap-2 justify-between">
            <p className="tabular-nums">
              {run.start_time ? formatTime(run.start_time) : '-'}
            </p>
            <p>{run.end_time ? formatDate(run.end_time) : '-'}</p>
          </div>
        </div>

        <div>
          <div className="text-xs">Finished at</div>

          <p className="tabular-nums">
            {run.end_time ? formatTime(run.end_time) : '-'}
          </p>

          {run.start_time &&
            run.end_time &&
            !isSameDay(run.start_time, run.end_time) && (
              <p>{formatDate(run.end_time)}</p>
            )}
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
              {pipeline.version && run.pipeline_version !== pipeline.version && (
                <span className="ml-2 text-xs text-amber-600 dark:text-amber-500">
                  outdated
                </span>
              )}
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}
