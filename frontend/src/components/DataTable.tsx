import { useMemo, useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'

interface Props {
  data: Record<string, any>[]
  /** CSS height of the scrolling area */
  height?: string
}

const ROW_HEIGHT = 32
const ROW_NUMBER_WIDTH = 56
const MIN_COLUMN_WIDTH = 96
const MAX_COLUMN_WIDTH = 320
const CHARACTER_WIDTH = 8
/** Rows looked at to guess a column width, so a huge output stays cheap */
const WIDTH_SAMPLE_SIZE = 50

/**
 * How a value is shown in a cell: primitives as they are, anything else as
 * JSON, so a nested object doesn't render as `[object Object]`.
 */
const formatValue = (value: unknown): string => {
  if (value === null || value === undefined) {
    return ''
  }

  return typeof value === 'object' ? JSON.stringify(value) : String(value)
}

/**
 * The columns of a set of rows, in the order the keys first appear.
 *
 * Task outputs are plain JSON, so rows are not guaranteed to share a shape:
 * taking the union rather than the keys of the first row keeps the columns
 * that only later rows have.
 */
const getColumns = (data: Record<string, any>[]) => {
  const keys: string[] = []
  const seen = new Set<string>()

  for (const row of data) {
    for (const key of Object.keys(row ?? {})) {
      if (!seen.has(key)) {
        seen.add(key)
        keys.push(key)
      }
    }
  }

  const sample = data.slice(0, WIDTH_SAMPLE_SIZE)

  return keys.map((key) => {
    const longest = sample.reduce(
      (max, row) => Math.max(max, formatValue(row?.[key]).length),
      key.length
    )

    return {
      key,
      width: Math.min(
        Math.max(longest * CHARACTER_WIDTH + 16, MIN_COLUMN_WIDTH),
        MAX_COLUMN_WIDTH
      ),
    }
  })
}

/**
 * A read-only table for a task output that is a list of records.
 *
 * Rows are virtualized, so an output with many thousands of records renders
 * as fast as a small one.
 */
export default function DataTable({ data, height = '70vh' }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null)

  const columns = useMemo(() => getColumns(data), [data])

  const virtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 12,
  })

  const totalWidth =
    ROW_NUMBER_WIDTH + columns.reduce((sum, column) => sum + column.width, 0)

  const cellClasses =
    'shrink-0 truncate px-2 leading-8 border-r border-tremor-border dark:border-dark-tremor-border'

  return (
    <div>
      <div
        ref={scrollRef}
        style={{ height, maxWidth: '75vw' }}
        className="overflow-auto rounded-lg border border-tremor-border dark:border-dark-tremor-border bg-tremor-background dark:bg-dark-tremor-background"
      >
        {/* `minWidth` so a table narrower than the dialog still spans it */}
        <div style={{ minWidth: totalWidth }} className="text-sm">
          <div className="sticky top-0 z-20 flex h-8 font-medium bg-tremor-background-subtle dark:bg-dark-tremor-background-subtle border-b border-tremor-border dark:border-dark-tremor-border">
            <div
              style={{ width: ROW_NUMBER_WIDTH }}
              className={`${cellClasses} sticky left-0 z-10 bg-tremor-background-subtle dark:bg-dark-tremor-background-subtle`}
            />

            {columns.map((column) => (
              <div
                key={column.key}
                style={{ width: column.width }}
                className={cellClasses}
                title={column.key}
              >
                {column.key}
              </div>
            ))}
          </div>

          {/* `relative`, so the rows are placed against the body of the table
              rather than against the header that precedes them */}
          <div
            style={{ height: virtualizer.getTotalSize() }}
            className="relative"
          >
            {virtualizer.getVirtualItems().map((virtualRow) => {
              const row = data[virtualRow.index]

              return (
                <div
                  key={virtualRow.key}
                  style={{
                    height: virtualRow.size,
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                  className="absolute top-0 left-0 flex w-full border-b border-tremor-border dark:border-dark-tremor-border hover:bg-tremor-background-muted dark:hover:bg-dark-tremor-background-muted"
                >
                  <div
                    style={{ width: ROW_NUMBER_WIDTH }}
                    className={`${cellClasses} sticky left-0 z-10 text-right tabular-nums bg-tremor-background-subtle dark:bg-dark-tremor-background-subtle text-tremor-content-subtle dark:text-dark-tremor-content-subtle`}
                  >
                    {virtualRow.index + 1}
                  </div>

                  {columns.map((column) => {
                    const value = formatValue(row?.[column.key])

                    return (
                      <div
                        key={column.key}
                        style={{ width: column.width }}
                        className={cellClasses}
                        title={value}
                      >
                        {value}
                      </div>
                    )
                  })}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <p className="mt-2 text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
        {data.length.toLocaleString()} {data.length === 1 ? 'row' : 'rows'} ×{' '}
        {columns.length} {columns.length === 1 ? 'column' : 'columns'}
      </p>
    </div>
  )
}
