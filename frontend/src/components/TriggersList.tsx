import {
  Button,
  Card,
  Icon,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  Text,
  Title,
} from '@tremor/react'
import { formatDistanceToNow } from 'date-fns'
import { useNavigate } from 'react-router-dom'

import { Pipeline } from '@/types'
import { ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline'

interface Props {
  pipeline: Pipeline
}

const TriggersList: React.FC<Props> = ({ pipeline }) => {
  const navigate = useNavigate()

  return (
    <Card>
      <Title>Triggers</Title>

      <Table>
        <TableHead className="sticky top-0 bg-tremor-background dark:bg-dark-tremor-background shadow dark:shadow-tremor-dropdown z-10">
          <TableRow>
            <TableHeaderCell>Name</TableHeaderCell>
            <TableHeaderCell>Interval</TableHeaderCell>
            <TableHeaderCell>Next Fire Time</TableHeaderCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {pipeline.triggers.map((trigger) => (
            <TableRow
              key={trigger.id}
              className="cursor-pointer hover:bg-slate-50 dark:hover:bg-dark-tremor-background-subtle transition-colors"
              onClick={() =>
                navigate(`/pipelines/${pipeline.id}/triggers/${trigger.id}`)
              }
            >
              <TableCell>{trigger.name}</TableCell>
              <TableCell>
                <Text>{trigger.schedule}</Text>
              </TableCell>
              <TableCell>
                {formatDistanceToNow(pipeline.getNextFireTime()!, {
                  includeSeconds: true,
                  addSuffix: true,
                })}
              </TableCell>
            </TableRow>
          ))}

          {pipeline.triggers.length === 0 && (
            <TableRow>
              <TableCell colSpan={3}>
                <Text className="text-center italic">
                  This pipeline has no triggers, can be run only manually.
                </Text>

                <div className="text-center mt-2 text-sm">
                  <a
                    href="https://lucafaggianelli.github.io/plombery/triggers/"
                    target="_blank"
                    className="inline-flex items-center gap-2 bg-indigo-50/30 hover:bg-indigo-50 dark:bg-indigo-950/50 dark:hover:bg-indigo-950 rounded-sm px-4 py-2 text-indigo-500 transition-colors duration-300 cursor-pointer no-underline"
                    rel="noopener noreferrer"
                  >
                    How to create triggers
                    <Icon icon={ArrowTopRightOnSquareIcon} size="sm" className='p-0' color='indigo' />
                  </a>
                </div>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
}

export default TriggersList
