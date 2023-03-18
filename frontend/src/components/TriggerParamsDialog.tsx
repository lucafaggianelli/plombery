import { Trigger } from '@/types'
import { Button, Card, Flex, Subtitle, Title } from '@tremor/react'
import { useState } from 'react'
import Dialog from './Dialog'

interface Props {
  trigger: Trigger
}

const TriggerParamsDialog: React.FC<Props> = ({ trigger }) => {
  const [open, setOpen] = useState(false)

  return (
    <>
      <Button
        color="indigo"
        variant="light"
        size="xs"
        onClick={() => setOpen(true)}
      >
        Show params
      </Button>

      <Dialog
        isOpen={open}
        title="Trigger params"
        subtitle={trigger.name}
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
        <pre className="p-3 tr-bg-slate-100 rounded-md">
          {JSON.stringify(trigger.params, null, 2)}
        </pre>
      </Dialog>
    </>
  )
}

export default TriggerParamsDialog
