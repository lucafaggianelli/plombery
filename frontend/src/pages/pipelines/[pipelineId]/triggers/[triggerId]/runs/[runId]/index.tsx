import { useQuery } from '@tanstack/react-query'
import { Block, Card, ColGrid, Flex, Metric, Text, Title } from '@tremor/react'
import { useParams } from 'react-router-dom'

import Breadcrumbs from '@/components/Breadcrumbs'
import LogViewer from '@/components/LogViewer'
import StatusBadge from '@/components/StatusBadge'
import RunsTasksList from '@/components/Tasks'
import { getPipeline, getRun } from '@/repository'

const RunViewPage = () => {
  const urlParams = useParams()
  const pipelineId = urlParams.pipelineId as string
  const triggerId = urlParams.triggerId as string
  const runId = parseInt(urlParams.runId as string)

  const pipelineQuery = useQuery({
    queryKey: ['pipeline', pipelineId],
    queryFn: () => getPipeline(pipelineId),
    initialData: { id: '', name: '', description: '', tasks: [], triggers: [] },
    enabled: !!pipelineId,
  })

  const runQuery = useQuery({
    queryKey: ['run', pipelineId, triggerId, runId],
    queryFn: () => getRun(runId),
    enabled: !!(pipelineId && triggerId && runId),
  })

  const pipeline = pipelineQuery.data
  const trigger = pipeline.triggers.find((trigger) => trigger.id === triggerId)
  const run = runQuery.data

  if (!run) {
    return <div>Run not found</div>
  }

  if (!trigger) {
    return <div>Trigger not found</div>
  }

  return (
    <main className="bg-slate-50 p-6 sm:p-10 min-h-screen">
      <Title>Run #{runId}</Title>

      <Breadcrumbs pipeline={pipeline} trigger={trigger} run={run} />

      <ColGrid numColsMd={3} gapX="gap-x-6" gapY="gap-y-6" marginTop="mt-6">
        <RunsTasksList pipeline={pipeline} run={run} />

        <Card>
          <Flex alignItems="items-start">
            <Text>Duration</Text>
            <StatusBadge status={run.status} />
          </Flex>
          <Flex
            justifyContent="justify-start"
            alignItems="items-baseline"
            spaceX="space-x-3"
            truncate={true}
          >
            <Metric>{(run.duration / 1000).toFixed(1)}s</Metric>
          </Flex>
        </Card>
      </ColGrid>

      <Block marginTop="mt-6">
        <Card>
          <LogViewer pipeline={pipeline} trigger={trigger} runId={runId} />
        </Card>
      </Block>
    </main>
  )
}

export default RunViewPage
