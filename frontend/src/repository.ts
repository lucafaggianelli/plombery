import { UseMutationOptions } from '@tanstack/react-query'
import ky, { HTTPError, Options } from 'ky'

import { LogEntry, Pipeline, PipelineRun } from './types'

const DEFAULT_BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000/api'
  : `${window.location.protocol}//${window.location.host}/api`
const BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL

const client = ky.create({ prefixUrl: BASE_URL })

export const getApiUrl = () => BASE_URL

/**
 * Helper function to GET a JSON request
 */
const get = async <ResponseType = any>(
  url: string,
  request?: Omit<Options, 'method'>
): Promise<ResponseType> => {
  return (await client.get(url, request)).json<ResponseType>()
}

/**
 * Helper function to POST a JSON request
 */
const post = async <ResponseType = any>(
  url: string,
  request?: Omit<Options, 'method'>
): Promise<ResponseType> => {
  return (
    await client.get(url, { ...request, method: 'post' })
  ).json<ResponseType>()
}

export const getCurrentUser = async () => {
  return await get<{ user: any; is_authentication_enabled: boolean }>('whoami')
}

export const logout = async () => {
  await post('logout')
}

export const getWebsocketUrl = () => {
  const url = new URL(BASE_URL)
  url.protocol = 'ws'
  url.pathname += '/ws'
  return url
}

export const listPipelines = async (): Promise<Pipeline[]> => {
  const pipelines = await get<Pipeline[]>('pipelines')

  pipelines.forEach((pipeline) => {
    pipeline.triggers.forEach((trigger) => {
      if (trigger.next_fire_time) {
        trigger.next_fire_time = new Date(trigger.next_fire_time)
      }
    })
  })

  return pipelines.map(
    (pipeline) =>
      new Pipeline(
        pipeline.id,
        pipeline.name,
        pipeline.description,
        pipeline.tasks,
        pipeline.triggers
      )
  )
}

export const getPipeline = async (pipelineId: string): Promise<Pipeline> => {
  const pipeline = await get<Pipeline>(`pipelines/${pipelineId}`)

  pipeline.triggers.forEach((trigger) => {
    if (trigger.next_fire_time) {
      trigger.next_fire_time = new Date(trigger.next_fire_time)
    }
  })

  return new Pipeline(
    pipeline.id,
    pipeline.name,
    pipeline.description,
    pipeline.tasks,
    pipeline.triggers
  )
}

export const getPipelineInputSchema = async (pipelineId: string) => {
  return await get(`pipelines/${pipelineId}/input-schema`)
}

export const listRuns = async (
  pipelineId?: string,
  triggerId?: string
): Promise<PipelineRun[]> => {
  const params = {
    pipeline_id: pipelineId ?? '',
    trigger_id: triggerId ?? '',
  }

  const runs = await get<any[]>('runs', {
    searchParams: params,
  })

  runs.forEach((run) => {
    run.start_time = new Date(run.start_time)
  })

  return runs as PipelineRun[]
}

export const getRun = async (runId: number): Promise<PipelineRun> => {
  const run = await get(`runs/${runId}`)
  run.start_time = new Date(run.start_time)

  return run as PipelineRun
}

export const getLogs = async (runId: number): Promise<LogEntry[]> => {
  const rawLogs = await client.get(`runs/${runId}/logs`).text()

  if (!rawLogs) {
    return []
  }

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
  return await get(`runs/${runId}/data/${taskId}`)
}

export const getPipelineRunUrl = (pipelineId: string) =>
  `${BASE_URL}/pipelines/${pipelineId}/run`

export const runPipeline = (
  pipelineId: string
): UseMutationOptions<PipelineRun, HTTPError, any> => ({
  async mutationFn(params) {
    return await post<PipelineRun>(`pipelines/${pipelineId}/run`, {
      json: params,
    })
  },
})

export const getTriggerRunUrl = (pipelineId: string, triggerId: string) =>
  `/pipelines/${pipelineId}/triggers/${triggerId}/run`

export const runPipelineTrigger = (
  pipelineId: string,
  triggerId: string
): UseMutationOptions<PipelineRun, HTTPError> => ({
  async mutationFn() {
    return await post<PipelineRun>(
      `pipelines/${pipelineId}/triggers/${triggerId}/run`
    )
  },
})
