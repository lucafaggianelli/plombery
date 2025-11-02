import { Button, Card, Metric, Title } from '@tremor/react'
import { addMilliseconds, isSameDay } from 'date-fns'

import StatusBadge from './StatusBadge'
import { Pipeline, TaskRun } from '@/types'
import { formatDate, formatDateTime, formatDuration, formatTime } from '@/utils'
import Timer from './Timer'
import DataViewerDialog from './DataViewerDialog'
import { TableCellsIcon } from '@heroicons/react/24/outline'
import { useState } from 'react'

interface Props {
  pipeline: Pipeline
  runs: TaskRun[]
}

export default function TaskRunDetails({ pipeline, runs }: Props) {
  const [viewDataDialog, setViewDataDialog] = useState<string | undefined>()

  const run = runs[0]

  const runEndTime = addMilliseconds(run.start_time, run.duration)
  const mapping_index = runs.length > 1 ? `[${run.map_index}]` : ''

  return (
    <Card className="p-3">
      <DataViewerDialog
        runId={run.id}
        taskId={viewDataDialog || ''}
        open={!!viewDataDialog}
        onClose={() => setViewDataDialog(undefined)}
      />

      <Title>
        {run.task_id}
        {mapping_index}
      </Title>

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

      {run?.task_output_id && (
        <Button
          variant="light"
          color="indigo"
          size="xs"
          icon={TableCellsIcon}
          tooltip="View task output data"
          onClick={() => setViewDataDialog(run.task_output_id)}
        >
          View data
        </Button>
      )}
    </Card>
  )
}
