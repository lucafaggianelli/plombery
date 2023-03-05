import { Color } from '@tremor/react'
import dayjs from 'dayjs'

export const STATUS_COLORS: { [key: string]: Color } = {
  success: 'emerald',
  fail: 'rose',
  cancel: 'gray',
  warning: 'orange',
}

export const formatDateTime = (date: Date) =>
  dayjs(date).format('D MMM YYYY HH:mm:ss (Z[Z])')
