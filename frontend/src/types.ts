export type PipelineRunStatus = 'running' | 'completed' | 'failed' | 'cancelled'
export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'

export interface LogEntry {
  id: number
  task: string
  level: LogLevel
  message: string
  timestamp: Date
  exc_info?: string
  loggerName: string
}

export interface Trigger {
  id: string
  name: string
  description?: string
  schedule?: string
  paused?: boolean
  params?: any
}

export interface Task {
  id: string
  name: string
  description: string
}

export interface Pipeline {
  id: string
  name: string
  description: string
  tasks: Task[]
  triggers: Trigger[]
}

export interface TaskRun {
  duration: number
  has_output: boolean
  status: PipelineRunStatus
  task_id: string
}

export interface PipelineRun {
  id: number
  status: PipelineRunStatus
  pipeline_id: string
  trigger_id: string
  start_time: Date
  duration: number
  tasks_run: TaskRun[]
}

export interface WebSocketMessage {
  type: 'logs' | 'run-update'
  data: any
}
