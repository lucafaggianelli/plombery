import { useQuery } from '@tanstack/react-query'
import { Card, Grid, Title } from '@tremor/react'
import { useParams } from 'react-router'
import { useEffect } from 'react'

import Breadcrumbs from '@/components/Breadcrumbs'
import LogViewer from '@/components/LogViewer'
import PageLayout from '@/components/PageLayout'
import { MANUAL_TRIGGER } from '@/constants'
import { getPipeline, getRun } from '@/repository'
import { socket } from '@/socket'
import { Trigger } from '@/types'
import DagViewer from '@/components/DagViewer'
import DagDetailsPanel from '@/components/DagDetailsPanel'
import ManualRunDialog from '@/components/ManualRunDialog'

const RunViewPage = () => {
  const urlParams = useParams()
  const pipelineId = urlParams.pipelineId as string
  const triggerId = urlParams.triggerId as string
  const runId = parseInt(urlParams.runId as string)

  useEffect(() => {
    const onRunUpdate = async () => {
      await runQuery.refetch()
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

  return (
    <PageLayout
      header={
        <div className="flex gap-4 items-start justify-between">
          <div>
            <Title>Run #{runId}</Title>
            <Breadcrumbs pipeline={pipeline} trigger={trigger} run={run} />
          </div>

          <ManualRunDialog pipeline={pipeline} trigger={trigger} />
        </div>
      }
    >
      <Grid numItemsMd={2} className="gap-6 mt-6">
        <Card className="col-span-2 p-0">
          <DagViewer pipeline={pipeline} run={run}>
            <DagDetailsPanel pipeline={pipeline} run={run} />
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
