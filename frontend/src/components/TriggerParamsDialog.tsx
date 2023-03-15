import { Trigger } from '@/types'
import { Button, Card, Flex, Subtitle, Title } from '@tremor/react'
import { createRef, MouseEventHandler } from 'react'

interface Props {
  trigger: Trigger
}

const TriggerParamsDialog: React.FC<Props> = ({ trigger }) => {
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
    <>
      <Button
        color="indigo"
        variant="light"
        size="xs"
        onClick={() => dialog.current?.showModal()}
      >
        Show params
      </Button>

      <dialog
        ref={dialog}
        style={{ padding: 0, background: 'transparent', overflow: 'visible' }}
        onClick={closeDialogOnBackdropClick}
      >
        <Card>
          <Title>Trigger params</Title>
          <Subtitle>{trigger.name}</Subtitle>

          <div style={{ minWidth: 350, maxWidth: '600px', overflow: 'auto' }}>
            <pre className="p-3 my-3 tr-bg-slate-100">
              {JSON.stringify(trigger.params, null, 2)}
            </pre>
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
        </Card>
      </dialog>
    </>
  )
}

export default TriggerParamsDialog
