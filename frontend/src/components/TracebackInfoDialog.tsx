import { Button, Flex } from '@tremor/react'
import { useState } from 'react'

import { LogEntry } from '@/types'
import Dialog from './Dialog'

interface Props {
  logEntry: LogEntry
}

const TracebackInfoDialog: React.FC<Props> = ({ logEntry }) => {
  const [open, setOpen] = useState(false)

  return (
    <Flex className="mt-1">
      <Button
        color="rose"
        variant="secondary"
        size="xs"
        onClick={() => setOpen(true)}
      >
        Traceback info
      </Button>

      <Dialog
        isOpen={open}
        title="Traceback info"
        footer={
          <Button
            variant="primary"
            color="indigo"
            onClick={() => {
              setOpen(false)
            }}
          >
            Close
          </Button>
        }
        onClose={() => setOpen(false)}
      >
        <div className="flex flex-col">
          <div
            style={{
              minWidth: 350,
              maxWidth: '100%',
              overflow: 'auto',
              flexGrow: 1,
              maxHeight: '70vh',
            }}
            className="p-3 my-3 bg-tremor-background-subtle dark:bg-dark-tremor-background-subtle rounded-md whitespace-pre font-mono"
          >
            {logEntry.exc_info}
          </div>
        </div>
      </Dialog>
    </Flex>
  )
}

export default TracebackInfoDialog
