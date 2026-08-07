import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  XCircleIcon,
  NoSymbolIcon,
} from '@heroicons/react/24/outline'
import { Color } from '@tremor/react'
import { format, addMinutes, intervalToDuration } from 'date-fns'

import { PipelineRunStatus, Task, TaskRun } from './types'
import { RunningIcon } from './components/RunningIcon'

type ExtendedStatus = PipelineRunStatus | 'warning'

export const STATUS_COLORS: Record<ExtendedStatus, Color> = {
  pending: 'slate',
  completed: 'emerald',
  failed: 'rose',
  cancelled: 'slate',
  running: 'blue',
  warning: 'amber',
}

export const STATUS_ICONS: Record<ExtendedStatus, React.ElementType<any>> = {
  pending: ClockIcon,
  completed: CheckCircleIcon,
  failed: XCircleIcon,
  cancelled: NoSymbolIcon,
  running: RunningIcon,
  warning: ExclamationTriangleIcon,
}

export const TASKS_COLORS: Color[] = [
  'cyan',
  'violet',
  'pink',
  'emerald',
  'orange',
  'stone',
  'fuchsia',
]

export const getTasksColors = (tasks: Task[]) => {
  return Object.fromEntries(
    tasks.map((task, i) => [
      task.id,
      `bg-${TASKS_COLORS[i % TASKS_COLORS.length]}-500`,
    ])
  )
}

export const formatDateTime = (date: Date, utc: boolean = false): string => {
  if (utc) {
    const finalDate = addMinutes(date, date.getTimezoneOffset())
    return format(finalDate, 'd MMM yyyy HH:mm:ss') + ' (UTC)'
  } else {
    return format(date, 'd MMM yyyy HH:mm:ss (XXX)')
  }
}

export const formatTime = (date: Date, utc: boolean = false) => {
  if (utc) {
    const finalDate = addMinutes(date, date.getTimezoneOffset())
    return format(finalDate, 'HH:mm:ss.SSS') + ' (UTC)'
  } else {
    return format(date, 'HH:mm:ss.SSS')
  }
}

export const formatDate = (date: Date) => format(date, 'd MMM yyyy')

const numberFormatter = new Intl.NumberFormat()

export const formatNumber = (value: number) => numberFormatter.format(value)

export const formatDuration = (durationMs: number) => {
  const parts = intervalToDuration({ start: 0, end: durationMs })
  const ms = durationMs % 1000

  return [
    parts.hours && `${parts.hours}h`,
    (parts.minutes || parts.hours) && `${parts.minutes || 0}m`,
    (parts.seconds || parts.minutes || parts.hours) &&
      `${(parts.seconds || 0).toString().padStart(2, '0')}s`,
    ms && `${(ms || 0).toFixed().padStart(3, '0')}ms`,
  ]
    .filter(Boolean)
    .join(' ')
}

/**
 * The status of a task as a whole, from the status of its runs.
 *
 * A mapped task has one run per item, so it is only complete when every
 * instance is, and a single failed instance fails the task.
 */
export const getTaskRunsStatus = (taskRuns: TaskRun[]): PipelineRunStatus => {
  if (taskRuns.length === 0) {
    return 'pending'
  }

  if (taskRuns.every((taskRun) => taskRun.status === 'completed')) {
    return 'completed'
  }

  if (taskRuns.some((taskRun) => taskRun.status === 'failed')) {
    return 'failed'
  }

  if (taskRuns.some((taskRun) => taskRun.status === 'cancelled')) {
    return 'cancelled'
  }

  if (taskRuns.some((taskRun) => taskRun.status === 'running')) {
    return 'running'
  }

  if (taskRuns.some((taskRun) => taskRun.status === 'pending')) {
    return 'pending'
  }

  return 'running'
}

/**
 * How long a set of task runs took from the first start to the last end.
 *
 * Mapped instances run concurrently, so summing their durations overstates
 * the time the task actually took: this measures the wall clock instead.
 */
export const getTaskRunsWallClock = (taskRuns: TaskRun[]): number | undefined => {
  const startTimes = taskRuns
    .map((taskRun) => taskRun.start_time?.getTime())
    .filter((time): time is number => time !== undefined)

  const endTimes = taskRuns
    .map((taskRun) => taskRun.end_time?.getTime())
    .filter((time): time is number => time !== undefined)

  if (!startTimes.length || endTimes.length !== taskRuns.length) {
    // Still running, or never recorded a time: no meaningful total yet
    return undefined
  }

  return Math.max(...endTimes) - Math.min(...startTimes)
}

export const countByStatus = (
  taskRuns: TaskRun[]
): Partial<Record<PipelineRunStatus, number>> => {
  const counts: Partial<Record<PipelineRunStatus, number>> = {}

  for (const taskRun of taskRuns) {
    counts[taskRun.status] = (counts[taskRun.status] ?? 0) + 1
  }

  return counts
}
