import { HotTable, HotTableProps } from '@handsontable/react'
import {
  registerAllCellTypes,
  registerAllRenderers,
  registerAllPlugins,
} from 'handsontable/registry'
import 'handsontable/dist/handsontable.full.min.css'

registerAllCellTypes()
registerAllRenderers()
registerAllPlugins()

const HandsonTable: React.FC<HotTableProps> = (props) => {
  return <HotTable {...props} licenseKey="non-commercial-and-evaluation" />
}

export default HandsonTable
