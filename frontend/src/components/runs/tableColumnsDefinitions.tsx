import { ColumnDef, createColumnHelper } from '@tanstack/table-core'
import { formatDistanceToNow, differenceInDays } from 'date-fns'

import StatusBadge from '@/components/StatusBadge'
import Timer from '@/components/Timer'
import { formatDateTime } from '@/utils'
import { PipelineRun } from '@/types'
import { Link } from 'react-router-dom'

const columnHelper = createColumnHelper<PipelineRun>()

export const columns: ColumnDef<PipelineRun, any>[] = [
  columnHelper.accessor('id', {
    header: () => <div className="text-right">#</div>,
    cell: ({ getValue }) => <div className="text-right">{getValue()}</div>,
  }),
  columnHelper.accessor('status', {
    header: 'Status',
    cell: ({ getValue }) => <StatusBadge status={getValue()} />,
  }),
  columnHelper.accessor('pipeline_id', {
    header: 'Pipeline',
    cell: ({ getValue }) => (
      <Link
        to={`/pipelines/${getValue()}`}
        className="link--arrow"
        title="View pipeline details"
        onClick={(event) => event.stopPropagation()}
      >
        {getValue()}
      </Link>
    ),
  }),
  columnHelper.accessor('trigger_id', {
    header: 'Trigger',
    cell: ({ row }) => (
      <Link
        to={`/pipelines/${row.original.pipeline_id}/triggers/${row.original.trigger_id}`}
        className="link--arrow"
        title="View trigger details"
        onClick={(event) => event.stopPropagation()}
      >
        {row.original.trigger_id}
      </Link>
    ),
  }),
  columnHelper.accessor('start_time', {
    header: 'Started at',
    cell: ({ getValue }) =>
      differenceInDays(new Date(), getValue()) <= 1
        ? formatDistanceToNow(getValue(), {
            addSuffix: true,
            includeSeconds: true,
          })
        : formatDateTime(getValue()),
  }),
  columnHelper.accessor('duration', {
    header: () => <div className="text-right">Duration</div>,
    cell: ({ row }) => (
      <div className="text-right">
        {row.original.status !== 'running' ? (
          (row.original.duration / 1000).toFixed(2)
        ) : (
          <Timer startTime={row.original.start_time} />
        )}{' '}
        s
      </div>
    ),
  }),
]
