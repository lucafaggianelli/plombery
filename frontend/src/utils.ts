import {
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  NoSymbolIcon,
  StopCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline'
import { Color } from '@tremor/react'
import dayjs from 'dayjs'

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

const TASKS_COLORS: Color[] = ['cyan', 'violet', 'pink']

export const getTasksColors = (tasks: Task[]) => {
  return Object.fromEntries(
    tasks.map((task, i) => [
      task.id,
      `bg-${TASKS_COLORS[i % TASKS_COLORS.length]}-500`,
    ])
  )
}

export const formatDateTime = (date: Date) =>
  dayjs(date).format('D MMM YYYY HH:mm:ss (Z[Z])')

export const formatTimestamp = (date: Date) =>
  dayjs(date).format('HH:mm:ss.SSS')
