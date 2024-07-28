import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Bold,
  Card,
  CategoryBar,
  Flex,
  Grid,
  Metric,
  Text,
  Title,
} from '@tremor/react'
import { addMilliseconds, isSameDay } from 'date-fns'
import { useParams } from 'react-router-dom'
import { useEffect } from 'react'

import Breadcrumbs from '@/components/Breadcrumbs'
import LogViewer from '@/components/LogViewer'
import PageLayout from '@/components/PageLayout'
import StatusBadge from '@/components/StatusBadge'
import RunsTasksList from '@/components/Tasks'
import Timer from '@/components/Timer'
import { MANUAL_TRIGGER } from '@/constants'
import { getPipeline, getRun } from '@/repository'
import { socket } from '@/socket'
import { Trigger } from '@/types'
import { TASKS_COLORS, formatDate, formatDateTime, formatTime } from '@/utils'

const RunViewPage = () => {
  const queryClient = useQueryClient()
  const urlParams = useParams()
  const pipelineId = urlParams.pipelineId as string
  const triggerId = urlParams.triggerId as string
  const runId = parseInt(urlParams.runId as string)

  useEffect(() => {
    const onRunUpdate = () => {
      queryClient.invalidateQueries({
        queryKey: getRun(pipelineId, triggerId, runId).queryKey,
      })
    }
    socket.on('run-update', onRunUpdate)

    return () => {
      socket.off('run-update', onRunUpdate)
    }
  }, [pipelineId])

  const pipelineQuery = useQuery(getPipeline(pipelineId))
  const runQuery = useQuery(getRun(pipelineId, triggerId, runId))

  if (pipelineQuery.isPending) {
    return <div>Loading...</div>
  }

  if (pipelineQuery.isError) {
    return <div>Error</div>
  }

  const pipeline = pipelineQuery.data

  const isManualTrigger = triggerId === MANUAL_TRIGGER.id
  const trigger: Trigger | undefined = !isManualTrigger
    ? pipeline.triggers.find((trigger) => trigger.id === triggerId)
    : MANUAL_TRIGGER

  const run = runQuery.data

  if (!run) {
    return <div>Run not found</div>
  }

  if (!trigger) {
    return <div>Trigger not found</div>
  }

  const totalTasksDuration = (run.tasks_run || []).reduce(
    (tot, cur) => tot + cur.duration,
    0
  )
  const tasksRunDurations = (run.tasks_run || []).map((tr) =>
    totalTasksDuration ? (tr.duration / totalTasksDuration) * 100 : 0
  )

  const runEndTime = addMilliseconds(run.start_time, run.duration)

  return (
    <PageLayout
      header={
        <>
          <Title>Run #{runId}</Title>
          <Breadcrumbs pipeline={pipeline} trigger={trigger} run={run} />
        </>
      }
    >
      <Grid numItemsMd={3} className="gap-6 mt-6">
        <RunsTasksList pipeline={pipeline} run={run} />

        <Card>
          <Flex className="items-start">
            <Text>Duration</Text>
            <StatusBadge status={run.status} />
          </Flex>

          <Flex className="justify-start items-baseline space-x-3 truncate">
            <Metric>
              {run.status !== 'running' ? (
                (run.duration / 1000).toFixed(2)
              ) : (
                <Timer startTime={run.start_time} />
              )}{' '}
              s
            </Metric>
          </Flex>

          <CategoryBar
            values={tasksRunDurations}
            colors={TASKS_COLORS}
            showLabels={false}
            className="mt-3"
          />

          <Flex alignItems="start" className="mt-2">
            <div>
              <Text>
                <Bold title={formatDateTime(run.start_time, true)}>
                  {formatTime(run.start_time)}
                </Bold>
              </Text>
              <Text className="mt-1">{formatDate(run.start_time)}</Text>
            </div>

            <div className="text-right">
              <Text>
                <Bold title={formatDateTime(runEndTime, true)}>
                  {formatTime(runEndTime)}
                </Bold>
              </Text>
              {!isSameDay(run.start_time, runEndTime) && (
                <Text>{formatDate(runEndTime)}</Text>
              )}
            </div>
          </Flex>
        </Card>
      </Grid>

      <div className="mt-6">
        <Card>
          <LogViewer pipeline={pipeline} run={run} />
        </Card>
      </div>
    </PageLayout>
  )
}

export default RunViewPage
