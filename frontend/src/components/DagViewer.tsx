import Dagre from '@dagrejs/dagre'
import { useState, useCallback, useMemo, useEffect } from 'react'
import {
  ReactFlow,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Node,
  Edge,
  Background,
  Handle,
  Position,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { Pipeline, PipelineRun, Task, TaskRun } from '@/types'
import TaskRunStatusIcon from './TaskRunStatusIcon'

interface TaskWithRun extends Record<string, any> {
  task: Task
  run?: TaskRun
}

export function TaskNode({ data }: Node<TaskWithRun>) {
  return (
    <div className="bg-tremor-background dark:bg-dark-tremor-background px-2 py-2 rounded-lg border dark:border-dark-tremor-background-subtle">
      <div className="flex gap-2 items-center">
        <TaskRunStatusIcon status={data.run?.status} />
        <div className="text-xs">{data.task.name}</div>
      </div>

      {data.task.downstream_task_ids.length > 0 && (
        <Handle type="source" position={Position.Right} />
      )}

      {data.task.upstream_task_ids.length > 0 && (
        <Handle type="target" position={Position.Left} />
      )}
    </div>
  )
}

const getLayoutedElements = (
  nodes: Node[],
  edges: Edge[],
  options: { direction: 'TB' | 'LR' }
) => {
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: options.direction })

  edges.forEach((edge) => g.setEdge(edge.source, edge.target))
  nodes.forEach((node) =>
    g.setNode(node.id, {
      ...node,
      width: node.measured?.width ?? 0,
      height: node.measured?.height ?? 0,
    })
  )

  Dagre.layout(g)

  return {
    nodes: nodes.map((node) => {
      const position = g.node(node.id)
      // We are shifting the dagre node position (anchor=center center) to the top left
      // so it matches the React Flow node anchor point (top left).
      const x = position.x - (node.measured?.width ?? 0) / 2
      const y = position.y - (node.measured?.height ?? 0) / 2

      return { ...node, position: { x, y } }
    }),
    edges,
  }
}

export default function DagViewer({
  pipeline,
  run,
}: {
  pipeline: Pipeline
  run: PipelineRun
}) {
  useEffect(() => {
    const taskRunsMap = Object.fromEntries(
      run.task_runs.map((taskRun) => [taskRun.task_id, taskRun])
    )

    const initialNodes: Node[] = pipeline.tasks.map((task) => ({
      id: task.id,
      type: 'task',
      position: { x: 0, y: 0 },
      data: { task, run: taskRunsMap[task.id] },
      measured: { height: 60, width: 150 },
    }))

    const initialEdges: Edge[] = pipeline.tasks.flatMap((task) =>
      task.upstream_task_ids.map((upstream) => ({
        id: `${task.id}-${upstream}`,
        source: upstream,
        target: task.id,
        animated:
          !taskRunsMap[upstream] ||
          ['running', 'pending'].includes(taskRunsMap[upstream]?.status),
      }))
    )

    const layouted = getLayoutedElements(initialNodes, initialEdges, {
      direction: 'LR',
    })

    setNodes(layouted.nodes)
    setEdges(layouted.edges)
  }, [pipeline, run])

  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])

  const onNodesChange = useCallback(
    (changes) =>
      setNodes((nodesSnapshot) => applyNodeChanges(changes, nodesSnapshot)),
    []
  )
  const onEdgesChange = useCallback(
    (changes) =>
      setEdges((edgesSnapshot) => applyEdgeChanges(changes, edgesSnapshot)),
    []
  )
  const onConnect = useCallback(
    (params) => setEdges((edgesSnapshot) => addEdge(params, edgesSnapshot)),
    []
  )

  return (
    <div style={{ width: '100%', height: '500px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={{
          task: TaskNode,
        }}
        fitView
        colorMode="system"
      >
        <Background />
      </ReactFlow>
    </div>
  )
}
