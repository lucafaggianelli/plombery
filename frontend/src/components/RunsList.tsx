import { PipelineRun } from '@/types'
import { formatDateTime } from '@/utils'
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
import { Link } from 'react-router-dom'
import StatusBadge from './StatusBadge'

interface Props {
  pipelineId: string
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

const ws =
  typeof window !== 'undefined'
    ? new WebSocket('ws://localhost:8000/api/ws')
    : undefined

const RunsList: React.FC<Props> = ({ pipelineId, runs: _runs, triggerId }) => {
  const [runs, setRuns] = useState(_runs)
  const queryClient = useQueryClient()

  const onWsMessage = useCallback(
    (event: MessageEvent) => {
      const { data } = JSON.parse(event.data)

      data.run.start_time = new Date(data.run.start_time)

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
    ws?.addEventListener('message', onWsMessage)

    return () => {
      ws?.removeEventListener('message', onWsMessage)
    }
  }, [onWsMessage])

  useEffect(() => {
    if (_runs.length) {
      setRuns(_runs)
    }
  }, [_runs])

  return (
    <Card className="mt-5">
      <Title>Runs</Title>

      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell className="text-right">#</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
            {!triggerId && <TableHeaderCell>Trigger</TableHeaderCell>}
            <TableHeaderCell>Started at</TableHeaderCell>
            <TableHeaderCell className="text-right">
              Duration
            </TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {runs.map((run) => (
            <TableRow key={run.id}>
              <TableCell className="text-right">
                <Link
                  to={`/pipelines/${pipelineId}/triggers/${run.trigger_id}/runs/${run.id}`}
                  className="hover:text-indigo-500 hover:border-b-indigo-500 border-b border-b-transparent transition-colors"
                >
                  {run.id}
                </Link>
              </TableCell>
              <TableCell>
                <StatusBadge status={run.status} />
              </TableCell>
              {!triggerId && (
                <TableCell>
                  <Link
                    to={`/pipelines/${pipelineId}/triggers/${run.trigger_id}`}
                    className="hover:text-indigo-500 hover:border-b-indigo-500 border-b border-b-transparent transition-colors"
                    title="View trigger details"
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
