import { useQuery } from '@tanstack/react-query'
import {
  Badge,
  Color,
  Flex,
  Grid,
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
import { LogLevel, Pipeline } from '@/types'
import { formatTimestamp, getTasksColors } from '@/utils'
import TracebackInfoDialog from './TracebackInfoDialog'

interface Props {
  pipeline: Pipeline
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

const LogViewer: React.FC<Props> = ({ pipeline, runId }) => {
  const [filter, setFilter] = useState<FilterType>({ levels: [], tasks: [] })

  const query = useQuery({
    queryKey: ['logs', runId],
    queryFn: () => getLogs(runId),
    enabled: !!runId,
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

  const tasksColors = getTasksColors(pipeline.tasks)

  return (
    <>
      <Grid numColsMd={3} className="gap-6">
        <div>
          <Text>Tasks</Text>

          <MultiSelectBox
            className="mt-1"
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
        </div>

        <div>
          <Text>Log level</Text>

          <MultiSelectBox
            className="mt-1"
            onValueChange={(levels) => {
              onFilterChange({ levels })
            }}
          >
            {Object.keys(LOG_LEVELS_COLORS).map((level) => (
              <MultiSelectBoxItem text={level} value={level} key={level} />
            ))}
          </MultiSelectBox>
        </div>
      </Grid>

      <div className="logs-table">
        <Table className="mt-6">
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
                    <Badge size="xs" color={LOG_LEVELS_COLORS[log.level]}>
                      {log.level}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Flex>
                      <div
                        className={`h-2 w-2 mr-2 rounded-full ${
                          tasksColors[log.task]
                        }`}
                      />
                      {log.task}
                    </Flex>
                  </TableCell>
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
