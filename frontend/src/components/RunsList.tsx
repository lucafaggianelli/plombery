import { PipelineRun } from '@/src/types'
import { STATUS_COLORS } from '@/src/utils'
import {
  Card,
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  Text,
  Badge,
} from '@tremor/react'
import Link from 'next/link'

interface Props {
  pipelineId: string
  runs: PipelineRun[]
  triggerId: string
}

const RunsList: React.FC<Props> = ({ pipelineId, runs, triggerId }) => (
  <Card marginTop="mt-5">
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell textAlignment="text-right">#</TableHeaderCell>
          <TableHeaderCell>Status</TableHeaderCell>
          <TableHeaderCell>Started at</TableHeaderCell>
          <TableHeaderCell textAlignment="text-right">Duration</TableHeaderCell>
          <TableHeaderCell> </TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {runs.map((run) => (
          <TableRow key={run.id}>
            <TableCell textAlignment="text-right">{run.id}</TableCell>
            <TableCell>
              <Badge text={run.status} color={STATUS_COLORS[run.status]} />
            </TableCell>
            <TableCell>
              <Text>{run.start_time.toString()}</Text>
            </TableCell>
            <TableCell textAlignment="text-right">
              {(run.duration / 1000).toFixed(2)} s
            </TableCell>
            <TableCell>
              <Link
                href={`/pipelines/${pipelineId}/triggers/${triggerId}/runs/${run.id}`}
              >
                Logs
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </Card>
)

export default RunsList
