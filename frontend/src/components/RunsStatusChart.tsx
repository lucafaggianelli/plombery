import {
  Card,
  Title,
  Text,
  Flex,
  Tracking,
  TrackingBlock,
} from '@tremor/react'
import { PipelineRun } from '../types'
import { STATUS_COLORS } from '../utils'

interface Props {
  runs: PipelineRun[]
}

const RunsStatusChart: React.FC<Props> = ({ runs }) => {
  const successfulRuns = runs.filter((run) => run.status === 'completed')

  const successPercentage = (successfulRuns.length / runs.length) * 100 || 0

  const fromDate = runs[0]?.start_time
  const toDate = runs[runs.length - 1]?.start_time

  return (
    <Card>
      <Flex>
        <Title>Trigger health</Title>
      </Flex>

      <Flex marginTop="mt-4">
        <Text>Successful runs</Text>
        <Text>{successPercentage.toFixed(1)} %</Text>
      </Flex>
      {runs.length ? (
        <Tracking marginTop="mt-2">
          {runs.map((run) => (
            <TrackingBlock
              key={run.id}
              color={STATUS_COLORS[run.status]}
              tooltip={`#${run.id} ${run.status}`}
            />
          ))}
        </Tracking>
      ) : (
        <Text textAlignment="text-center" marginTop="mt-8">
          <em>This trigger has no runs yet</em>
        </Text>
      )}
      <Flex marginTop="mt-2">
        <Text>{fromDate && fromDate.toDateString()}</Text>
        <Text>{toDate && toDate.toDateString()}</Text>
      </Flex>
    </Card>
  )
}

export default RunsStatusChart
