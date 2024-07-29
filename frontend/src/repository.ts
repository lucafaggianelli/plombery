import { UseMutationOptions, UseQueryOptions } from '@tanstack/react-query'
import ky, { HTTPError, Options } from 'ky'

import { LogEntry, Pipeline, PipelineRun, WhoamiResponse } from './types'
import { JSONSchema7 } from 'json-schema'

interface BaseError {
  status: number
  data: any
}

interface Error422 extends BaseError {
  status: 422
  data: {
    detail: {
      loc: string[]
      msg: string
      type: string
    }[]
  }
}

type AllErrors = Error422

class PlomberyHttpError extends Error implements BaseError {
  data: any
  status: number

  constructor(message: string, status: number, data: AllErrors) {
    super(message)
    this.data = { data, status }
    this.status = status
  }
}

const DEFAULT_BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000/api'
  : `${window.location.protocol}//${window.location.host}/api`
const BASE_URL: string = import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL

const client = ky.create({
  prefixUrl: BASE_URL,
  credentials: 'include',
  redirect: 'follow',
})

export const getApiUrl = (): string => BASE_URL

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
  request?: Options
): Promise<ResponseType> => {
  try {
    return await client.post(url, request).json<ResponseType>()
  } catch (e) {
    const error = e as HTTPError

    throw new PlomberyHttpError(
      error.message,
      error.response.status,
      await error.response.json()
    )
  }
}

export const getWebsocketUrl = () => {
  const url = new URL(BASE_URL)
  url.pathname = url.pathname.replace(/api$/, '')
  return url
}

export const getPipelineRunUrl = (pipelineId: string) =>
  `${BASE_URL}/pipelines/${pipelineId}/run`

export const getCurrentUser = async () => {
  return await get<WhoamiResponse>('auth/whoami')
}

export const logout = async () => {
  await post('auth/logout')
}

/**
 * Pipelines
 */

export const listPipelines = (): UseQueryOptions<Pipeline[], HTTPError> => ({
  queryKey: ['pipelines'],
  queryFn: async () => {
    const pipelines = await get<Pipeline[]>('pipelines/')

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
  },
  initialData: [],
})

export const getPipeline = (
  pipelineId: string
): UseQueryOptions<Pipeline, HTTPError> => ({
  queryKey: ['pipeline', pipelineId],
  queryFn: async () => {
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
  },
  initialData: new Pipeline('', '', '', [], []),
  enabled: !!pipelineId,
})

export const getPipelineInputSchema = (
  pipelineId: string
): UseQueryOptions<JSONSchema7, HTTPError> => ({
  queryKey: ['pipeline-input', pipelineId],
  queryFn: async () => {
    return await get(`pipelines/${pipelineId}/input-schema`)
  },
})

/**
 * Runs
 */

export const listRuns = (
  pipelineId?: string,
  triggerId?: string
): UseQueryOptions<PipelineRun[], HTTPError> => ({
  queryKey: ['runs', pipelineId, triggerId],
  queryFn: async () => {
    const params = {
      pipeline_id: pipelineId ?? '',
      trigger_id: triggerId ?? '',
    }

    const runs = await get<any[]>('runs/', {
      searchParams: params,
    })

    runs.forEach((run) => {
      run.start_time = new Date(run.start_time)
    })

    return runs as PipelineRun[]
  },
  initialData: [],
})

export const getRun = (
  pipelineId: string,
  triggerId: string,
  runId: number
): UseQueryOptions<PipelineRun, HTTPError> => ({
  queryKey: ['runs', pipelineId, triggerId, runId],
  queryFn: async () => {
    const run = await get(`runs/${runId}`)
    run.start_time = new Date(run.start_time)

    return run as PipelineRun
  },
  enabled: !!(pipelineId && triggerId && runId),
})

export const getLogs = (
  runId: number
): UseQueryOptions<LogEntry[], HTTPError> => ({
  queryKey: ['logs', runId],
  queryFn: async () => {
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
  },
  enabled: !!runId,
  initialData: [],
})

export const getRunDataUrl = (runId: number, taskId: string) =>
  `runs/${runId}/data/${taskId}`

export const getRunData = (
  runId: number,
  taskId: string
): UseQueryOptions<any, HTTPError> => ({
  queryKey: ['getRunData', { runId, taskId }],
  queryFn: async () => {
    return await get(getRunDataUrl(runId, taskId))
  },
})

export const runPipeline = (
  pipelineId: string,
  triggerId?: string
): UseMutationOptions<
  PipelineRun,
  PlomberyHttpError,
  Record<string, any> | void
> => ({
  async mutationFn(params) {
    return await post<PipelineRun>(`pipelines/${pipelineId}/run`, {
      json: {
        trigger_id: triggerId,
        params,
      },
    })
  },
})

export const getLatestRelease = (): UseQueryOptions<{
  tag_name: string
  prerelease: boolean
}> => ({
  queryKey: ['gh', 'latest-release'],
  queryFn: async () => {
    return await ky
      .get(
        'https://api.github.com/repos/lucafaggianelli/plombery/releases/latest'
      )
      .json<{ tag_name: string; prerelease: boolean }>()
  },
})
