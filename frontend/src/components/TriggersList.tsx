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
    <Card>
      <Title>Triggers</Title>

      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Name</TableHeaderCell>
            <TableHeaderCell>Interval</TableHeaderCell>
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
                <Text>{trigger.aps_trigger}</Text>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  )
}

export default TriggersList
