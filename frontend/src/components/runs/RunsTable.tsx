import { UseQueryResult, useQueryClient } from '@tanstack/react-query'
import { Card, Title } from '@tremor/react'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { HTTPError } from 'ky'

import { socket } from '@/socket'
import { PipelineRun } from '@/types'
import DataTable from '@/components/ui/table'
import { columns } from './tableColumnsDefinitions'

interface Props {
  pipelineId?: string
  query: UseQueryResult<PipelineRun[], HTTPError>
  triggerId?: string
}

const RunsList: React.FC<Props> = ({ pipelineId, query, triggerId }) => {
  const [runs, setRuns] = useState<PipelineRun[]>(query.data || [])
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const onWsMessage = useCallback(
    (data: any) => {
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
    socket.on('run-update', onWsMessage)

    return () => {
      socket.off('run-update', onWsMessage)
    }
  }, [pipelineId])

  useEffect(() => {
    if (query.data?.length) {
      setRuns(query.data)
    }
  }, [query.data])

  return (
    <Card>
      <Title>Runs</Title>

      <DataTable
        columns={columns}
        data={runs}
        isHoverable
        isLoading={query.isFetching || query.isLoading}
        error={query.error}
        onRowClick={(row) => {
          navigate(
            `/pipelines/${row.original.pipeline_id}/triggers/${row.original.trigger_id}/runs/${row.original.id}`
          )
        }}
        initialState={{
          columnVisibility: {
            pipeline_id: !pipelineId,
            trigger_id: !triggerId,
          },
        }}
      />
    </Card>
  )
}

export default RunsList
