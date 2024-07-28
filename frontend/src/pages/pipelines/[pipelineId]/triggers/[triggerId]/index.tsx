import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Card,
  Title,
  Subtitle,
  Text,
  Bold,
  ListItem,
  Button,
  Flex,
  Grid,
} from '@tremor/react'
import { PlayIcon } from '@heroicons/react/24/outline'
import { useNavigate, useParams } from 'react-router-dom'
import React from 'react'

import TriggerParamsDialog from '@/components/TriggerParamsDialog'
import Breadcrumbs from '@/components/Breadcrumbs'
import ManualRunDialog from '@/components/ManualRunDialog'
import PageLayout from '@/components/PageLayout'
import RunsDurationChart from '@/components/RunsDurationChart'
import RunsList from '@/components/RunsList'
import RunsStatusChart from '@/components/RunsStatusChart'
import { MANUAL_TRIGGER } from '@/constants'
import { getPipeline, listRuns, runPipeline } from '@/repository'
import { Trigger } from '@/types'
import PipelineHttpRun from '@/components/help/PipelineHttpRun'

const TriggerView: React.FC = () => {
  const navigate = useNavigate()
  const urlParams = useParams()
  const pipelineId = urlParams.pipelineId as string
  const triggerId = urlParams.triggerId as string

  const pipelineQuery = useQuery(getPipeline(pipelineId))

  const runsQuery = useQuery({
    ...listRuns(pipelineId, triggerId),
    enabled: !!triggerId,
  })

  const runPipelineMutation = useMutation({
    ...runPipeline(pipelineId, triggerId),
    onSuccess(data) {
      navigate(
        `/pipelines/${data.pipeline_id}/triggers/${data.trigger_id}/runs/${data.id}`
      )
    },
  })

  if (pipelineQuery.isPending) return <div>Loading...</div>

  if (pipelineQuery.isError) return <div>An error has occurred</div>

  const pipeline = pipelineQuery.data

  const isManualTrigger = triggerId === MANUAL_TRIGGER.id
  const trigger: Trigger | undefined = !isManualTrigger
    ? pipeline.triggers.find((trigger) => trigger.id === triggerId)
    : MANUAL_TRIGGER

  if (!trigger) {
    return <div>Trigger not found</div>
  }

  const runTriggerButton = isManualTrigger ? (
    <ManualRunDialog pipeline={pipeline} />
  ) : (
    <Button
      size="xs"
      color="indigo"
      variant="secondary"
      icon={PlayIcon}
      onClick={() => {
        runPipelineMutation.mutateAsync()
      }}
    >
      Run
    </Button>
  )

  return (
    <PageLayout
      header={
        <div>
          <Flex className="items-start">
            <Flex className="justify-start items-start md:items-center flex-col md:flex-row min-w-0">
              <Title className="truncate max-w-full">
                Trigger {trigger.name}
              </Title>
              {trigger.description && (
                <Text className="truncate max-w-full">
                  <span className="hidden md:inline mx-2">&middot;</span>
                  {trigger.description}
                </Text>
              )}
            </Flex>

            {runTriggerButton}
          </Flex>

          <Breadcrumbs
            pipeline={pipeline}
            trigger={trigger}
            className="mt-4 md:mt-0"
          />
        </div>
      }
    >
      <Grid numItemsMd={2} numItemsLg={3} className="gap-6 mt-6">
        <Card className="flex flex-col h-full">
          <Title>{trigger.name}</Title>
          <Subtitle>{trigger.description}</Subtitle>

          <div style={{ flexGrow: 1 }} />

          <ListItem>
            <Text>Schedule</Text>
            <Text>
              <Bold>{trigger.schedule}</Bold>
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

          <Flex className="">
            <Text>Run URL</Text>

            <PipelineHttpRun pipelineId={pipelineId} triggerId={triggerId} />
          </Flex>
        </Card>

        <RunsStatusChart subject="Trigger" query={runsQuery} />

        <RunsDurationChart query={runsQuery} />
      </Grid>

      <div className="mt-6">
        <RunsList
          query={runsQuery}
          pipelineId={pipelineId}
          triggerId={triggerId}
        />
      </div>
    </PageLayout>
  )
}

export default TriggerView
