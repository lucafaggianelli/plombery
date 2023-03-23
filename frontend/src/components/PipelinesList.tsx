import { useQuery } from '@tanstack/react-query'
import { Text, Title, Flex } from '@tremor/react'
import { Link } from 'react-router-dom'
import React from 'react'

import { listPipelines } from '@/repository'
import ManualRunDialog from './ManualRunDialog'
import TriggersList from './TriggersList'

const PipelinesList: React.FC = () => {
  const query = useQuery({
    queryKey: ['pipelines'],
    queryFn: listPipelines,
    initialData: [],
  })

  if (query.isLoading) return <div>Loading...</div>

  if (query.error) return <div>An error has occurred</div>

  const pipelines = query.data

  return (
    <>
      {pipelines.map((pipeline) => (
        <React.Fragment key={pipeline.id}>
          <Flex>
            <Flex>
              <Flex className="justify-start items-baseline space-x-2">
                <Title>
                  <Link to={`/pipelines/${pipeline.id}`}>{pipeline.name}</Link>
                </Title>
                <Text className="truncate max-w-lg">
                  {pipeline.description}
                </Text>
              </Flex>
            </Flex>

            <ManualRunDialog pipeline={pipeline} />
          </Flex>

          <TriggersList pipeline={pipeline} />
        </React.Fragment>
      ))}
    </>
  )
}

export default PipelinesList
