import { AreaChart, Card, Flex, Metric, Text } from '@tremor/react'

import { PipelineRun } from '../types'

interface Props {
  runs: PipelineRun[]
}

const dataFormatter = (number: number) => (number / 1000).toFixed(1) + ' s'

const RunsDurationChart: React.FC<Props> = ({ runs }) => {
  const successfulRuns = runs
    .filter((run) => run.status === 'completed')
    .reverse()
  const avgDuration =
    successfulRuns.reduce((total, current) => total + current.duration, 0) /
      successfulRuns.length || 0

  return (
    <Card>
      <Flex className="items-start">
        <Text>Duration (AVG)</Text>
      </Flex>

      <Flex className="justify-start items-baseline space-x-3 truncate">
        <Metric>{dataFormatter(avgDuration)}</Metric>
      </Flex>

      <AreaChart
        data={successfulRuns}
        index="id"
        categories={['duration']}
        colors={['indigo']}
        valueFormatter={dataFormatter}
        yAxisWidth={40}
        showLegend={false}
        autoMinValue
        className="mt-6 h-28"
      />
    </Card>
  )
}

export default RunsDurationChart
