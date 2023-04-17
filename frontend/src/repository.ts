import { UseMutationOptions } from '@tanstack/react-query'

import { HTTPError, SuperFetch } from './http-client'
import { LogEntry, Pipeline, PipelineRun } from './types'

const DEFAULT_BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000/api'
  : `${window.location.protocol}//${window.location.host}/api`
const BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL

const client = new SuperFetch({ baseUrl: BASE_URL })

export const getApiUrl = () => client.baseUrl

export const getCurrentUser = async () => {
  return await client.get<{ user: any; is_authentication_enabled: boolean }>(
    '/whoami'
  )
}

export const logout = async () => {
  await client.post('/logout')
}

export const getWebsocketUrl = () => {
  const url = new URL(BASE_URL)
  url.protocol = 'ws'
  url.pathname += '/ws'
  return url
}

export const listPipelines = async (): Promise<Pipeline[]> => {
  const pipelines = await client.get<any[]>('/pipelines')

  return pipelines as Pipeline[]
}

export const getPipeline = async (pipelineId: string): Promise<Pipeline> => {
  const pipeline = await client.get(`/pipelines/${pipelineId}`)

  return pipeline as Pipeline
}

export const getPipelineInputSchema = async (pipelineId: string) => {
  return await client.get(`/pipelines/${pipelineId}/input-schema`)
}

export const listRuns = async (
  pipelineId?: string,
  triggerId?: string
): Promise<PipelineRun[]> => {
  const params = {
    pipeline_id: pipelineId,
    trigger_id: triggerId,
  }

  const runs = await client.get<any[]>({
    url: '/runs',
    params,
  })

  runs.forEach((run) => {
    run.start_time = new Date(run.start_time)
  })

  return runs as PipelineRun[]
}

export const getRun = async (runId: number): Promise<PipelineRun> => {
  const run = await client.get(`/runs/${runId}`)
  run.start_time = new Date(run.start_time)

  return run as PipelineRun
}

export const getLogs = async (runId: number): Promise<LogEntry[]> => {
  const rawLogs = await client.get<string>(`/runs/${runId}/logs`)

  // Logs data is in JSONL format (1 JSON object per line)
  return rawLogs.split('\n').map((line, i) => {
    const parsed = JSON.parse(line)
    // Add a unique id to be used as key for React
    parsed.id = i
    parsed.timestamp = new Date(parsed.timestamp)
    return parsed
  })
}

export const getRunData = async (runId: number, taskId: string) => {
  return await client.get(`/runs/${runId}/data/${taskId}`)
}

export const getPipelineRunUrl = (pipelineId: string) =>
  `${BASE_URL}/pipelines/${pipelineId}/run`

export const runPipeline = (
  pipelineId: string
): UseMutationOptions<void, HTTPError, any> => ({
  async mutationFn(params) {
    client.post({ url: `/pipelines/${pipelineId}/run`, json: params })
  },
})

export const getTriggerRunUrl = (
  pipelineId: string,
  triggerId: string,
  absolute: boolean = true
) =>
  `${
    absolute ? BASE_URL : ''
  }/pipelines/${pipelineId}/triggers/${triggerId}/run`

export const runPipelineTrigger = async (
  pipelineId: string,
  triggerId: string
) => {
  return await client.post(getTriggerRunUrl(pipelineId, triggerId, false))
}
