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

  const mapping_index = runs.length > 1 ? `[${run.map_index}]` : ''

  return (
    <Card className="p-3 max-w-[350px]">
      <DataViewerDialog
        runId={run.id}
        taskId={viewDataDialog || ''}
        open={!!viewDataDialog}
        onClose={() => setViewDataDialog(undefined)}
      />

      <header className="flex items-start gap-4 justify-between">
        <Title className="mb-4">
          {run.task_id}
          {mapping_index}
        </Title>
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
      </div>

      {run?.task_output_id && (
        <Button
          variant="secondary"
          color="indigo"
          size="xs"
          icon={TableCellsIcon}
          onClick={() => setViewDataDialog(run.task_output_id)}
          className="w-full mt-4"
        >
          View output data
        </Button>
      )}
    </Card>
  )
}
