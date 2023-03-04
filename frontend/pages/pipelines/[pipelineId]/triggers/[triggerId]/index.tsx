import Breadcrumbs from '@/src/components/Breadcrumbs'
import RunsDurationChart from '@/src/components/RunsDurationChart'
import RunsList from '@/src/components/RunsList'
import RunsStatusChart from '@/src/components/RunsStatusChart'
import { getPipeline, getRuns } from '@/src/repository'
import { useQuery } from '@tanstack/react-query'
import { Card, Text, Title, ColGrid, Block } from '@tremor/react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import React from 'react'

const TriggerView: React.FC = () => {
  const router = useRouter()
  const pipelineId = router.query.pipelineId as string
  const triggerId = router.query.triggerId as string

  const pipelineQuery = useQuery({
    queryKey: ['pipeline', pipelineId],
    queryFn: () => getPipeline(pipelineId),
    initialData: { id: '', name: '', tasks: [], triggers: [] },
    enabled: !!pipelineId,
  })

  const runsQuery = useQuery({
    queryKey: ['runs', triggerId, pipelineId],
    queryFn: () => getRuns(pipelineId, triggerId),
    initialData: [],
    enabled: !!triggerId,
  })

  if (runsQuery.isLoading || pipelineQuery.isLoading)
    return <div>Loading...</div>

  if (runsQuery.error || pipelineQuery.error)
    return <div>An error has occurred</div>

  const pipeline = pipelineQuery.data
  const trigger = pipeline.triggers.find(
    (trigger) => trigger.name === triggerId
  )

  if (!trigger) {
    return <div>Trigger not found</div>
  }

  return (
    <main className="bg-slate-50 p-6 sm:p-10 min-h-screen">
      <Title>Trigger {trigger.name}</Title>
      <Breadcrumbs pipeline={pipeline} trigger={trigger} />

      <ColGrid
        numColsMd={2}
        numColsLg={3}
        gapX="gap-x-6"
        gapY="gap-y-6"
        marginTop="mt-6"
      >
        <Card>
          {/* Placeholder to set height */}
          <div className="h-28" />
        </Card>

        <RunsStatusChart runs={runsQuery.data} />

        <RunsDurationChart runs={runsQuery.data} />
      </ColGrid>

      <Block marginTop="mt-6">
        <RunsList
          runs={runsQuery.data}
          pipelineId={pipelineId}
          triggerId={triggerId}
        />
      </Block>
    </main>
  )
}

export default TriggerView
