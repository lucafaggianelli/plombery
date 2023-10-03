import { UseQueryResult, useQueryClient } from '@tanstack/react-query'
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
} from '@tremor/react'
import { formatDistanceToNow, differenceInDays } from 'date-fns'
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useSocket } from '@/socket'
import { PipelineRun, WebSocketMessage } from '@/types'
import { formatDateTime } from '@/utils'
import StatusBadge from './StatusBadge'
import Timer from './Timer'

interface Props {
  pipelineId?: string
  query: UseQueryResult<PipelineRun[], unknown>
  triggerId?: string
}

const RunsList: React.FC<Props> = ({
  pipelineId,
  query,
  triggerId,
}) => {
  const [runs, setRuns] = useState<PipelineRun[]>(query.data || [])
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { lastMessage } = useSocket('run-update')

  const onWsMessage = useCallback(
    (message: WebSocketMessage) => {
      const { data, type } = message

      data.run.start_time = new Date(data.run.start_time)
      data.run.trigger_id = data.trigger

      if (data.run.status === 'running') {
        setRuns([data.run, ...runs])
      } else {
        let oldRuns = [...runs]
        const i = oldRuns.findIndex((run) => run.id === data.run.id)

        if (i >= 0) {
          oldRuns[i] = data.run
        } else {
          oldRuns = [data.run, ...oldRuns]
        }

        setRuns(oldRuns)

        queryClient.invalidateQueries({
          queryKey: ['runs', pipelineId, triggerId],
        })
      }
    },
    [pipelineId, queryClient, runs, triggerId]
  )

  useEffect(() => {
    if (lastMessage) {
      onWsMessage(lastMessage)
    }
  }, [lastMessage])

  useEffect(() => {
    if (query.data?.length) {
      setRuns(query.data)
    }
  }, [query.data])

  return (
    <Card>
      <Title>Runs</Title>

      <Table className="overflow-auto max-h-[50vh]">
        <TableHead className="sticky top-0 bg-tremor-background dark:bg-dark-tremor-background shadow dark:shadow-tremor-dropdown z-10">
          <TableRow>
            <TableHeaderCell className="text-right">#</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
            {!pipelineId && <TableHeaderCell>Pipeline</TableHeaderCell>}
            {!triggerId && <TableHeaderCell>Trigger</TableHeaderCell>}
            <TableHeaderCell>Started at</TableHeaderCell>
            <TableHeaderCell className="text-right">Duration</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {runs.map((run) => (
            <TableRow
              key={run.id}
              className="cursor-pointer hover:bg-slate-50 dark:hover:bg-dark-tremor-background-subtle transition-colors"
              onClick={() =>
                navigate(
                  `/pipelines/${run.pipeline_id}/triggers/${run.trigger_id}/runs/${run.id}`
                )
              }
            >
              <TableCell className="text-right">{run.id}</TableCell>
              <TableCell>
                <StatusBadge status={run.status} />
              </TableCell>
              {!pipelineId && (
                <TableCell>
                  <Link
                    to={`/pipelines/${run.pipeline_id}`}
                    className="link--arrow"
                    title="View pipeline details"
                    onClick={(event) => event.stopPropagation()}
                  >
                    {run.pipeline_id}
                  </Link>
                </TableCell>
              )}
              {!triggerId && (
                <TableCell>
                  <Link
                    to={`/pipelines/${run.pipeline_id}/triggers/${run.trigger_id}`}
                    className="link--arrow"
                    title="View trigger details"
                    onClick={(event) => event.stopPropagation()}
                  >
                    {run.trigger_id}
                  </Link>
                </TableCell>
              )}
              <TableCell title={formatDateTime(run.start_time, true)}>
                <Text>
                  {differenceInDays(new Date(), run.start_time) <= 1
                    ? formatDistanceToNow(run.start_time, {
                        addSuffix: true,
                        includeSeconds: true,
                      })
                    : formatDateTime(run.start_time)}
                </Text>
              </TableCell>
              <TableCell className="text-right">
                {run.status !== 'running' ? (
                  (run.duration / 1000).toFixed(2)
                ) : (
                  <Timer startTime={run.start_time} />
                )}{' '}
                s
              </TableCell>
            </TableRow>
          ))}

          {query.isFetching &&
            new Array(10).fill(1).map((_, i) => (
              <TableRow className="animate-pulse" key={i}>
                <TableCell>
                  <div className="h-2 py-2 bg-slate-700 rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-2 py-2 bg-slate-700 rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-2 py-2 bg-slate-700 rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-2 py-2 bg-slate-700 rounded" />
                </TableCell>
                {pipelineId && (
                  <TableCell>
                    <div className="h-2 py-2 bg-slate-700 rounded" />
                  </TableCell>
                )}
                {triggerId && (
                  <TableCell>
                    <div className="h-2 py-2 bg-slate-700 rounded" />
                  </TableCell>
                )}
              </TableRow>
            ))}
        </TableBody>
      </Table>
    </Card>
  )
}

export default RunsList
