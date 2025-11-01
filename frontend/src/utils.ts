import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  StopCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline'
import { Color } from '@tremor/react'
import { format, addMinutes, intervalToDuration } from 'date-fns'

import { PipelineRunStatus, Task } from './types'
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
  cancelled: StopCircleIcon,
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
