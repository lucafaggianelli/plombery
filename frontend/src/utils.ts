import {
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  NoSymbolIcon,
  StopCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline'
import { Color } from '@tremor/react'
import { format } from 'date-fns'

import { PipelineRunStatus, Task } from './types'

type ExtendedStatus = PipelineRunStatus | 'warning' | 'notrun'

export const STATUS_COLORS: Record<ExtendedStatus, Color> = {
  completed: 'emerald',
  failed: 'rose',
  cancelled: 'slate',
  running: 'blue',
  notrun: 'slate',
  warning: 'amber',
}

export const STATUS_ICONS: Record<ExtendedStatus, React.ElementType<any>> = {
  completed: CheckCircleIcon,
  failed: XCircleIcon,
  cancelled: StopCircleIcon,
  running: ArrowPathIcon,
  notrun: NoSymbolIcon,
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

export const formatDateTime = (date: Date) =>
  format(date, 'd MMM yyyy HH:mm:ss (XXX)')

export const formatTimestamp = (date: Date) =>
  format(date, 'HH:mm:ss.SSS')
