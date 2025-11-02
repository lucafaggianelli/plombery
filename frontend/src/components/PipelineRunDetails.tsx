import { Card, Metric } from '@tremor/react'

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
  const runEndTime = addMilliseconds(run.start_time, run.duration)

  return (
    <Card className="p-3">
      <div className="flex items-start">
        <div className="text-xs">Duration</div>
        <StatusBadge status={run.status} />
      </div>

      <div className="flex justify-start items-baseline space-x-3 truncate">
        <Metric className="tabular-nums text-lg">
          {run.status !== 'running' ? (
            formatDuration(run.duration)
          ) : (
            <Timer startTime={run.start_time} />
          )}
        </Metric>
      </div>

      <div className="flex items-start mt-2 gap-4">
        <div>
          <p
            className="font-medium"
            title={formatDateTime(run.start_time, true)}
          >
            {formatTime(run.start_time)}
          </p>

          <p className="mt-1">{formatDate(run.start_time)}</p>
        </div>

        <div className="text-right">
          <p className="font-medium" title={formatDateTime(runEndTime, true)}>
            {formatTime(runEndTime)}
          </p>

          {!isSameDay(run.start_time, runEndTime) && (
            <p>{formatDate(runEndTime)}</p>
          )}
        </div>
      </div>
    </Card>
  )
}
