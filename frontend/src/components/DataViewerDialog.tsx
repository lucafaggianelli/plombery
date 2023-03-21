import React, { Suspense } from 'react'
import { Button, Text } from '@tremor/react'
import { useQuery } from '@tanstack/react-query'

import { HTTPError } from '@/http-client'
import { getRunData } from '@/repository'
import Dialog from './Dialog'

interface Props {
  runId: number
  taskId: string
  open: boolean
  onClose: () => any
}

const HotTable = React.lazy(() => import('./HandsonTable.js'))

const DataViewerDialog: React.FC<Props> = ({
  runId,
  taskId,
  open,
  onClose,
}) => {
  const query = useQuery<any, HTTPError>({
    queryKey: ['getRunData', { runId, taskId }],
    queryFn: () => getRunData(runId, taskId),
    enabled: open,
  })

  return (
    <>
      <Dialog
        title={taskId}
        subtitle="View data"
        isOpen={open}
        maxWidth="90%"
        minWidth="90%"
        footer={
          <Button variant="secondary" color="indigo" onClick={() => onClose()}>
            Close
          </Button>
        }
        onClose={onClose}
      >
        {!query.isLoading && !query.isError && (
          <Suspense fallback={<div>Loading...</div>}>
            <HotTable
              data={query.data}
              rowHeaders={true}
              colHeaders={Object.keys(query.data[0])}
              height="70vh"
              width="100%"
              licenseKey="non-commercial-and-evaluation"
            />
          </Suspense>
        )}

        {query.isError &&
          (query.error.response.status === 404 ? (
            <Text>The task has no data</Text>
          ) : (
            <Text color="rose">
              Error fetching task data: {query.error.message}
            </Text>
          ))}
      </Dialog>
    </>
  )
}

export default DataViewerDialog
