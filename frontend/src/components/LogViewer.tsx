import { useQuery } from '@tanstack/react-query'
import {
  Badge,
  Block,
  ColGrid,
  Color,
  MultiSelectBox,
  MultiSelectBoxItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  Text,
} from '@tremor/react'
import { useCallback, useState } from 'react'

import { getLogs } from '@/repository'
import { LogLevel, Pipeline, Trigger } from '@/types'
import { formatTimestamp } from '@/utils'
import TracebackInfoDialog from './TracebackInfoDialog'

interface Props {
  pipeline: Pipeline
  trigger: Trigger
  runId: number
}

const LOG_LEVELS_COLORS: Record<LogLevel, Color> = {
  DEBUG: 'slate',
  INFO: 'sky',
  WARNING: 'amber',
  ERROR: 'rose',
}

interface FilterType {
  levels: string[]
  tasks: string[]
}

const LogViewer: React.FC<Props> = ({ pipeline, trigger, runId }) => {
  const [filter, setFilter] = useState<FilterType>({ levels: [], tasks: [] })

  const query = useQuery({
    queryKey: ['logs', pipeline.id, trigger.id, runId],
    queryFn: () => getLogs(pipeline.id, trigger.id, runId),
    enabled: [pipeline.id, trigger.id, runId].every((x) => !!x),
    initialData: [],
  })

  const onFilterChange = useCallback((newFilter: Partial<FilterType>) => {
    setFilter((currentFilter) => ({ ...currentFilter, ...newFilter }))
  }, [])

  if (query.isLoading) {
    return <div>Loading...</div>
  }

  if (query.isError) {
    return <div>Error loading logs</div>
  }

  const logs = query.data.filter((log) => {
    return (
      (filter.levels.length === 0 || filter.levels.includes(log.level)) &&
      (filter.tasks.length === 0 || filter.tasks.includes(log.task))
    )
  })

  return (
    <>
      <ColGrid numColsMd={3} gapX="gap-x-6" gapY="gap-y-6">
        <Block>
          <Text>Tasks</Text>

          <MultiSelectBox<string>
            marginTop="mt-1"
            onValueChange={(tasks) => {
              onFilterChange({ tasks })
            }}
          >
            {pipeline.tasks.map((task) => (
              <MultiSelectBoxItem
                text={task.name}
                value={task.id}
                key={task.id}
              />
            ))}
          </MultiSelectBox>
        </Block>

        <Block>
          <Text>Log level</Text>

          <MultiSelectBox<string>
            marginTop="mt-1"
            onValueChange={(levels) => {
              onFilterChange({ levels })
            }}
          >
            {Object.keys(LOG_LEVELS_COLORS).map((level) => (
              <MultiSelectBoxItem text={level} value={level} key={level} />
            ))}
          </MultiSelectBox>
        </Block>
      </ColGrid>
      <div className="logs-table">
        <Table marginTop="mt-6">
          <TableHead>
            <TableRow>
              <TableHeaderCell>Time</TableHeaderCell>
              <TableHeaderCell>Level</TableHeaderCell>
              <TableHeaderCell>Task</TableHeaderCell>
              <TableHeaderCell>Message</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.map((log, i) => {
              const duration =
                i !== 0
                  ? log.timestamp.getTime() - logs[i - 1].timestamp.getTime()
                  : -1

              return (
                <TableRow key={log.id}>
                  <TableCell>
                    <span className="font-mono text-xs text-slate-500">
                      {formatTimestamp(log.timestamp)}
                    </span>
                    {duration >= 0 && (
                      <span className="font-mono text-xs text-slate-500 ml-2">
                        +{duration} ms
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge
                      text={log.level}
                      size="xs"
                      color={LOG_LEVELS_COLORS[log.level]}
                    />
                  </TableCell>
                  <TableCell>{log.task}</TableCell>
                  <TableCell>
                    <Text>{log.message}</Text>

                    {log.exc_info && <TracebackInfoDialog logEntry={log} />}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
    </>
  )
}

export default LogViewer
