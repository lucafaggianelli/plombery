import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Bold, Card, Flex, Grid, Metric, Text, Title } from '@tremor/react'
import { addMilliseconds, isSameDay } from 'date-fns'
import { useParams } from 'react-router'
import { useEffect } from 'react'

import Breadcrumbs from '@/components/Breadcrumbs'
import LogViewer from '@/components/LogViewer'
import PageLayout from '@/components/PageLayout'
import StatusBadge from '@/components/StatusBadge'
import Timer from '@/components/Timer'
import { MANUAL_TRIGGER } from '@/constants'
import { getPipeline, getRun } from '@/repository'
import { socket } from '@/socket'
import { Trigger } from '@/types'
import { formatDate, formatDateTime, formatDuration, formatTime } from '@/utils'
import DagViewer from '@/components/DagViewer'

const RunViewPage = () => {
  const queryClient = useQueryClient()
  const urlParams = useParams()
  const pipelineId = urlParams.pipelineId as string
  const triggerId = urlParams.triggerId as string
  const runId = parseInt(urlParams.runId as string)

  useEffect(() => {
    const onRunUpdate = async () => {
      await queryClient.invalidateQueries({
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

  if (pipelineQuery.isPending || runQuery.isPending) {
    return <div>Loading...</div>
  }

  if (pipelineQuery.isError) {
    return <div>Error loading the pipeline</div>
  }

  const pipeline = pipelineQuery.data
  const run = runQuery.data

  const isManualTrigger = triggerId === MANUAL_TRIGGER.id
  const trigger: Trigger | undefined = !isManualTrigger
    ? pipeline.triggers.find((trigger) => trigger.id === triggerId)
    : MANUAL_TRIGGER

  if (!run) {
    return <div>Run not found</div>
  }

  if (!trigger) {
    return <div>Trigger not found</div>
  }

  const totalTasksDuration = (run.task_runs || []).reduce(
    (tot, cur) => tot + cur.duration,
    0
  )
  const tasksRunDurations = (run.task_runs || []).map((tr) =>
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
      <Grid numItemsMd={2} className="gap-6 mt-6">
        <Card className="col-span-2 p-0">
          <DagViewer pipeline={pipeline} run={run}>
            <Card className="p-3">
              <Flex className="items-start">
                <Text className="text-xs">Duration</Text>
                <StatusBadge status={run.status} />
              </Flex>

              <Flex className="justify-start items-baseline space-x-3 truncate">
                <Metric className="tabular-nums text-lg">
                  {run.status !== 'running' ? (
                    formatDuration(run.duration)
                  ) : (
                    <Timer startTime={run.start_time} />
                  )}
                </Metric>
              </Flex>

              <Flex className="items-start mt-2 gap-4">
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
          </DagViewer>
        </Card>
      </Grid>

      <div className="mt-6">
        <Card className="p-0 overflow-hidden">
          <LogViewer pipeline={pipeline} run={run} />
        </Card>
      </div>
    </PageLayout>
  )
}

export default RunViewPage
