export interface Trigger {
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
    status: string
    start_time: Date
    duration: number
}
