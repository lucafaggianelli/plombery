import { Metric, TableCell, TableRow, Text } from '@tremor/react'
import { twMerge } from 'tailwind-merge'

const base = 'animate-pulse rounded'
const bgColor = 'bg-slate-200 dark:bg-slate-700'

interface Props {
  className?: string
}

export const TrackerLoader: React.FC<Props> = ({ className }) => (
  <div className={twMerge('h-10', base, bgColor, className)} />
)

export const ChartLoader: React.FC<Props> = ({ className }) => (
  <div className={twMerge('h-28', base, bgColor, className)} />
)

export const TextLoader: React.FC<Props> = ({ className }) => (
  <Text className={twMerge(base, bgColor, className)}>&nbsp;</Text>
)

export const MetricLoader: React.FC<Props> = ({ className }) => (
  <Metric className={twMerge('w-24', base, bgColor, className)}>&nbsp;</Metric>
)

interface TableLoaderProps {
  columns?: number
  rows?: number
}

export const TableLoader: React.FC<TableLoaderProps> = ({columns = 6, rows = 10}) =>
  new Array(rows).fill(1).map((_, i) => (
    <TableRow className="animate-pulse" key={i}>
      {new Array(columns).fill(1).map((_, j) => (
        <TableCell key={j}>
          <TextLoader />
        </TableCell>
      ))}
    </TableRow>
  ))
