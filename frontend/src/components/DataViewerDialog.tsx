import React, { Suspense } from 'react'
import { Button, Text } from '@tremor/react'
import { useQuery } from '@tanstack/react-query'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'

import { getApiUrl, getRunData, getRunDataUrl } from '@/repository'
import Dialog from './Dialog'

interface Props {
  runId: number
  taskId: string
  open: boolean
  onClose: () => any
}

const HotTable = React.lazy(() => import('./HandsonTable.js'))
const ReactJson = React.lazy(() => import('@microlink/react-json-view'))

const JsonComponent: React.FC<{ data: any }> = ({ data }) => {
  const isDark = document.documentElement.classList.contains('dark')

  return (
    <div className="border dark:border-slate-800 rounded-lg">
      <Suspense fallback={<div>Loading table UI...</div>}>
        <ReactJson
          src={data}
          collapseStringsAfterLength={50}
          iconStyle="triangle"
          theme={isDark ? 'summerfruit' : 'summerfruit:inverted'}
          style={{
            padding: 24,
            borderRadius: 'inherit',
          }}
        />
      </Suspense>
    </div>
  )
}

const PrimitiveComponent: React.FC<{ data: any }> = ({ data }) => {
  return (
    <div className="border dark:border-slate-800 rounded-lg p-6">
      {JSON.stringify(data)}
    </div>
  )
}

const DataViewer: React.FC<{ data: any }> = ({ data }) => {
  if (Array.isArray(data) && typeof data[0] === 'object') {
    return (
      <Suspense fallback={<div>Loading table UI...</div>}>
        <HotTable
          data={data}
          rowHeaders={true}
          colHeaders={Object.keys(data[0])}
          height="70vh"
          width="700px"
          licenseKey="non-commercial-and-evaluation"
        />
      </Suspense>
    )
  } else if (typeof data === 'object' && data !== null) {
    return <JsonComponent data={data} />
  } else {
    return <PrimitiveComponent data={data} />
  }
}

const DataViewerDialog: React.FC<Props> = ({
  runId,
  taskId,
  open,
  onClose,
}) => {
  const query = useQuery({
    ...getRunData(runId, taskId),
    enabled: open,
  })

  return (
    <>
      <Dialog
        title={taskId}
        subtitle="View data"
        isOpen={open}
        footer={
          <>
            <Button
              variant="secondary"
              color="indigo"
              onClick={() => onClose()}
            >
              Close
            </Button>

            <a
              href={`${getApiUrl()}/${getRunDataUrl(runId, taskId)}`}
              target="_blank"
              className="tremor-Button-root flex-shrink-0 inline-flex justify-center items-center group font-medium outline-none rounded-tremor-default shadow-tremor-input dark:shadow-dark-tremor-input border px-4 py-2 text-sm bg-indigo-500 border-indigo-500 text-white hover:bg-indigo-600 hover:border-indigo-700 no-underline hover:text-inherit"
              rel="noopener noreferrer"
            >
              <ArrowDownTrayIcon className="tremor-Button-icon shrink-0 h-5 w-5 -ml-1 mr-1.5" />
              Download
            </a>
          </>
        }
        onClose={onClose}
      >
        {query.isPending && <div>Loading...</div>}

        {query.isError &&
          (query.error.response.status === 404 ? (
            <Text>The task has no data</Text>
          ) : (
            <Text color="rose">
              Error fetching task data: {query.error.message}
            </Text>
          ))}

        {!query.isPending && !query.isError && <DataViewer data={query.data} />}
      </Dialog>
    </>
  )
}

export default DataViewerDialog
