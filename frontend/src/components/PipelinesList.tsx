import { useQuery } from '@tanstack/react-query'
import { Text, Title, Card, List, Bold, ListItem, Icon } from '@tremor/react'
import { formatDistanceToNow } from 'date-fns'
import { Link } from 'react-router-dom'
import React from 'react'

import { listPipelines } from '@/repository'
import ManualRunDialog from './ManualRunDialog'
import { ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline'

const PipelinesList: React.FC = () => {
  const query = useQuery(listPipelines())

  if (query.isPending) return <div>Loading...</div>

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

        {pipelines.length === 0 && (
          <div className='mt-4'>
            <Text className="text-center italic">
              There are no pipelines, you can't do much.
            </Text>

            <div className="text-center mt-2 text-sm">
              <a
                href="https://lucafaggianelli.github.io/plombery/pipelines/"
                target="_blank"
                className="inline-flex items-center gap-2 bg-indigo-50/30 hover:bg-indigo-50 dark:bg-indigo-950/50 dark:hover:bg-indigo-950 rounded-sm px-4 py-2 text-indigo-500 transition-colors duration-300 cursor-pointer no-underline"
                rel="noopener noreferrer"
              >
                How to create pipelines
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
    </Card>
  )
}

export default PipelinesList
