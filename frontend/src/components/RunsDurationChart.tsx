import { AreaChart, Card, Flex, Metric, Text } from '@tremor/react'

import { PipelineRun } from '../types'

interface Props {
  runs: PipelineRun[]
}

const dataFormatter = (number: number) => (number / 1000).toFixed(1) + ' s'

const RunsDurationChart: React.FC<Props> = ({ runs }) => {
  const successfulRuns = runs.filter((run) => run.status === 'completed').reverse()
  const avgDuration =
    successfulRuns.reduce((total, current) => total + current.duration, 0) /
    successfulRuns.length || 0

  return (
    <Card>
      <Flex alignItems="items-start">
        <Text>Duration</Text>
      </Flex>

      <Flex
        justifyContent="justify-start"
        alignItems="items-baseline"
        spaceX="space-x-3"
        truncate={true}
      >
        <Metric>{dataFormatter(avgDuration)}</Metric>
      </Flex>

      <AreaChart
        data={successfulRuns}
        dataKey="id"
        categories={['duration']}
        colors={['indigo']}
        valueFormatter={dataFormatter}
        marginTop="mt-6"
        yAxisWidth="w-10"
        height="h-28"
        showLegend={false}
        autoMinValue
      />
    </Card>
  )
}

export default RunsDurationChart
