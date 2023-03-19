import { HotTable } from '@handsontable/react'
import {
  registerAllCellTypes,
  registerAllRenderers,
  registerAllPlugins,
} from 'handsontable/registry'
import 'handsontable/dist/handsontable.full.min.css'
import { Button, Text } from '@tremor/react'
import { useQuery } from '@tanstack/react-query'

import { getRunData } from '@/repository'
import Dialog from './Dialog'
import { HTTPError } from '@/http-client'

interface Props {
  runId: number
  taskId: string
  open: boolean
  onClose: () => any
}

registerAllCellTypes()
registerAllRenderers()
registerAllPlugins()

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
        footer={
          <Button variant="secondary" color="indigo" onClick={() => onClose()}>
            Close
          </Button>
        }
        onClose={onClose}
      >
        {!query.isLoading && !query.isError && (
          <HotTable
            data={query.data}
            rowHeaders={true}
            colHeaders={Object.keys(query.data[0])}
            height="70vh"
            licenseKey="non-commercial-and-evaluation"
          />
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
