import { OnSelectionChangeFunc, useOnSelectionChange } from '@xyflow/react'
import { useCallback, useState } from 'react'

import { Pipeline, PipelineRun } from '@/types'
import { TRIGGER_NODE_ID } from './DagViewer'
import PipelineRunDetails from './PipelineRunDetails'
import TaskRunDetails from './TaskRunDetails'
import TriggerRunDetails from './TriggerRunDetails'

interface Props {
  pipeline: Pipeline
  run: PipelineRun
}

export default function DagDetailsPanel({ pipeline, run }: Props) {
  const [selectedNode, setSelectedNode] = useState<string | undefined>()

  const onChange: OnSelectionChangeFunc = useCallback(({ nodes }) => {
    setSelectedNode(nodes[0]?.id)
  }, [])

  useOnSelectionChange({ onChange })

  if (selectedNode === TRIGGER_NODE_ID) {
    return <TriggerRunDetails pipeline={pipeline} run={run} />
  }

  if (selectedNode) {
    const taskRuns = run.task_runs.filter(
      (taskRun) => taskRun.task_id === selectedNode
    )

    // The task carries the mapping metadata and the dependencies, which the
    // runs alone don't have
    const task = pipeline.tasks.find((task) => task.id === selectedNode)

    return (
      <TaskRunDetails
        task={task}
        taskId={selectedNode}
        runs={taskRuns}
        runStatus={run.status}
      />
    )
  }

  return <PipelineRunDetails pipeline={pipeline} run={run} />
}
