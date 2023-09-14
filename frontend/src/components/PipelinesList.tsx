import { useQuery } from '@tanstack/react-query'
import { Text, Title, Card, List, Bold, ListItem } from '@tremor/react'
import { formatDistanceToNow } from 'date-fns'
import { Link } from 'react-router-dom'
import React from 'react'

import { listPipelines } from '@/repository'
import ManualRunDialog from './ManualRunDialog'

const PipelinesList: React.FC = () => {
  const query = useQuery(listPipelines())

  if (query.isLoading) return <div>Loading...</div>

  if (query.isError) return <div>An error has occurred</div>

  const pipelines = query.data

  return (
    <Card>
      <Title>Pipelines</Title>

      <List>
        {pipelines.map((pipeline) => (
          <ListItem key={pipeline.id} className="gap-x-1">
            <div className="min-w-0">
              <Text className="truncate">
                <Bold>
                  <Link to={`/pipelines/${pipeline.id}`}>{pipeline.name}</Link>
                </Bold>
              </Text>
              {pipeline.description && (
                <Text className="truncate">{pipeline.description}</Text>
              )}
            </div>

            {pipeline.hasTrigger() && (
              <div
                className="min-w-0"
                title={pipeline.getNextFireTime()?.toString()}
              >
                <Text className="truncate">Next fire time</Text>
                <Text className="truncate">
                  <Bold>
                    {formatDistanceToNow(pipeline.getNextFireTime()!, {
                      addSuffix: true,
                      includeSeconds: true,
                    })}
                  </Bold>
                </Text>
              </div>
            )}

            <ManualRunDialog pipeline={pipeline} />
          </ListItem>
        ))}
      </List>
    </Card>
  )
}

export default PipelinesList
