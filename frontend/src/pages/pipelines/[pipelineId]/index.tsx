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
    <PageLayout
      header={
        <Flex className="items-start">
          <div>
            <Flex className="justify-start items-start md:items-center flex-col md:flex-row">
              <Title>Pipeline {pipeline.name}</Title>
              {pipeline.description && (
                <Text className="truncate">
                  <span className="hidden md:inline mx-2">&middot;</span>
                  {pipeline.description}
                </Text>
              )}
            </Flex>
            <Breadcrumbs pipeline={pipeline} />
          </div>

          <ManualRunDialog pipeline={pipeline} />
        </Flex>
      }
    >
      <Grid numColsMd={2} numColsLg={3} className="gap-6 mt-6">
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

          <ListItem>
            <Flex className="justify-start">
              <Text>Run URL</Text>

              <Icon
                size="sm"
                color="slate"
                icon={QuestionMarkCircleIcon}
                tooltip="URL to run the pipeline programmatically via an HTTP POST request"
              />
            </Flex>

            <Flex className="justify-end">
              <div
                className="bg-slate-100 border-slate-300 rounded border text-slate-500 text-xs truncate px-1 py-0.5 mr-2"
                style={{ maxWidth: 200 }}
                title={getPipelineRunUrl(pipelineId)}
              >
                {getPipelineRunUrl(pipelineId)}
              </div>

              <CopyButton content={getPipelineRunUrl(pipelineId)} />
            </Flex>
          </ListItem>
        </Card>

        <RunsStatusChart
          subject="Pipeline"
          runs={[...runsQuery.data].reverse()}
        />

        <RunsDurationChart runs={runsQuery.data} />
      </Grid>

      <Grid
        numCols={1}
        numColsSm={1}
        numColsMd={1}
        numColsLg={2}
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
