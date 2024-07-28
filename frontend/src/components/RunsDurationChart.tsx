import { AreaChart, Card, Flex, Metric, Text } from '@tremor/react'
import { UseQueryResult } from '@tanstack/react-query'
import { HTTPError } from 'ky'

import { PipelineRun } from '../types'
import ErrorAlert from './queries/Error'
import { ChartLoader, MetricLoader } from './queries/Loaders'

interface Props {
  query: UseQueryResult<PipelineRun[], HTTPError>
}

const dataFormatter = (number: number) => (number / 1000).toFixed(1) + ' s'

const Loader = () => (
  <Card>
    <Text>Duration (AVG)</Text>

    <MetricLoader />

    <ChartLoader className="mt-6" />
  </Card>
)

const RunsDurationChart: React.FC<Props> = ({ query }) => {
  if (query.isPending) {
    return <Loader />
  }

  if (query.isError) {
    return (
      <Card>
        <ErrorAlert query={query} />
      </Card>
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
