import {
  Card,
  Icon,
  Title,
  Text,
  Flex,
  Tracking,
  TrackingBlock,
  Color,
  ColGrid,
} from '@tremor/react'
import { PipelineRun } from '../types'
import { STATUS_COLORS } from '../utils'

interface Props {
  runs: PipelineRun[]
}

const RunsStatusChart: React.FC<Props> = ({ runs }) => {
  if (!runs.length) {
    return null
  }

  const successfulRuns = runs
    .filter((run) => run.status === 'success')

  const successPercentage = (successfulRuns.length / runs.length) * 100

  const fromDate = successfulRuns[0].start_time
  const toDate = successfulRuns[successfulRuns.length - 1].start_time

  return (
    <Card>
      <Flex>
        <Title>Trigger</Title>
      </Flex>

      <Flex marginTop="mt-4">
        <Text>Status</Text>
        <Text>{successPercentage.toFixed(1)} %</Text>
      </Flex>
      <Tracking marginTop="mt-2">
        {runs.map((run) => (
          <TrackingBlock
            key={run.id}
            color={STATUS_COLORS[run.status]}
            tooltip={run.status}
          />
        ))}
      </Tracking>
      <Flex marginTop="mt-2">
        <Text>{fromDate.toDateString()}</Text>
        <Text>{toDate.toDateString()}</Text>
      </Flex>
    </Card>
  )
}

export default RunsStatusChart
