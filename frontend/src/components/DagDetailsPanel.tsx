import { OnSelectionChangeFunc, useOnSelectionChange } from '@xyflow/react'
import { useCallback, useState } from 'react'

import { Pipeline, PipelineRun } from '@/types'
import PipelineRunDetails from './PipelineRunDetails'
import TaskRunDetails from './TaskRunDetails'

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

  if (selectedNode) {
    const taskRuns = run.task_runs.filter(
      (taskRun) => taskRun.task_id === selectedNode
    )

    // The task carries the mapping metadata, which the runs alone don't have
    const task = pipeline.tasks.find((task) => task.id === selectedNode)

    return <TaskRunDetails task={task} runs={taskRuns} />
  }

  return <PipelineRunDetails pipeline={pipeline} run={run} />
}
