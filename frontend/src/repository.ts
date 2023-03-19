import { SuperFetch } from './http-client'
import { LogEntry, Pipeline, PipelineRun } from './types'

const DEFAULT_BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000/api'
  : '/api'
const BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL

const client = new SuperFetch({ baseUrl: BASE_URL })

export const getPipelines = async (): Promise<Pipeline[]> => {
  const response = await fetch(`${BASE_URL}/pipelines`)
  const pipelines: any[] = await response.json()
  pipelines.forEach((pipeline) => {
    pipeline.triggers.forEach((trigger: any) => {
      trigger.next_fire_time = new Date(trigger.next_fire_time)
    })
  })

  return pipelines as Pipeline[]
}

export const getPipeline = async (pipelineId: string): Promise<Pipeline> => {
  const response = await fetch(`${BASE_URL}/pipelines/${pipelineId}`)
  const pipeline = await response.json()
  pipeline.triggers.forEach((trigger: any) => {
    trigger.next_fire_time = new Date(trigger.next_fire_time)
  })

  return pipeline as Pipeline
}

export const getPipelineInputSchema = async (pipelineId: string) => {
  const response = await fetch(
    `${BASE_URL}/pipelines/${pipelineId}/input-schema`
  )
  return await response.json()
}

export const getRuns = async (
  pipelineId?: string,
  triggerId?: string
): Promise<PipelineRun[]> => {
  const params = {
    pipeline_id: pipelineId,
    trigger_id: triggerId,
  }

  const runs = await client.fetch<any[]>({
    url: '/runs',
    params,
  })

  runs.forEach((run) => {
    run.start_time = new Date(run.start_time)
  })

  return runs as PipelineRun[]
}

export const getRun = async (runId: number): Promise<PipelineRun> => {
  const response = await fetch(`${BASE_URL}/runs/${runId}`)
  const run = await response.json()
  run.start_time = new Date(run.start_time)

  return run as PipelineRun
}

export const getLogs = async (
  pipelineId: string,
  triggerId: string,
  runId: number
): Promise<LogEntry[]> => {
  const response = await fetch(
    `${BASE_URL}/pipelines/${pipelineId}/triggers/${triggerId}/runs/${runId}/logs`
  )
  // Logs data is in JSONL format (1 JSON object per line)
  const rawLogs: string = await response.text()

  return rawLogs.split('\n').map((line, i) => {
    const parsed = JSON.parse(line)
    // Add a unique id to be used as key for React
    parsed.id = i
    parsed.timestamp = new Date(parsed.timestamp)
    return parsed
  })
}

export const getRunData = async (
  pipelineId: string,
  triggerId: string,
  runId: number,
  taskId: string
) => {
  const response = await fetch(
    `${BASE_URL}/pipelines/${pipelineId}/triggers/${triggerId}/runs/${runId}/data/${taskId}`
  )

  return await response.json()
}

export const getPipelineRunUrl = (pipelineId: string) =>
  `${BASE_URL}/pipelines/${pipelineId}/run`

export const getTriggerRunUrl = (pipelineId: string, triggerId: string) =>
  `${BASE_URL}/pipelines/${pipelineId}/triggers/${triggerId}/run`

export const runPipelineTrigger = async (
  pipelineId: string,
  triggerId: string
) => {
  const response = await fetch(getTriggerRunUrl(pipelineId, triggerId), {
    method: 'POST',
  })
  return await response.json()
}
