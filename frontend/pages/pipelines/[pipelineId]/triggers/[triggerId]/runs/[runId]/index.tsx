import Breadcrumbs from '@/src/components/Breadcrumbs'
import LogViewer from '@/src/components/LogViewer'
import { getPipeline, getRun } from '@/src/repository'
import { STATUS_COLORS } from '@/src/utils'
import { useQuery } from '@tanstack/react-query'
import {
  Badge,
  Block,
  Card,
  ColGrid,
  Flex,
  Metric,
  Text,
  Title,
} from '@tremor/react'
import { useRouter } from 'next/router'

const LOG_LEVELS = ['debug', 'info', 'warning', 'error']

const LogsPage = () => {
  const router = useRouter()
  const pipelineId = router.query.pipelineId as string
  const triggerId = router.query.triggerId as string
  const runId = parseInt(router.query.runId as string)

  const pipelineQuery = useQuery({
    queryKey: ['pipeline', pipelineId],
    queryFn: () => getPipeline(pipelineId),
    initialData: { id: '', name: '', description: '', tasks: [], triggers: [] },
    enabled: !!pipelineId,
  })

  const runQuery = useQuery({
    queryKey: ['run', pipelineId, triggerId, runId],
    queryFn: () => getRun(pipelineId, triggerId, runId),
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
        <Card>
          <Flex alignItems="items-start">
            <Text>Duration</Text>
            <Badge text={run.status} color={STATUS_COLORS[run.status]} />
          </Flex>
          <Flex
            justifyContent="justify-start"
            alignItems="items-baseline"
            spaceX="space-x-3"
            truncate={true}
          >
            <Metric>{(run.duration / 1000).toFixed(1)}s</Metric>
          </Flex>

          <a
            href={`http://localhost:8000/pipelines/${pipelineId}/triggers/${triggerId}/runs/${runId}/data/${pipeline.tasks[0]}`}
          >
            Download data
          </a>
        </Card>
      </ColGrid>

      <Block marginTop="mt-6">
        <Card>
          <LogViewer
            pipeline={pipeline}
            trigger={trigger}
            runId={runId}
          />
        </Card>
      </Block>
    </main>
  )
}

export default LogsPage
