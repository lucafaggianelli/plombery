import { WrenchScrewdriverIcon } from '@heroicons/react/24/outline'
import { Button } from '@tremor/react'
import { useState } from 'react'

import { Trigger } from '@/types'
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
        size="sm"
        icon={WrenchScrewdriverIcon}
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
        <pre className="p-3 bg-slate-100 dark:bg-dark-tremor-background-subtle dark:text-dark-tremor-content-emphasis rounded-md">
          {JSON.stringify(trigger.params, null, 2)}
        </pre>
      </Dialog>
    </>
  )
}

export default TriggerParamsDialog
