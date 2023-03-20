import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Card,
  Title,
  ColGrid,
  Block,
  Subtitle,
  Text,
  Bold,
  ListItem,
  Button,
  Flex,
  Icon,
} from '@tremor/react'
import { useParams } from 'react-router-dom'
import React from 'react'

import TriggerParamsDialog from '@/components/TriggerParamsDialog'
import CopyButton from '@/components/CopyButton'
import Breadcrumbs from '@/components/Breadcrumbs'
import RunsDurationChart from '@/components/RunsDurationChart'
import RunsList from '@/components/RunsList'
import RunsStatusChart from '@/components/RunsStatusChart'
import {
  getPipeline,
  listRuns,
  getTriggerRunUrl,
  runPipelineTrigger,
} from '@/repository'
import { formatDateTime } from '@/utils'
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline'

const TriggerView: React.FC = () => {
  const urlParams = useParams()
  const pipelineId = urlParams.pipelineId as string
  const triggerId = urlParams.triggerId as string

  const pipelineQuery = useQuery({
    queryKey: ['pipeline', pipelineId],
    queryFn: () => getPipeline(pipelineId),
    initialData: { id: '', name: '', description: '', tasks: [], triggers: [] },
    enabled: !!pipelineId,
  })

  const runsQuery = useQuery({
    queryKey: ['runs', triggerId, pipelineId],
    queryFn: () => listRuns(pipelineId, triggerId),
    initialData: [],
    enabled: !!triggerId,
  })

  const runPipelineMutation = useMutation({
    mutationFn: () => runPipelineTrigger(pipelineId, triggerId),
  })

  if (runsQuery.isLoading || pipelineQuery.isLoading)
    return <div>Loading...</div>

  if (runsQuery.error || pipelineQuery.error)
    return <div>An error has occurred</div>

  const pipeline = pipelineQuery.data
  const trigger = pipeline.triggers.find((trigger) => trigger.id === triggerId)

  if (!trigger) {
    return <div>Trigger not found</div>
  }

  return (
    <main className="bg-slate-50 p-6 sm:p-10 min-h-screen">
      <Flex alignItems="items-start">
        <Block>
          <Title>Trigger {trigger.name}</Title>
          <Breadcrumbs pipeline={pipeline} trigger={trigger} />
        </Block>

        <Button
          size="xs"
          color="indigo"
          onClick={() => {
            runPipelineMutation.mutateAsync()
          }}
        >
          Run now
        </Button>
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
            <Title>{trigger.name}</Title>
            <Subtitle>{trigger.description}</Subtitle>

            <div style={{ flexGrow: 1 }} />

            <ListItem>
              <Text>Schedule</Text>
              <Text>
                <Bold>{trigger.interval}</Bold>
              </Text>
            </ListItem>

            <ListItem>
              <Text>Next run</Text>
              <Text>
                <Bold>{formatDateTime(trigger.next_fire_time)}</Bold>
              </Text>
            </ListItem>

            <ListItem>
              <Text>Params</Text>
              {trigger.params ? (
                <TriggerParamsDialog trigger={trigger} />
              ) : (
                <Text>
                  <em>No params</em>
                </Text>
              )}
            </ListItem>

            <ListItem>
              <Flex justifyContent="justify-start">
                <Text>Run URL</Text>

                <Icon
                  size="sm"
                  color="slate"
                  icon={QuestionMarkCircleIcon}
                  tooltip="URL to run the trigger programmatically via an HTTP POST request"
                />
              </Flex>

              <Flex justifyContent="justify-end">
                <div
                  className="bg-slate-100 tr-border-slate-300 rounded tr-border text-slate-500 text-sm truncate px-1 mr-2"
                  style={{ maxWidth: 200 }}
                  title={getTriggerRunUrl(pipelineId, triggerId)}
                >
                  {getTriggerRunUrl(pipelineId, triggerId)}
                </div>

                <CopyButton content={getTriggerRunUrl(pipelineId, triggerId)} />
              </Flex>
            </ListItem>
          </div>
        </Card>

        <RunsStatusChart
          subject="Trigger"
          runs={[...runsQuery.data].reverse()}
        />

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
