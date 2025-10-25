import { Badge } from '@tremor/react'

import { PipelineRunStatus } from '@/types'
import { STATUS_COLORS, STATUS_ICONS } from '@/utils'

interface Props {
  status: PipelineRunStatus
}

const StatusBadge: React.FC<Props> = ({ status }) => (
  <Badge
    color={STATUS_COLORS[status]}
    icon={STATUS_ICONS[status]}
    className="rounded-full cursor-[inherit]"
  >
    {status}
  </Badge>
)

export default StatusBadge
