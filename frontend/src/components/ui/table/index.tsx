import { useEffect, createRef, PropsWithChildren } from 'react'
import {
  flexRender,
  getCoreRowModel as getDefaultCoreRowModel,
  useReactTable,
  Row,
  Table as TanTable,
  TableOptions,
  RowModel,
  SortDirection,
} from '@tanstack/react-table'
import {
  Icon,
  Table,
  TableBody,
  TableCell,
  TableFoot,
  TableFooterCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  Text,
} from '@tremor/react'
import { twMerge } from 'tailwind-merge'
import {
  ArrowDownIcon,
  ArrowUpIcon,
  ArrowsUpDownIcon,
} from '@heroicons/react/20/solid'

import { TableLoader } from '@/components/queries/Loaders'

interface CommonProps<T> {
  isHoverable?: boolean
  onRowClick?: (row: Row<T>) => any
  rowClassName?: string
}

interface TableRowsProps extends CommonProps<any> {
  table: TanTable<any>
}

interface Props<T = any>
  extends Omit<TableOptions<T>, 'getCoreRowModel'>,
    CommonProps<T>,
    PropsWithChildren {
  className?: string
  emptyMessage?: JSX.Element | string
  error?: any
  getCoreRowModel?: (table: TanTable<any>) => () => RowModel<T>
  hasNextPage?: boolean
  isLoading?: boolean
  onBottomReached?: () => any
  showFooter?: boolean
}

const SORTING_ICONS: Record<SortDirection, JSX.Element> = {
  asc: <Icon icon={ArrowUpIcon} className="p-0" />,
  desc: <Icon icon={ArrowDownIcon} className="p-0" />,
}

const UNSET_SORTING_ICON = (
  <Icon
    icon={ArrowsUpDownIcon}
    className="p-0 opacity-0 group-hover:opacity-50 transition-opacity"
    color="gray"
  />
)

const TableRows: React.FC<TableRowsProps> = ({
  isHoverable,
  onRowClick,
  rowClassName,
  table,
}) => {
  return table.getRowModel().rows.map((row) => (
    <TableRow
      key={row.id}
      className={twMerge(
        isHoverable &&
          'hover:bg-slate-50 dark:hover:bg-dark-tremor-background-subtle transition-colors',
        !!onRowClick && 'cursor-pointer',
        rowClassName
      )}
      onClick={onRowClick ? () => onRowClick(row) : undefined}
    >
      {row.getVisibleCells().map((cell) => (
        <TableCell key={cell.id}>
          {flexRender(cell.column.columnDef.cell, cell.getContext())}
        </TableCell>
      ))}
    </TableRow>
  ))
}

const DataTable: <T>(p: Props<T>) => React.ReactElement<Props<T>> = ({
  className,
  emptyMessage = <Text className="text-center opacity-70 italic">No data</Text>,
  error,
  getCoreRowModel,
  hasNextPage = false,
  isHoverable = false,
  isLoading = false,
  onRowClick,
  onBottomReached,
  rowClassName,
  showFooter = false,
  ...options
}) => {
  const table = useReactTable({
    getCoreRowModel: getCoreRowModel || getDefaultCoreRowModel(),
    ...options,
  })

  const infiniteScrollRef = createRef<HTMLTableRowElement>()

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entry) => {
        if (entry[0].isIntersecting) {
          onBottomReached && onBottomReached()
        }
      },
      {
        threshold: 0.5,
      }
    )

    if (infiniteScrollRef.current && onBottomReached) {
      observer.observe(infiniteScrollRef.current)

      return () => {
        observer.disconnect()
      }
    }
  }, [infiniteScrollRef, onBottomReached])

  const tableRows = table.getRowModel().rows
  const isEmpty = tableRows.length === 0
  const columnsCount = table.getFlatHeaders().length

  return (
    <Table className={twMerge('overflow-auto', className)}>
      <TableHead className="sticky top-0 bg-tremor-background dark:bg-dark-tremor-background shadow dark:shadow-tremor-dropdown z-[1]">
        {table.getHeaderGroups().map((headerGroup) => (
          <TableRow key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <TableHeaderCell
                key={header.id}
                className={twMerge(
                  'group',
                  !header.isPlaceholder &&
                    header.column.getCanSort() &&
                    'cursor-pointer select-none'
                )}
                onClick={
                  !header.isPlaceholder
                    ? header.column.getToggleSortingHandler()
                    : undefined
                }
              >
                {header.isPlaceholder ? null : (
                  <div className="flex justify-between">
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                    {SORTING_ICONS[
                      header.column.getIsSorted() as SortDirection
                    ] ?? UNSET_SORTING_ICON}
                  </div>
                )}
              </TableHeaderCell>
            ))}
          </TableRow>
        ))}
      </TableHead>
      <TableBody>
        {isLoading ? (
          <TableLoader columns={columnsCount} />
        ) : (
          error && (
            <TableRow>
              <TableCell colSpan={columnsCount}>{error}</TableCell>
            </TableRow>
          )
        )}

        {!isEmpty ? (
          <TableRows
            table={table}
            isHoverable={isHoverable}
            onRowClick={onRowClick}
            rowClassName={rowClassName}
          />
        ) : (
          <TableRow>
            <TableCell colSpan={columnsCount}>{emptyMessage}</TableCell>
          </TableRow>
        )}

        {/* Infinite scroll sensor */}
        {!isEmpty && (
          <TableRow ref={infiniteScrollRef}>
            <TableCell colSpan={columnsCount}>
              <Text className="text-center opacity-70 italic">
                {hasNextPage ? 'Loading more items...' : 'All items loaded'}
              </Text>
            </TableCell>
          </TableRow>
        )}
      </TableBody>

      {showFooter && (
        <TableFoot>
          {table.getFooterGroups().map((footerGroup) => (
            <TableRow key={footerGroup.id}>
              {footerGroup.headers.map((header) => (
                <TableFooterCell key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.footer,
                        header.getContext()
                      )}
                </TableFooterCell>
              ))}
            </TableRow>
          ))}
        </TableFoot>
      )}
    </Table>
  )
}

export default DataTable
