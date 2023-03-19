import { Flex, Text } from '@tremor/react'
import { Link } from 'react-router-dom'
import React from 'react'

import { Pipeline, PipelineRun, Trigger } from '../types'

interface Props {
  pipeline: Pipeline
  trigger?: Trigger
  run?: PipelineRun
}

const Separator = () => <Text>/</Text>

const Breadcrumbs: React.FC<Props> = ({ pipeline, trigger, run }) => {
  if (run && !trigger) {
    throw new Error()
  }

  return (
    <div className="breadcrumbs">
      <Flex spaceX="space-x-2" justifyContent="justify-start">
        <Text>
          <Link to="/">Pipelines</Link>
        </Text>
        <Separator />
        <Text>
          {trigger ? (
            <Link to={`/pipelines/${pipeline.id}`}>{pipeline.name}</Link>
          ) : (
            pipeline.name
          )}
        </Text>

        {trigger && (
          <>
            <Separator />
            <Text>Triggers</Text>
            <Separator />
            <Text>
              {run ? (
                <Link to={`/pipelines/${pipeline.id}/triggers/${trigger.id}`}>
                  {trigger.name}
                </Link>
              ) : (
                trigger.name
              )}
            </Text>
          </>
        )}

        {run && trigger && (
          <>
            <Separator />
            <Text>Runs</Text>
            <Separator />
            <Text>#{run.id}</Text>
          </>
        )}
      </Flex>
    </div>
  )
}

export default Breadcrumbs
