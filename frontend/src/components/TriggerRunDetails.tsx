import { Card, Title } from '@tremor/react'

import { MANUAL_TRIGGER } from '@/constants'
import { Pipeline, PipelineRun } from '@/types'
import { formatDateTime } from '@/utils'

interface Props {
  pipeline: Pipeline
  run: PipelineRun
}

/**
 * What the run started from: the trigger node is the only place where the
 * input params of the run are visible.
 */
export default function TriggerRunDetails({ pipeline, run }: Props) {
  const trigger =
    run.trigger_id === MANUAL_TRIGGER.id
      ? MANUAL_TRIGGER
      : pipeline.triggers.find((trigger) => trigger.id === run.trigger_id)

  const inputParams = Object.entries(run.input_params ?? {})

  return (
    <Card className="p-3 max-w-[350px] max-h-[460px] overflow-y-auto">
      <header className="min-w-0">
        <Title className="truncate" title={trigger?.name ?? run.trigger_id}>
          {trigger?.name ?? run.trigger_id}
        </Title>

        <p className="font-mono text-xs truncate text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
          {run.trigger_id}
        </p>
      </header>

      {trigger?.description && (
        <p className="mt-2 text-sm text-tremor-content dark:text-dark-tremor-content">
          {trigger.description}
        </p>
      )}

      <div className="space-y-4 mt-4">
        {trigger?.schedule && (
          <div>
            <div className="text-xs">Schedule</div>
            <p className="font-mono text-sm break-words">{trigger.schedule}</p>
          </div>
        )}

        <div>
          <div className="text-xs">Fired at</div>
          <p className="tabular-nums text-sm">
            {run.start_time ? formatDateTime(run.start_time) : '-'}
          </p>
        </div>

        <div>
          <div className="text-xs">Input params</div>

          {inputParams.length ? (
            <pre className="mt-1 p-2 text-xs overflow-x-auto rounded-md bg-slate-100 dark:bg-dark-tremor-background-subtle dark:text-dark-tremor-content-emphasis">
              {JSON.stringify(run.input_params, null, 2)}
            </pre>
          ) : (
            <p className="text-sm text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
              None
            </p>
          )}
        </div>
      </div>
    </Card>
  )
}
