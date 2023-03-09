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
    description: string
    interval: string
    next_fire_time: Date
    paused: boolean
    params: any
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

export interface PipelineRun {
    id: number
    status: PipelineRunStatus
    start_time: Date
    duration: number
}
