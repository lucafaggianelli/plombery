import { AreaChart, Card, Flex, Metric, Text } from '@tremor/react'
import { UseQueryResult } from '@tanstack/react-query'
import { HTTPError } from 'ky'

import { PipelineRun } from '../types'

interface Props {
  query: UseQueryResult<PipelineRun[], HTTPError>
}

const dataFormatter = (number: number) => (number / 1000).toFixed(1) + ' s'

const loader = (
  <Card>
    <Flex className="items-start">
      <Text>Duration (AVG)</Text>
    </Flex>

    <Flex className="justify-start items-baseline space-x-3 truncate">
      <Metric className="w-24 bg-slate-700 animate-pulse rounded">
        &nbsp;
      </Metric>
    </Flex>

    <div className="mt-6 h-28 bg-slate-700 animate-pulse rounded bg-stripes"></div>
  </Card>
)

const RunsDurationChart: React.FC<Props> = ({ query }) => {
  if (query.isFetching || query.isLoading) {
    return loader
  }

  if (query.isError) {
    return (
      <div className="text-rose">Error fetching data {query.error.message}</div>
    )
  }

  const successfulRuns = query.data
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
