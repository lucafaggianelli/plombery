import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Title,
  ColGrid,
  Block,
  Text,
  ListItem,
  Flex,
  Icon,
  List,
  Bold,
} from '@tremor/react'
import { useParams } from 'react-router-dom'
import React from 'react'
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline'

import CopyButton from '@/components/CopyButton'
import Breadcrumbs from '@/components/Breadcrumbs'
import RunsDurationChart from '@/components/RunsDurationChart'
import RunsList from '@/components/RunsList'
import RunsStatusChart from '@/components/RunsStatusChart'
import { getPipeline, getPipelineRunUrl, listRuns } from '@/repository'
import ManualRunDialog from '@/components/ManualRunDialog'

const PipelineView: React.FC = () => {
  const urlParams = useParams()
  const pipelineId = urlParams.pipelineId as string

  const pipelineQuery = useQuery({
    queryKey: ['pipeline', pipelineId],
    queryFn: () => getPipeline(pipelineId),
    initialData: { id: '', name: '', description: '', tasks: [], triggers: [] },
    enabled: !!pipelineId,
  })

  const runsQuery = useQuery({
    queryKey: ['runs', pipelineId, undefined],
    queryFn: () => listRuns(pipelineId),
    initialData: [],
  })

  if (runsQuery.isLoading || pipelineQuery.isLoading)
    return <div>Loading...</div>

  if (runsQuery.error || pipelineQuery.error)
    return <div>An error has occurred</div>

  const pipeline = pipelineQuery.data

  return (
    <main className="bg-slate-50 p-6 sm:p-10 min-h-screen">
      <Flex alignItems="items-start">
        <Block>
          <Flex justifyContent="justify-start" spaceX="space-x-2">
            <Title>Pipeline {pipeline.name}</Title>
            {pipeline.description && (
              <Text truncate>&middot; {pipeline.description}</Text>
            )}
          </Flex>
          <Breadcrumbs pipeline={pipeline} />
        </Block>

        <ManualRunDialog pipeline={pipeline} />
      </Flex>

      <ColGrid
        numColsMd={2}
        numColsLg={3}
        gapX="gap-x-6"
        gapY="gap-y-6"
        marginTop="mt-6"
      >
        <Card>
          <div className="tr-flex tr-flex-col tr-h-full">
            <Title>Tasks</Title>

            <List>
              {pipeline.tasks.map((task) => (
                <ListItem key={task.id}>
                  <Block>
                    <Text>
                      <Bold>{task.name}</Bold>
                    </Text>
                    {task.description && (
                      <Text truncate>{task.description}</Text>
                    )}
                  </Block>
                </ListItem>
              ))}
            </List>

            <div style={{ flexGrow: 1 }} />

            <ListItem>
              <Flex justifyContent="justify-start">
                <Text>Run URL</Text>

                <Icon
                  size="sm"
                  color="slate"
                  icon={QuestionMarkCircleIcon}
                  tooltip="URL to run the pipeline programmatically via an HTTP POST request"
                />
              </Flex>

              <Flex justifyContent="justify-end">
                <div
                  className="bg-slate-100 tr-border-slate-300 rounded tr-border text-slate-500 text-xs truncate px-1 mr-2"
                  style={{ maxWidth: 200 }}
                  title={getPipelineRunUrl(pipelineId)}
                >
                  {getPipelineRunUrl(pipelineId)}
                </div>

                <CopyButton content={getPipelineRunUrl(pipelineId)} />
              </Flex>
            </ListItem>
          </div>
        </Card>

        <RunsStatusChart
          subject="Pipeline"
          runs={[...runsQuery.data].reverse()}
        />

        <RunsDurationChart runs={runsQuery.data} />
      </ColGrid>

      <Block marginTop="mt-6">
        <RunsList runs={runsQuery.data} pipelineId={pipelineId} />
      </Block>
    </main>
  )
}

export default PipelineView
