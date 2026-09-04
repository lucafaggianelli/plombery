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
import { useCallback, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router'

import { socket } from '@/socket'
import { RunsPages, RunsQuery, runsQueryKey } from '@/repository'
import { formatDateTime } from '@/utils'
import StatusBadge from './StatusBadge'
import Timer from './Timer'
import ErrorAlert from './queries/Error'
import { TableLoader, TextLoader } from './queries/Loaders'

interface Props {
  pipelineId?: string
  query: RunsQuery
  triggerId?: string
}

/**
 * How far ahead of the bottom of the list the next page starts loading, so
 * that it's usually there by the time the user scrolls down to it.
 */
const LOAD_MORE_MARGIN = '200px'

const RunsList: React.FC<Props> = ({ pipelineId, query, triggerId }) => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const tableRef = useRef<HTMLTableElement>(null)
  const loadMoreRef = useRef<HTMLTableRowElement>(null)

  const { fetchNextPage, hasNextPage, isFetchingNextPage } = query

  const onWsMessage = useCallback(
    (data: any) => {
      // Ignore malformed events rather than throwing inside the socket handler:
      // an exception here would stop the list from ever updating again, leaving
      // a finished run displayed as still running.
      if (!data?.run?.id) {
        return
      }

      // The event is broadcast for every run, while this list may be showing
      // a single pipeline or a single trigger
      if (
        (pipelineId && data.pipeline !== pipelineId) ||
        (triggerId && data.trigger !== triggerId)
      ) {
        return
      }

      const update = {
        ...data.run,
        start_time: data.run.start_time
          ? new Date(data.run.start_time)
          : undefined,
        pipeline_id: data.pipeline,
        trigger_id: data.trigger,
      }

      queryClient.setQueryData<RunsPages>(
        runsQueryKey(pipelineId, triggerId),
        (current) => {
          if (!current) {
            return current
          }

          let found = false

          const pages = current.pages.map((page) => {
            const i = page.findIndex((run) => run.id === update.id)

            if (i < 0) {
              return page
            }

            found = true
            const merged = [...page]
            // Merged, as the event only carries the fields that change
            merged[i] = { ...merged[i], ...update }

            return merged
          })

          if (found) {
            return { ...current, pages }
          }

          // A run nothing has seen yet is newer than every run on the first
          // page, which is the only place it can go
          return {
            ...current,
            pages: [[update, ...(pages[0] ?? [])], ...pages.slice(1)],
          }
        },
      )

      if (data.run.status !== 'running') {
        // The event carries only the fields that change, so refetch to pick
        // up the rest of a run that just finished
        queryClient.invalidateQueries({
          queryKey: runsQueryKey(pipelineId, triggerId),
        })
      }
    },
    [pipelineId, queryClient, triggerId],
  )

  useEffect(() => {
    socket.on('run-update', onWsMessage)

    return () => {
      socket.off('run-update', onWsMessage)
    }
  }, [onWsMessage])

  // Load the next page once the bottom of the list comes into view. The
  // scrolling element is the div Tremor wraps the table in, as that's what
  // carries the max height and the overflow.
  useEffect(() => {
    const loadMore = loadMoreRef.current
    const root = tableRef.current?.parentElement

    if (!loadMore || !root) {
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isFetchingNextPage) {
          fetchNextPage()
        }
      },
      { root, rootMargin: LOAD_MORE_MARGIN },
    )

    observer.observe(loadMore)

    return () => observer.disconnect()
  }, [fetchNextPage, hasNextPage, isFetchingNextPage])

  const runs = query.data ?? []
  const numberOfColumns = 5 + Number(!pipelineId) + Number(!triggerId)

  return (
    <Card className="p-0 overflow-hidden">
      <Title className="p-6">Runs</Title>

      <Table ref={tableRef} className="overflow-auto max-h-[50vh]">
        <TableHead className="sticky top-0 bg-tremor-background dark:bg-dark-tremor-background shadow dark:shadow-tremor-dropdown z-10">
          <TableRow>
            <TableHeaderCell className="text-right">#</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
            {!pipelineId && <TableHeaderCell>Pipeline</TableHeaderCell>}
            {!triggerId && <TableHeaderCell>Trigger</TableHeaderCell>}
            <TableHeaderCell>Started at</TableHeaderCell>
            <TableHeaderCell className="text-right">Duration</TableHeaderCell>
            <TableHeaderCell>Version</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {runs.map((run) => (
            <TableRow
              key={run.id}
              className="cursor-pointer hover:bg-slate-50 dark:hover:bg-dark-tremor-background-subtle transition-colors"
              onClick={() =>
                navigate(
                  `/pipelines/${run.pipeline_id}/triggers/${run.trigger_id}/runs/${run.id}`,
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
              <TableCell
                title={
                  run.start_time
                    ? formatDateTime(run.start_time, true)
                    : undefined
                }
              >
                <Text>
                  {run.start_time
                    ? differenceInDays(new Date(), run.start_time) <= 1
                      ? formatDistanceToNow(run.start_time, {
                          addSuffix: true,
                          includeSeconds: true,
                        })
                      : formatDateTime(run.start_time)
                    : '-'}
                </Text>
              </TableCell>
              <TableCell className="text-right">
                {run.status !== 'running' ? (
                  (run.duration / 1000).toFixed(2)
                ) : run.start_time ? (
                  <Timer startTime={run.start_time} />
                ) : (
                  '-'
                )}{' '}
                s
              </TableCell>

              <TableCell>
                {run.pipeline_version && (
                  <Text className="text-xs font-mono text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                    {run.pipeline_version}
                  </Text>
                )}
              </TableCell>
            </TableRow>
          ))}

          {query.isPending && <TableLoader columns={numberOfColumns} />}

          {/* Both the trigger of the next page and its placeholder: it sits
              right below the last run, so it scrolls into view exactly when
              there is more to load */}
          {hasNextPage && (
            <TableRow ref={loadMoreRef} className="animate-pulse">
              <TableCell colSpan={numberOfColumns}>
                <TextLoader />
              </TableCell>
            </TableRow>
          )}

          {query.isError && (
            <TableRow>
              <TableCell colSpan={numberOfColumns}>
                <ErrorAlert query={query} />
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
}

export default RunsList
