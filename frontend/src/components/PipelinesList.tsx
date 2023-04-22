import { useQuery } from '@tanstack/react-query'
import { Text, Title, Flex, Card, List, Bold, ListItem } from '@tremor/react'
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
    <Card>
      <Title>Pipelines</Title>

      <List>
        {pipelines.map((pipeline) => (
          <ListItem key={pipeline.id}>
            <div>
              <Text>
                <Bold>
                  <Link to={`/pipelines/${pipeline.id}`}>{pipeline.name}</Link>
                </Bold>
              </Text>
              {pipeline.description && (
                <Text className="truncate">{pipeline.description}</Text>
              )}
            </div>

            <ManualRunDialog pipeline={pipeline} />
          </ListItem>
        ))}
      </List>
    </Card>
  )
}

export default PipelinesList
