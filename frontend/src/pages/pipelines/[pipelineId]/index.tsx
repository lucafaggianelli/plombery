import { useQuery } from '@tanstack/react-query'
import { Card, Title, Col, Text, Flex, Grid } from '@tremor/react'
import { useParams } from 'react-router'
import React from 'react'

import Breadcrumbs from '@/components/Breadcrumbs'
import RunsDurationChart from '@/components/RunsDurationChart'
import RunsList from '@/components/RunsList'
import RunsStatusChart from '@/components/RunsStatusChart'
import { getPipeline, listRuns } from '@/repository'
import ManualRunDialog from '@/components/ManualRunDialog'
import TriggersList from '@/components/TriggersList'
import PageLayout from '@/components/PageLayout'
import DagViewer from '@/components/DagViewer'

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
        <Card className="md:col-span-2 lg:col-span-3 p-0">
          <DagViewer pipeline={pipeline} />
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
