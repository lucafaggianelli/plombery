import { Icon } from '@tremor/react'

import { PipelineRunStatus } from '@/types'
import { STATUS_COLORS, STATUS_ICONS } from '@/utils'

export default function TaskRunStatusIcon({
  status,
}: {
  status?: PipelineRunStatus
}) {
  return (
    <Icon
      variant="light"
      icon={STATUS_ICONS[status || 'pending']}
      color={STATUS_COLORS[status || 'pending']}
    />
  )
}
