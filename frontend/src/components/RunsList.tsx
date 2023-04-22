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
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import useWebSocket from 'react-use-websocket'

import { PipelineRun, WebSocketMessage } from '@/types'
import { formatDateTime } from '@/utils'
import StatusBadge from './StatusBadge'
import { getWebsocketUrl } from '@/repository'

interface Props {
  pipelineId?: string
  runs: PipelineRun[]
  triggerId?: string
}

const Timer: React.FC<{ startTime: Date }> = ({ startTime }) => {
  const [time, setTime] = useState(Date.now() - startTime.getTime())

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(Date.now() - startTime.getTime())
    }, 500)

    return () => {
      clearInterval(interval)
    }
  })

  return <span>{(time / 1000).toFixed(2)}</span>
}

const RunsList: React.FC<Props> = ({ pipelineId, runs: _runs, triggerId }) => {
  const [runs, setRuns] = useState(_runs)
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { lastJsonMessage } = useWebSocket(getWebsocketUrl().toString())

  const onWsMessage = useCallback(
    (message: WebSocketMessage) => {
      const { data, type } = message

      if (type !== 'run-update') {
        return
      }

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
    if (lastJsonMessage) {
      onWsMessage(lastJsonMessage as any)
    }
  }, [lastJsonMessage])

  useEffect(() => {
    if (_runs.length) {
      setRuns(_runs)
    }
  }, [_runs])

  return (
    <Card>
      <Title>Runs</Title>

      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell className="text-right">#</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
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
              <TableCell>
                <Text>{formatDateTime(run.start_time)}</Text>
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
