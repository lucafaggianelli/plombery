import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Badge,
  Color,
  Flex,
  Grid,
  Icon,
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
import { createRef, useCallback, useEffect, useState } from 'react'

import { getLogs } from '@/repository'
import { useSocket } from '@/socket'
import {
  LogEntry,
  LogLevel,
  Pipeline,
  PipelineRun,
  WebSocketMessage,
} from '@/types'
import { formatNumber, formatTime, getTasksColors } from '@/utils'
import TracebackInfoDialog from './TracebackInfoDialog'
import { BarsArrowDownIcon } from '@heroicons/react/24/outline'

interface Props {
  pipeline: Pipeline
  run: PipelineRun
}

/**
 * If the user scrolls to the bottom and arrives
 * that close to the bottom then the scroll lock is
 * activated.
 */
const SCROLL_LOCK_THRESHOLD = 30

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

const LogViewer: React.FC<Props> = ({ pipeline, run }) => {
  const [filter, setFilter] = useState<FilterType>({ levels: [], tasks: [] })
  const [scrollToBottom, setScrollToBottom] = useState(true)
  const { lastMessage } = useSocket(`logs.${run.id}`)
  const queryClient = useQueryClient()

  const logsBottomRef = createRef<HTMLTableRowElement>()
  const tableRef = createRef<HTMLTableElement>()

  const query = useQuery(getLogs(run.id))

  const onWsMessage = useCallback(
    (message: WebSocketMessage) => {
      const { data } = message

      queryClient.setQueryData<LogEntry[]>(['logs', run.id], (oldLogs = []) => {
        const log: LogEntry = JSON.parse(data)
        log.id = oldLogs.length
        log.timestamp = new Date(log.timestamp)
        return [...oldLogs, log]
      })
    },
    [run.id]
  )

  const onMouseScroll = useCallback(
    (e: Event) => {
      const element = tableRef.current?.parentElement
      if (!element) {
        return
      }

      const event = e as WheelEvent

      // Add deltaY as the scrollTop doesn't include it at this point
      let scrollBottom = Math.max(
        element.scrollTop + element.clientHeight + event.deltaY,
        0
      )

      scrollBottom = Math.min(scrollBottom, element.scrollHeight)

      const userScrolledToBottom =
        element.scrollHeight - scrollBottom < SCROLL_LOCK_THRESHOLD

      setScrollToBottom(userScrolledToBottom)
    },
    [tableRef]
  )

  useEffect(() => {
    tableRef.current?.parentElement?.addEventListener('wheel', onMouseScroll)

    return () => {
      tableRef.current?.parentElement?.removeEventListener(
        'wheel',
        onMouseScroll
      )
    }
  }, [tableRef])

  useEffect(() => {
    if (scrollToBottom) {
      logsBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  })

  useEffect(() => {
    if (lastMessage) {
      onWsMessage(lastMessage)
    }
  }, [lastMessage])

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

  const hasLiveLogs = ['running', 'pending'].includes(run.status)

  return (
    <Flex flexDirection="col" alignItems="stretch" style={{ maxHeight: 600 }}>
      <Grid numColsMd={3} className="gap-6 items-start">
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

        {hasLiveLogs && (
          <Flex justifyContent="end" className="order-first md:order-last">
            <Icon
              icon={BarsArrowDownIcon}
              variant="light"
              color={scrollToBottom ? 'indigo' : 'gray'}
              tooltip="Automatically scroll to the latest logs. Click to toggle"
              className="mr-4"
              style={{
                cursor: 'pointer',
              }}
              onClick={() => {
                setScrollToBottom(!scrollToBottom)
              }}
            />

            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
            </span>

            <Text className="ml-2 opacity-80">Live logs</Text>
          </Flex>
        )}
      </Grid>

      <Table className="mt-6 flex-grow" ref={tableRef}>
        <TableHead className="sticky top-0 bg-white shadow z-10">
          <TableRow>
            <TableHeaderCell className="bg-white">Time</TableHeaderCell>
            <TableHeaderCell className="bg-white">Level</TableHeaderCell>
            <TableHeaderCell className="bg-white">Task</TableHeaderCell>
            <TableHeaderCell className="bg-white">Message</TableHeaderCell>
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
                  <Text className="font-mono text-xs">
                    <span title={formatTime(log.timestamp, true)}>
                      {formatTime(log.timestamp)}
                    </span>

                    {duration >= 0 && (
                      <span className="text-slate-400 ml-2">
                        +{formatNumber(duration)} ms
                      </span>
                    )}
                  </Text>
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
                <TableCell className="w-full">
                  <Text>{log.message}</Text>

                  {log.exc_info && <TracebackInfoDialog logEntry={log} />}
                </TableCell>
              </TableRow>
            )
          })}
          <tr ref={logsBottomRef} />
        </TableBody>
      </Table>
    </Flex>
  )
}

export default LogViewer
