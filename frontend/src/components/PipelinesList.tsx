import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  Text,
  Title,
  Badge,
  Flex,
  Button,
} from '@tremor/react'
import Link from 'next/link'
import React from 'react'
import { getPipelines } from '../repository'

import { Pipeline } from '../types'
import ManualRunDialog from './ManualRunDialog'

interface TriggersListProps {
  pipeline: Pipeline
}

const TriggersList: React.FC<TriggersListProps> = ({ pipeline }) => (
  <Card marginTop="mt-5">
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>Name</TableHeaderCell>
          <TableHeaderCell>Interval</TableHeaderCell>
          <TableHeaderCell>Next fire time</TableHeaderCell>
          <TableHeaderCell>Latest Status</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {pipeline.triggers.map((trigger) => (
          <TableRow key={trigger.name}>
            <TableCell>
              <Link href={`/pipelines/${pipeline.id}/triggers/${trigger.name}`}>
                {trigger.name}
              </Link>
            </TableCell>
            <TableCell>
              <Text>{trigger.interval}</Text>
            </TableCell>
            <TableCell>
              {trigger.paused ? (
                <Badge
                  text="Disabled"
                  color="amber"
                  tooltip="Re-enable the trigger setting paused=False"
                  size="xs"
                />
              ) : (
                trigger.next_fire_time.toString()
              )}
            </TableCell>
            <TableCell>
              <Badge text="Success" color="emerald" size="xs" />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </Card>
)

const PipelinesList: React.FC = () => {
  const query = useQuery({
    queryKey: ['pipelines'],
    queryFn: getPipelines,
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
            <Flex justifyContent="justify-start" spaceX="space-x-2">
              <Title>{pipeline.name}</Title>
              <Text>
                <span className="tr-block tr-truncate tr-max-w-lg">
                  {pipeline.description}
                </span>
              </Text>
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
