import { Pipeline, PipelineRun } from './types'

const BASE_URL = 'http://localhost:8000/api'

export const getPipelines = async (): Promise<Pipeline[]> => {
  const response = await fetch(`${BASE_URL}/pipelines`)
  const pipelines: any[] = await response.json()
  pipelines.forEach(pipeline => {
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
  const response = await fetch(`${BASE_URL}/pipelines/${pipelineId}/input-schema`)
  return await response.json()
}

export const getRuns = async (pipelineId: string, triggerId: string): Promise<PipelineRun[]> => {
  const response = await fetch(
    `${BASE_URL}/pipelines/${pipelineId}/triggers/${triggerId}/runs`
  )
  const runs: any[] = await response.json()
  runs.forEach(run => {
    run.start_time = new Date(run.start_time)
  })

  return runs as PipelineRun[]
}

export const getRun = async (pipelineId: string, triggerId: string, runId: number): Promise<PipelineRun> => {
  const response = await fetch(
    `${BASE_URL}/pipelines/${pipelineId}/triggers/${triggerId}/runs/${runId}`
  )
  const run = await response.json()
  run.start_time = new Date(run.start_time)

  return run as PipelineRun
}

export const getLogs = async (pipelineId: string, triggerId: string, runId: number): Promise<string> => {
  const response = await fetch(`${BASE_URL}/pipelines/${pipelineId}/triggers/${triggerId}/runs/${runId}/logs`)
  return await response.json()
}

export const runPipelineTrigger = async (pipelineId: string, triggerId: string) => {
  const response = await fetch(`${BASE_URL}/pipelines/${pipelineId}/triggers/${triggerId}/run`, { method: 'POST' })
  return await response.json()
}
