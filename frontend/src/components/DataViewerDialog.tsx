import { HotTable } from '@handsontable/react'
import {
  registerAllCellTypes,
  registerAllRenderers,
  registerAllPlugins,
} from 'handsontable/registry'
import 'handsontable/dist/handsontable.full.min.css'
import { Button } from '@tremor/react'
import { useQuery } from '@tanstack/react-query'

import { getRunData } from '@/repository'
import Dialog from './Dialog'

interface Props {
  pipelineId: string
  triggerId: string
  runId: number
  taskId: string
  open: boolean
  onClose: () => any
}

registerAllCellTypes()
registerAllRenderers()
registerAllPlugins()

const DataViewerDialog: React.FC<Props> = ({
  pipelineId,
  triggerId,
  runId,
  taskId,
  open,
  onClose,
}) => {
  const query = useQuery({
    queryKey: ['getRunData', { pipelineId, triggerId, runId, taskId }],
    queryFn: () => getRunData(pipelineId, triggerId, runId, taskId),
    enabled: open,
  })

  return (
    <>
      <Dialog
        title={taskId}
        subtitle="View data"
        isOpen={open}
        footer={
          <Button
            variant="secondary"
            color="indigo"
            onClick={() => onClose()}
          >
            Close
          </Button>
        }
        onClose={onClose}
      >
        {!query.isLoading && <HotTable
          data={query.data}
          rowHeaders={true}
          colHeaders={Object.keys(query.data[0])}
          height="70vh"
          licenseKey="non-commercial-and-evaluation"
        />}
      </Dialog>
    </>
  )
}

export default DataViewerDialog
