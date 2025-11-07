export type PipelineRunStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'

export interface LogEntry {
  id: number
  task: string | null
  task_with_index: string | null
  level: LogLevel
  message: string
  timestamp: Date
  exc_info?: string
  loggerName: string
  map_index: number | null
}

export interface Trigger {
  id: string
  name: string
  description?: string
  schedule?: string
  paused?: boolean
  params?: any
  next_fire_time?: Date
}

export interface Task {
  id: string
  name: string
  description: string
  upstream_task_ids: string[]
  downstream_task_ids: string[]
  mapping_mode: 'fan_out' | 'chained_fan_out' | null
  map_upstream_id: string | null
}

export class Pipeline {
  constructor(
    public id: string,
    public name: string,
    public description: string,
    public tasks: Task[],
    public triggers: Trigger[]
  ) {}

  hasTrigger(): boolean {
    return this.triggers.some((trigger) => !!trigger.schedule)
  }

  getNextFireTime(): Date | undefined {
    const sortedTriggers = this.triggers
      .filter((trigger) => !!trigger.next_fire_time)
      .sort((a, b) => a.next_fire_time!.getTime() - b.next_fire_time!.getTime())

    const earliestTrigger = sortedTriggers[0]

    if (earliestTrigger) {
      return earliestTrigger.next_fire_time
    }
  }
}

export interface TaskRun {
  duration: number
  start_time?: Date
  end_time?: Date
  id: string
  context: any
  status: PipelineRunStatus
  task_id: string
  task_output_id?: string
  map_index?: number
  parent_task_run_id?: string
}

export interface PipelineRun {
  id: number
  status: PipelineRunStatus
  pipeline_id: string
  trigger_id: string
  start_time?: Date
  end_time?: Date
  duration: number
  task_runs: TaskRun[]
  input_params: Record<string, any>
}

export interface WhoamiResponse {
  user: any
  is_authentication_enabled: boolean
}
