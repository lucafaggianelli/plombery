import { Button, Card, Metric, Title } from '@tremor/react'
import { TableCellsIcon } from '@heroicons/react/24/outline'
import { useState } from 'react'

import StatusBadge from './StatusBadge'
import TaskRunStatusIcon from './TaskRunStatusIcon'
import TimeRange from './TimeRange'
import { PipelineRunStatus, Task, TaskRun } from '@/types'
import {
  areMappedRuns,
  countByStatus,
  formatDuration,
  formatTime,
  getMappingLabel,
  getTaskRunsStatus,
  getTaskRunsTimeSpan,
  getTaskRunsWallClock,
  isMappedRun,
} from '@/utils'
import Timer from './Timer'
import DataViewerDialog from './DataViewerDialog'

interface Props {
  /** Missing if the pipeline changed since this run and no longer has the task */
  task?: Task
  taskId: string
  runs: TaskRun[]
  /** The status of the pipeline run, to tell a pending task from a skipped one */
  runStatus: PipelineRunStatus
}

function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="mt-4">
      <div className="text-xs mb-1">{title}</div>
      {children}
    </div>
  )
}

/**
 * The tasks a task is wired to, so the dependencies are readable without
 * tracing the edges back through the graph.
 */
function TaskIdsList({ title, ids }: { title: string; ids: string[] }) {
  if (!ids.length) {
    return null
  }

  return (
    <Section title={title}>
      <div className="flex flex-wrap gap-1">
        {[...ids].sort().map((id) => (
          <span
            key={id}
            className="font-mono text-xs px-1.5 py-0.5 rounded bg-tremor-background-subtle dark:bg-dark-tremor-background-subtle"
          >
            {id}
          </span>
        ))}
      </div>
    </Section>
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
    <Section title="Instances">
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
    </Section>
  )
}

export default function TaskRunDetails({
  task,
  taskId,
  runs,
  runStatus,
}: Props) {
  const [outputRun, setOutputRun] = useState<TaskRun | undefined>()

  const firstRun = runs[0]

  // A task is mapped when its runs carry an index, not when there is more than
  // one of them: a fan out over a single item still produces one instance.
  // The pipeline definition has the last word, as a task can be declared as
  // mapped before it has produced any instance at all.
  const isMapped = !!task?.mapping_mode || areMappedRuns(runs)

  const status = runs.length ? getTaskRunsStatus(runs) : 'pending'
  const { start, end } = getTaskRunsTimeSpan(runs)
  const wallClock = getTaskRunsWallClock(runs)
  const statusCounts = countByStatus(runs)
  const mappingLabel = getMappingLabel(task) || (isMapped ? 'Mapped' : '')

  const dependencies = (
    <>
      <TaskIdsList title="Upstream" ids={task?.upstream_task_ids ?? []} />
      <TaskIdsList title="Downstream" ids={task?.downstream_task_ids ?? []} />
    </>
  )

  return (
    <Card className="p-3 max-w-[350px] max-h-[460px] overflow-y-auto">
      <DataViewerDialog
        runId={outputRun?.id || ''}
        taskId={outputRun?.task_output_id || ''}
        open={!!outputRun}
        onClose={() => setOutputRun(undefined)}
      />

      <header className="flex items-start gap-4 justify-between">
        <div className="min-w-0">
          <Title className="truncate" title={task?.name ?? taskId}>
            {task?.name ?? taskId}
          </Title>

          <p className="font-mono text-xs truncate text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
            {taskId}
            {/* The index only belongs here when the panel shows a single
                instance, the list below carries it otherwise */}
            {runs.length === 1 &&
              isMappedRun(firstRun) &&
              `[${firstRun.map_index}]`}
          </p>
        </div>

        <StatusBadge status={status} />
      </header>

      {task?.description && (
        <p className="mt-2 text-sm text-tremor-content dark:text-dark-tremor-content">
          {task.description}
        </p>
      )}

      {mappingLabel && (
        <div className="mt-2 text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
          {mappingLabel}
        </div>
      )}

      {!runs.length ? (
        <>
          <p className="mt-4 text-sm text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
            {['pending', 'running'].includes(runStatus)
              ? 'Waiting for its upstream tasks to complete.'
              : 'This task never ran in this pipeline run.'}
          </p>

          {dependencies}
        </>
      ) : (
        <>
          <div className="mt-4">
            <div className="text-xs">
              {isMapped && runs.length > 1 ? 'Total duration' : 'Duration'}
            </div>

            <Metric className="tabular-nums text-lg">
              {status === 'running' && start ? (
                <Timer startTime={start} />
              ) : wallClock !== undefined ? (
                formatDuration(wallClock)
              ) : (
                formatDuration(firstRun.duration)
              )}
            </Metric>

            {isMapped && (
              <div className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                {runs.length} {runs.length === 1 ? 'instance' : 'instances'}
                {runs.length > 1 && (
                  <>
                    ,{' '}
                    {Object.entries(statusCounts)
                      .map(([name, count]) => `${count} ${name}`)
                      .join(', ')}
                  </>
                )}
              </div>
            )}
          </div>

          <div className="mt-4">
            <TimeRange
              start={start}
              end={end}
              startLabel={
                isMapped && runs.length > 1 ? 'First started at' : 'Started at'
              }
              endLabel={
                isMapped && runs.length > 1 ? 'Last finished at' : 'Finished at'
              }
            />
          </div>

          {isMapped && runs.length > 1 ? (
            <InstancesList runs={runs} onViewOutput={setOutputRun} />
          ) : (
            <OutputButton run={firstRun} onView={setOutputRun} />
          )}

          {dependencies}
        </>
      )}
    </Card>
  )
}
