import { LogEntry } from '@/types'
import { Button, Card, Flex, Title } from '@tremor/react'
import { createRef, MouseEventHandler } from 'react'

interface Props {
  logEntry: LogEntry
}

const TracebackInfoDialog: React.FC<Props> = ({ logEntry }) => {
  const dialog = createRef<HTMLDialogElement>()

  const closeDialogOnBackdropClick: MouseEventHandler<HTMLDialogElement> = (
    event
  ) => {
    var rect = dialog.current!.getBoundingClientRect()
    var isInDialog =
      rect.top <= event.clientY &&
      event.clientY <= rect.top + rect.height &&
      rect.left <= event.clientX &&
      event.clientX <= rect.left + rect.width

    if (!isInDialog) {
      dialog.current?.close()
    }
  }

  return (
    <Flex justifyContent='justify-end' marginTop='mt-0'>
      <Button
        color="indigo"
        variant="light"
        size="xs"
        onClick={() => dialog.current?.showModal()}
      >
        Traceback info
      </Button>

      <dialog
        ref={dialog}
        style={{ padding: 0, background: 'transparent', overflow: 'visible', maxWidth: '80%' }}
        onClick={closeDialogOnBackdropClick}
      >
        <Card>
          <div className="flex flex-col" style={{ maxHeight: '90vh' }}>
            <Title>Traceback info</Title>

            <div
              style={{
                minWidth: 350,
                maxWidth: '100%',
                overflow: 'auto',
                flexGrow: 1,
              }}
              className="p-3 my-3 tr-bg-slate-100 rounded-md whitespace-pre font-mono"
            >
              {logEntry.exc_info}
            </div>

            <Flex justifyContent="justify-end" spaceX="space-x-6">
              <Button
                variant="primary"
                color="indigo"
                onClick={() => {
                  dialog.current?.close()
                }}
              >
                Close
              </Button>
            </Flex>
          </div>
        </Card>
      </dialog>
    </Flex>
  )
}

export default TracebackInfoDialog
