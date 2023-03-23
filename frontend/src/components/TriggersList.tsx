import {
  Badge,
  Card,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  Text,
  Title,
} from '@tremor/react'
import { useNavigate } from 'react-router-dom'

import { Pipeline } from '@/types'
import { formatDateTime } from '@/utils'

interface Props {
  pipeline: Pipeline
}

const TriggersList: React.FC<Props> = ({ pipeline }) => {
  const navigate = useNavigate()

  return (
    <Card className="mt-5">
      <Title>Triggers</Title>

      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Name</TableHeaderCell>
            <TableHeaderCell>Interval</TableHeaderCell>
            <TableHeaderCell>Next fire time</TableHeaderCell>
            <TableHeaderCell>Latest Status</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {pipeline.triggers.map((trigger) => (
            <TableRow
              key={trigger.id}
              className="cursor-pointer hover:bg-slate-50 transition-colors"
              onClick={() =>
                navigate(`/pipelines/${pipeline.id}/triggers/${trigger.id}`)
              }
            >
              <TableCell>{trigger.name}</TableCell>
              <TableCell>
                <Text>{trigger.interval}</Text>
              </TableCell>
              <TableCell>
                {trigger.paused ? (
                  <Badge
                    color="amber"
                    tooltip="Re-enable the trigger setting paused=False"
                    size="xs"
                  >
                    Disabled
                  </Badge>
                ) : trigger.next_fire_time ? (
                  formatDateTime(trigger.next_fire_time)
                ) : (
                  '-'
                )}
              </TableCell>
              <TableCell>-</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  )
}

export default TriggersList
