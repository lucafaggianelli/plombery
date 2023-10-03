import { UseQueryResult } from '@tanstack/react-query'
import { Card, Title, Text, Flex, Tracker, Italic, Metric } from '@tremor/react'
import { HTTPError } from 'ky'

import { PipelineRun } from '../types'
import { STATUS_COLORS } from '../utils'

interface Props {
  query: UseQueryResult<PipelineRun[], HTTPError>
  subject: 'Trigger' | 'Pipeline'
}

const Loader = ({ subject }: { subject: string }) => (
  <Card>
    <Flex className="items-start">
      <Text>Successful runs</Text>
    </Flex>

    <Flex className="justify-start items-baseline space-x-3 truncate">
      <Metric className="w-24 bg-slate-700 animate-pulse rounded">
        &nbsp;
      </Metric>
    </Flex>

    <>
      <Flex className="mt-4">
        <Text>{subject} health</Text>
      </Flex>

      <div className="h-10 mt-2 bg-slate-700 animate-pulse rounded" />
    </>
    <Flex className="mt-2">
      <div className="h-2 bg-slate-700 animate-pulse" />
      <div className="h-2 bg-slate-700 animate-pulse" />
    </Flex>
  </Card>
)

const RunsStatusChart: React.FC<Props> = ({ query, subject }) => {
  if (query.isLoading || query.isFetching) {
    return <Loader subject={subject} />
  }

  if (query.error) {
    return <div>error</div>
  }

  const runs = [...query.data].reverse()
  const successfulRuns = runs.filter((run) => run.status === 'completed')

  const successPercentage = (successfulRuns.length / runs.length) * 100 || 0

  const fromDate = runs[0]?.start_time
  const toDate = runs[runs.length - 1]?.start_time

  return (
    <Card>
      <Flex className="items-start">
        <Text>Successful runs</Text>
      </Flex>

      <Flex className="justify-start items-baseline space-x-3 truncate">
        <Metric>
          {successPercentage.toFixed(1)} <span className="text-lg">%</span>
        </Metric>
      </Flex>

      {runs.length ? (
        <>
          <Flex className="mt-4">
            <Text>{subject} health</Text>
          </Flex>
          <Tracker
            className="mt-2"
            data={runs.map((run) => ({
              key: run.id,
              color: STATUS_COLORS[run.status],
              tooltip: `#${run.id} ${run.status}`,
            }))}
          />
        </>
      ) : (
        <Text className="text-center mt-8">
          <Italic>This {subject.toLowerCase()} has no runs yet</Italic>
        </Text>
      )}
      <Flex className="mt-2">
        <Text>{fromDate && fromDate.toDateString()}</Text>
        <Text>{toDate && toDate.toDateString()}</Text>
      </Flex>
    </Card>
  )
}

export default RunsStatusChart
