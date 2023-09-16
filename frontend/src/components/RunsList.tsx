import { useQueryClient } from '@tanstack/react-query'
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
  runs: PipelineRun[]
  triggerId?: string
}

const RunsList: React.FC<Props> = ({ pipelineId, runs: _runs, triggerId }) => {
  const [runs, setRuns] = useState(_runs)
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
    if (_runs.length) {
      setRuns(_runs)
    }
  }, [_runs])

  return (
    <Card>
      <Title>Runs</Title>

      <Table className="overflow-auto max-h-[50vh]">
        <TableHead className="sticky top-0 bg-white shadow">
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
              className="cursor-pointer hover:bg-slate-50 transition-colors"
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
              <TableCell title={formatDateTime(run.start_time)}>
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
        </TableBody>
      </Table>
    </Card>
  )
}

export default RunsList
