import { PipelineRun } from '@/types'
import { formatDateTime, STATUS_COLORS } from '@/utils'
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
  Badge,
} from '@tremor/react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

interface Props {
  pipelineId: string
  runs: PipelineRun[]
  triggerId: string
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
          queryKey: ['runs', triggerId, pipelineId],
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
    <Card marginTop="mt-5">
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell textAlignment="text-right">#</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
            <TableHeaderCell>Started at</TableHeaderCell>
            <TableHeaderCell textAlignment="text-right">
              Duration
            </TableHeaderCell>
            <TableHeaderCell> </TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {runs.map((run) => (
            <TableRow key={run.id}>
              <TableCell textAlignment="text-right">{run.id}</TableCell>
              <TableCell>
                <Badge text={run.status} color={STATUS_COLORS[run.status]} />
              </TableCell>
              <TableCell>
                <Text>{formatDateTime(run.start_time)}</Text>
              </TableCell>
              <TableCell textAlignment="text-right">
                {run.status !== 'running' ? (
                  (run.duration / 1000).toFixed(2)
                ) : (
                  <Timer startTime={run.start_time} />
                )}{' '}
                s
              </TableCell>
              <TableCell>
                <Link
                  to={`/pipelines/${pipelineId}/triggers/${triggerId}/runs/${run.id}`}
                >
                  Logs
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  )
}

export default RunsList
