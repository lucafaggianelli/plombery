import { isSameDay } from 'date-fns'

import { formatDate, formatTime } from '@/utils'

interface Props {
  start?: Date
  end?: Date
  /** Labels, so that a mapped task can say "First started"/"Last finished" */
  startLabel?: string
  endLabel?: string
}

/**
 * The start and end of a run, showing the date only when it adds something:
 * next to the start time, and again on the end time if it fell on another day.
 */
export default function TimeRange({
  start,
  end,
  startLabel = 'Started at',
  endLabel = 'Finished at',
}: Props) {
  return (
    <div className="space-y-4">
      <div>
        <div className="text-xs">{startLabel}</div>

        <div className="flex gap-2 justify-between">
          <p className="tabular-nums">{start ? formatTime(start) : '-'}</p>
          <p>{start ? formatDate(start) : ''}</p>
        </div>
      </div>

      <div>
        <div className="text-xs">{endLabel}</div>

        <p className="tabular-nums">{end ? formatTime(end) : '-'}</p>

        {start && end && !isSameDay(start, end) && <p>{formatDate(end)}</p>}
      </div>
    </div>
  )
}
