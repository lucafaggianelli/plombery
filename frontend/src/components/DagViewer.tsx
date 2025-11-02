import Dagre from '@dagrejs/dagre'
import { useState, useCallback, useEffect, PropsWithChildren } from 'react'
import {
  ReactFlow,
  applyNodeChanges,
  applyEdgeChanges,
  Node,
  Edge,
  Background,
  Handle,
  Position,
  NodeProps,
  OnNodesChange,
  OnEdgesChange,
  Controls,
  Panel,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import {
  Pipeline,
  PipelineRun,
  PipelineRunStatus,
  Task,
  TaskRun,
} from '@/types'
import TaskRunStatusIcon from './TaskRunStatusIcon'
import { twMerge } from 'tailwind-merge'

interface Props extends PropsWithChildren {
  pipeline: Pipeline
  run?: PipelineRun
  className?: string
}

type TaskWithRun = {
  task: Task
  runs?: TaskRun[]
  status?: PipelineRunStatus
}

type TriggerWithParams = {
  trigger: { id: string }
  inputParams: Record<string, any>
}

export function TaskNode({
  data,
  selected,
}: NodeProps<Node<TaskWithRun, 'task'>>) {
  const numberInstances = data.runs?.length ?? 0

  return (
    <div className="relative">
      <div
        className={twMerge(
          'max-w-[250px] bg-tremor-background dark:bg-dark-tremor-background px-2 py-2 rounded-lg border dark:border-dark-tremor-background-subtle cursor-pointer hover:dark:border-dark-tremor-background-emphasis hover:border-tremor-background-emphasis transition-colors',
          selected &&
            'dark:border-dark-tremor-background-emphasis border-tremor-background-emphasis'
        )}
      >
        <div className="flex gap-2 items-center">
          {data.status && <TaskRunStatusIcon status={data.status} />}

          <div className="overflow-hidden">
            <div className="text-sm truncate">{data.task.name}</div>
            <div className="text-xs truncate text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
              {data.task.description}
            </div>
          </div>
        </div>

        {data.task.downstream_task_ids.length > 0 && (
          <Handle type="source" position={Position.Right} />
        )}

        {/* The target handle always exists as there's always a trigger that connects to it */}
        <Handle type="target" position={Position.Left} />

        {numberInstances > 1 && (
          <div className="absolute -top-2 -left-2 text-xs flex size-5 items-center justify-center rounded-full bg-sky-800 text-white">
            {numberInstances}&times;
          </div>
        )}
      </div>

      {data.task.mapping_mode === 'fan_out' && (
        <>
          <div className="absolute -z-10 size-full scale-75 -bottom-4 bg-tremor-background dark:bg-dark-tremor-background px-2 py-2 rounded-lg border dark:border-dark-tremor-background-subtle" />
          <div className="absolute -z-10 size-full scale-90 -bottom-2 bg-tremor-background dark:bg-dark-tremor-background px-2 py-2 rounded-lg border dark:border-dark-tremor-background-subtle" />
        </>
      )}
    </div>
  )
}

export function TriggerNode({
  data,
}: NodeProps<Node<TriggerWithParams, 'trigger'>>) {
  return (
    <div className="bg-tremor-background dark:bg-dark-tremor-background px-2 py-2 rounded-lg border dark:border-dark-tremor-background-subtle">
      <div className="flex gap-2 items-center">{data.trigger.id}</div>

      <Handle type="source" position={Position.Right} />
    </div>
  )
}

const nodeTypes = {
  task: TaskNode,
  trigger: TriggerNode,
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

const getTaskRunsStatus = (taskRuns: TaskRun[]): PipelineRunStatus => {
  if (taskRuns.length === 0) {
    return 'pending'
  }

  if (taskRuns.every((taskRun) => taskRun.status === 'completed')) {
    return 'completed'
  }

  if (taskRuns.some((taskRun) => taskRun.status === 'failed')) {
    return 'failed'
  }

  if (taskRuns.some((taskRun) => taskRun.status === 'running')) {
    return 'running'
  }

  if (taskRuns.some((taskRun) => taskRun.status === 'pending')) {
    return 'pending'
  }

  return 'running'
}

export default function DagViewer({
  pipeline,
  run,
  children,
  className,
}: Props) {
  const isDark = document.documentElement.classList.contains('dark')

  useEffect(() => {
    const groupedTaskRuns = run
      ? (Object.groupBy(run.task_runs, (taskRun) => taskRun.task_id) as Record<
          string,
          TaskRun[]
        >)
      : {}

    const tasksMap: Record<string, TaskWithRun> = Object.fromEntries(
      pipeline.tasks.map((task) => [
        task.id,
        {
          task,
          runs: groupedTaskRuns[task.id],
          status: groupedTaskRuns[task.id]
            ? getTaskRunsStatus(groupedTaskRuns[task.id])
            : undefined,
        },
      ])
    )

    const initialNodes: Node[] = pipeline.tasks.map((task) => ({
      id: task.id,
      type: 'task',
      position: { x: 0, y: 0 },
      data: tasksMap[task.id],
      measured: { height: 60, width: 250 },
    }))

    const initialEdges: Edge[] = pipeline.tasks.flatMap((task) =>
      task.upstream_task_ids.map((upstream) => ({
        id: `${task.id}-${upstream}`,
        source: upstream,
        target: task.id,
        animated: run
          ? !tasksMap[upstream]?.status ||
            ['running', 'pending'].includes(tasksMap[upstream]?.status)
          : false,
      }))
    )

    if (run) {
      initialNodes.push({
        id: 'trigger',
        type: 'trigger',
        position: { x: 0, y: 0 },
        data: {
          inputParams: run.input_params,
          trigger: { id: run.trigger_id },
        },
        measured: { height: 60, width: 200 },
      })

      pipeline.tasks
        .filter((task) => task.upstream_task_ids.length === 0)
        .forEach((task) =>
          initialEdges.push({
            id: `trigger-${task.id}`,
            source: 'trigger',
            target: task.id,
            animated: false,
          })
        )
    }

    const layouted = getLayoutedElements(initialNodes, initialEdges, {
      direction: 'LR',
    })

    setNodes(layouted.nodes)
    setEdges(layouted.edges)
  }, [pipeline, run])

  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])

  const onNodesChange: OnNodesChange = useCallback(
    (changes) =>
      setNodes((nodesSnapshot) => applyNodeChanges(changes, nodesSnapshot)),
    []
  )
  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) =>
      setEdges((edgesSnapshot) => applyEdgeChanges(changes, edgesSnapshot)),
    []
  )

  return (
    <div style={{ width: '100%', height: '500px' }} className={className}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        connectOnClick={false}
        multiSelectionKeyCode={null}
        nodeTypes={nodeTypes}
        fitView
        colorMode={isDark ? 'dark' : 'light'}
      >
        <Background />
        <Controls />
        <Panel position="top-right">{children}</Panel>
      </ReactFlow>
    </div>
  )
}
