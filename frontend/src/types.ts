export type PipelineRunStatus = 'running' | 'completed' | 'failed' | 'cancelled'

export interface Trigger {
    id: string
    name: string
    description: string
    interval: string
    next_fire_time: Date
    paused: boolean
}

export interface Pipeline {
    id: string
    name: string
    description: string
    tasks: string[]
    triggers: Trigger[]
}

export interface PipelineRun {
    id: number
    status: PipelineRunStatus
    start_time: Date
    duration: number
}
