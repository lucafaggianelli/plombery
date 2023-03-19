import Breadcrumbs from '@/components/Breadcrumbs'
import DataViewerDialog from '@/components/DataViewerDialog'
import LogViewer from '@/components/LogViewer'
import { getPipeline, getRun } from '@/repository'
import { STATUS_COLORS } from '@/utils'
import { useQuery } from '@tanstack/react-query'
import {
  Badge,
  Block,
  Button,
  Card,
  ColGrid,
  Flex,
  Metric,
  Text,
  Title,
} from '@tremor/react'
import { useState } from 'react'
import { useParams } from 'react-router-dom'

const LogsPage = () => {
  const urlParams = useParams()
  const pipelineId = urlParams.pipelineId as string
  const triggerId = urlParams.triggerId as string
  const runId = parseInt(urlParams.runId as string)

  const [viewDataDialog, setViewDataDialog] = useState<string | undefined>()

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
        </Card>

        <Card>
          {pipeline.tasks.map((task) => (
            <Button
              key={task.id}
              variant="secondary"
              color="indigo"
              size="xs"
              onClick={() => setViewDataDialog(task.id)}
            >
              View {task.id} data
            </Button>
          ))}
        </Card>
      </ColGrid>

      <DataViewerDialog
        pipelineId={pipelineId}
        triggerId={triggerId}
        runId={runId}
        taskId={viewDataDialog || ''}
        open={!!viewDataDialog}
        onClose={() => setViewDataDialog(undefined)}
      />

      <Block marginTop="mt-6">
        <Card>
          <LogViewer pipeline={pipeline} trigger={trigger} runId={runId} />
        </Card>
      </Block>
    </main>
  )
}

export default LogsPage
