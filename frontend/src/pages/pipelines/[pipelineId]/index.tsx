import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Title,
  Col,
  Text,
  ListItem,
  Flex,
  Icon,
  List,
  Bold,
  Grid,
  TextInput,
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
import TriggersList from '@/components/TriggersList'
import PageLayout from '@/components/PageLayout'

const PipelineView: React.FC = () => {
  const urlParams = useParams()
  const pipelineId = urlParams.pipelineId as string

  const pipelineQuery = useQuery(getPipeline(pipelineId))
  const runsQuery = useQuery(listRuns(pipelineId))

  const CopyUrlButton = () => (
    <CopyButton content={getPipelineRunUrl(pipelineId)} className="ml-2.5" />
  )

  if (runsQuery.isLoading || pipelineQuery.isLoading)
    return <div>Loading...</div>

  if (runsQuery.isError || pipelineQuery.isError)
    return <div>An error has occurred</div>

  const pipeline = pipelineQuery.data

  return (
    <PageLayout
      header={
        <div>
          <Flex className="items-start">
            <Flex className="justify-start items-start md:items-center flex-col md:flex-row min-w-0">
              <Title className="truncate max-w-full">
                Pipeline {pipeline.name}
              </Title>
              {pipeline.description && (
                <Text className="truncate max-w-full">
                  <span className="hidden md:inline mx-2">&middot;</span>
                  {pipeline.description}
                </Text>
              )}
            </Flex>

            <ManualRunDialog pipeline={pipeline} />
          </Flex>

          <Breadcrumbs pipeline={pipeline} className="mt-4" />
        </div>
      }
    >
      <Grid numItemsMd={2} numItemsLg={3} className="gap-6 mt-6">
        <Card className="flex flex-col h-full">
          <Title>Tasks</Title>

          <List>
            {pipeline.tasks.map((task) => (
              <ListItem key={task.id}>
                <div>
                  <Text>
                    <Bold>{task.name}</Bold>
                  </Text>
                  {task.description && (
                    <Text className="truncate">{task.description}</Text>
                  )}
                </div>
              </ListItem>
            ))}
          </List>

          <div style={{ flexGrow: 1 }} />

          <Flex className="gap-8">
            <Flex className="justify-start w-auto flex-shrink-0">
              <Text>Run URL</Text>

              <Icon
                size="sm"
                color="slate"
                icon={QuestionMarkCircleIcon}
                tooltip="URL to run the pipeline programmatically via an HTTP POST request"
              />
            </Flex>

            <TextInput
              title={getPipelineRunUrl(pipelineId)}
              value={getPipelineRunUrl(pipelineId)}
              readOnly
              icon={CopyUrlButton}
              className="flex-grow"
            />
          </Flex>
        </Card>

        <RunsStatusChart
          subject="Pipeline"
          runs={[...runsQuery.data].reverse()}
        />

        <RunsDurationChart runs={runsQuery.data} />
      </Grid>

      <Grid
        numItems={1}
        numItemsSm={1}
        numItemsMd={1}
        numItemsLg={2}
        className="gap-6 mt-6"
      >
        <Col>
          <TriggersList pipeline={pipeline} />
        </Col>

        <Col>
          <RunsList runs={runsQuery.data} pipelineId={pipelineId} />
        </Col>
      </Grid>
    </PageLayout>
  )
}

export default PipelineView
