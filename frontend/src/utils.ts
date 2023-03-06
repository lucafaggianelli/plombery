import { Color } from '@tremor/react'
import dayjs from 'dayjs'

import { PipelineRunStatus } from './types'

export const STATUS_COLORS: Record<PipelineRunStatus, Color> = {
  completed: 'emerald',
  failed: 'rose',
  cancelled: 'gray',
  running: 'blue',
}

export const formatDateTime = (date: Date) =>
  dayjs(date).format('D MMM YYYY HH:mm:ss (Z[Z])')
