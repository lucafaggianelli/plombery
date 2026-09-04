import { Badge, Callout } from '@tremor/react'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import React from 'react'

import { Pipeline } from '../types'

/**
 * A small "Not runnable" badge for lists, shown only when the pipeline has a
 * blocking issue. The issues themselves are in the `title` tooltip.
 */
export const PipelineRunnableBadge: React.FC<{ pipeline: Pipeline }> = ({
  pipeline,
}) => {
  if (pipeline.runnable) return null

  return (
    <Badge
      color="rose"
      icon={ExclamationTriangleIcon}
      tooltip={pipeline.issues.map((issue) => issue.message).join('\n')}
    >
      Not runnable
    </Badge>
  )
}

/**
 * The full list of what keeps a pipeline from running, for the pipeline page.
 * Renders nothing when there's nothing wrong.
 */
const PipelineIssues: React.FC<{ pipeline: Pipeline }> = ({ pipeline }) => {
  if (pipeline.issues.length === 0) return null

  return (
    <Callout
      title="This pipeline can't run"
      color="rose"
      icon={ExclamationTriangleIcon}
      className="mt-6"
    >
      <ul className="list-disc list-inside space-y-1">
        {pipeline.issues.map((issue, index) => (
          <li key={index}>
            {issue.task_id ? (
              <>
                <span className="font-semibold">{issue.task_id}</span>:{' '}
              </>
            ) : null}
            {issue.message}
          </li>
        ))}
      </ul>
    </Callout>
  )
}

export default PipelineIssues
