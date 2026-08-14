import { Button, Card, Metric, Title } from '@tremor/react'
import { isSameDay } from 'date-fns'
import { TableCellsIcon } from '@heroicons/react/24/outline'
import { useState } from 'react'

import StatusBadge from './StatusBadge'
import TaskRunStatusIcon from './TaskRunStatusIcon'
import { Task, TaskRun } from '@/types'
import {
  countByStatus,
  formatDate,
  formatDuration,
  formatTime,
  getTaskRunsStatus,
  getTaskRunsWallClock,
} from '@/utils'
import Timer from './Timer'
import DataViewerDialog from './DataViewerDialog'

interface Props {
  task?: Task
  runs: TaskRun[]
}

const MAPPING_MODE_LABELS: Record<string, string> = {
  fan_out: 'Fan out',
  chained_fan_out: 'Chained fan out',
}

function Times({ run }: { run: TaskRun }) {
  return (
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
  )
}

function OutputButton({
  run,
  onView,
}: {
  run: TaskRun
  onView: (run: TaskRun) => void
}) {
  if (!run.task_output_id) {
    return null
  }

  return (
    <Button
      variant="secondary"
      color="indigo"
      size="xs"
      icon={TableCellsIcon}
      onClick={() => onView(run)}
      className="w-full mt-4"
    >
      View output data
    </Button>
  )
}

/**
 * One row per mapped instance, so that every instance of a fan out is
 * reachable: its status, how long it took and its own output.
 */
function InstancesList({
  runs,
  onViewOutput,
}: {
  runs: TaskRun[]
  onViewOutput: (run: TaskRun) => void
}) {
  const sorted = [...runs].sort(
    (a, b) => (a.map_index ?? 0) - (b.map_index ?? 0)
  )

  return (
    <div className="mt-4">
      <div className="text-xs mb-1">Instances</div>

      <ul className="max-h-64 overflow-y-auto divide-y divide-tremor-border dark:divide-dark-tremor-border">
        {sorted.map((run) => (
          <li
            key={run.id}
            className="flex items-center gap-2 py-1.5 text-sm"
            title={
              run.start_time ? `Started at ${formatTime(run.start_time)}` : ''
            }
          >
            <TaskRunStatusIcon status={run.status} />

            <span className="tabular-nums text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
              [{run.map_index ?? 0}]
            </span>

            <span className="tabular-nums grow text-right">
              {run.status === 'running' && run.start_time ? (
                <Timer startTime={run.start_time} />
              ) : (
                formatDuration(run.duration)
              )}
            </span>

            {run.task_output_id ? (
              <button
                type="button"
                title="View output data"
                onClick={() => onViewOutput(run)}
                className="text-tremor-brand hover:text-tremor-brand-emphasis dark:text-dark-tremor-brand dark:hover:text-dark-tremor-brand-emphasis"
              >
                <TableCellsIcon className="size-4" />
              </button>
            ) : (
              <span className="size-4" />
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function TaskRunDetails({ task, runs }: Props) {
  const [outputRun, setOutputRun] = useState<TaskRun | undefined>()

  const firstRun = runs[0]

  if (!firstRun) {
    return null
  }

  // A task is mapped when its runs carry an index, not when there is more than
  // one of them: a fan out over a single item still produces one instance.
  const isMapped = runs.some((run) => run.map_index !== undefined)

  const status = getTaskRunsStatus(runs)
  const wallClock = getTaskRunsWallClock(runs)
  const statusCounts = countByStatus(runs)

  return (
    <Card className="p-3 max-w-[350px]">
      <DataViewerDialog
        runId={outputRun?.id || ''}
        taskId={outputRun?.task_output_id || ''}
        open={!!outputRun}
        onClose={() => setOutputRun(undefined)}
      />

      <header className="flex items-start gap-4 justify-between">
        <Title className="mb-4">
          {firstRun.task_id}
          {isMapped && !task?.mapping_mode && `[${firstRun.map_index ?? 0}]`}
        </Title>
        <StatusBadge status={status} />
      </header>

      {task?.mapping_mode && (
        <div className="mb-4 text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
          {MAPPING_MODE_LABELS[task.mapping_mode] ?? task.mapping_mode}
          {task.map_upstream_id && <> over {task.map_upstream_id}</>}
        </div>
      )}

      <div>
        <div className="text-xs">
          {isMapped && runs.length > 1 ? 'Total duration' : 'Duration'}
        </div>
        <Metric className="tabular-nums text-lg">
          {status === 'running' && firstRun.start_time ? (
            <Timer startTime={firstRun.start_time} />
          ) : wallClock !== undefined ? (
            formatDuration(wallClock)
          ) : (
            formatDuration(firstRun.duration)
          )}
        </Metric>

        {isMapped && runs.length > 1 && (
          <div className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
            {runs.length} instances,{' '}
            {Object.entries(statusCounts)
              .map(([name, count]) => `${count} ${name}`)
              .join(', ')}
          </div>
        )}
      </div>

      {isMapped && runs.length > 1 ? (
        <InstancesList runs={runs} onViewOutput={setOutputRun} />
      ) : (
        <>
          <Times run={firstRun} />
          <OutputButton run={firstRun} onView={setOutputRun} />
        </>
      )}
    </Card>
  )
}
