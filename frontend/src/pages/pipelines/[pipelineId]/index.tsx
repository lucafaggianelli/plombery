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
import { ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline'

import Breadcrumbs from '@/components/Breadcrumbs'
import RunsDurationChart from '@/components/RunsDurationChart'
import RunsList from '@/components/RunsList'
import RunsStatusChart from '@/components/RunsStatusChart'
import { getPipeline, listRuns } from '@/repository'
import ManualRunDialog from '@/components/ManualRunDialog'
import TriggersList from '@/components/TriggersList'
import PageLayout from '@/components/PageLayout'
import PipelineHttpRun from '@/components/help/PipelineHttpRun'

const PipelineView: React.FC = () => {
  const urlParams = useParams()
  const pipelineId = urlParams.pipelineId as string

  const pipelineQuery = useQuery(getPipeline(pipelineId))
  const runsQuery = useQuery(listRuns(pipelineId))

  if (pipelineQuery.isPending) return <div>Loading...</div>

  if (pipelineQuery.isError) return <div>An error has occurred</div>

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

          <Breadcrumbs pipeline={pipeline} className="mt-4 md:mt-0" />
        </div>
      }
    >
      <Grid numItemsMd={2} numItemsLg={3} className="gap-6 mt-6">
        <Card className="flex flex-col h-full">
          <Title>Tasks</Title>

          <List>
            {pipeline.tasks.map((task) => (
              <ListItem key={task.id}>
                <div className="max-w-full">
                  <Text>
                    <Bold>{task.name}</Bold>
                  </Text>
                  {task.description && (
                    <div className="truncate" title={task.description}>
                      {task.description}
                    </div>
                  )}
                </div>
              </ListItem>
            ))}

            {pipeline.tasks.length === 0 && (
              <div className="mt-4">
                <Text className="text-center italic">
                  This pipeline has no tasks so it can't be run.
                </Text>

                <div className="text-center mt-2 text-sm">
                  <a
                    href="https://lucafaggianelli.github.io/plombery/tasks/"
                    target="_blank"
                    className="inline-flex items-center gap-2 bg-indigo-50/30 hover:bg-indigo-50 dark:bg-indigo-950/50 dark:hover:bg-indigo-950 rounded-sm px-4 py-2 text-indigo-500 transition-colors duration-300 cursor-pointer no-underline"
                    rel="noopener noreferrer"
                  >
                    How to create tasks
                    <Icon
                      icon={ArrowTopRightOnSquareIcon}
                      size="sm"
                      className="p-0"
                      color="indigo"
                    />
                  </a>
                </div>
              </div>
            )}
          </List>

          <div style={{ flexGrow: 1 }} />

          <Flex className="justify-between gap-8">
            <Text>Run URL</Text>

            <PipelineHttpRun pipelineId={pipelineId} />
          </Flex>
        </Card>

        <RunsStatusChart subject="Pipeline" query={runsQuery} />

        <RunsDurationChart query={runsQuery} />
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
          <RunsList query={runsQuery} pipelineId={pipelineId} />
        </Col>
      </Grid>
    </PageLayout>
  )
}

export default PipelineView
