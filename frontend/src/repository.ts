import {
  InfiniteData,
  QueryKey,
  UseInfiniteQueryOptions,
  UseInfiniteQueryResult,
  UseMutationOptions,
  UseQueryOptions,
} from '@tanstack/react-query'
import ky, { HTTPError, isHTTPError, Options } from 'ky'

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
  prefix: BASE_URL,
  credentials: 'include',
  redirect: 'follow',
})

export const getApiUrl = (): string => BASE_URL

/**
 * Helper function to GET a JSON request
 */
const get = async <ResponseType = any>(
  url: string,
  request?: Omit<Options, 'method'>,
): Promise<ResponseType> => {
  return (await client.get(url, request)).json<ResponseType>()
}

/**
 * Helper function to POST a JSON request
 */
const post = async <ResponseType = any>(
  url: string,
  request?: Options,
): Promise<ResponseType> => {
  try {
    return await client.post(url, request).json<ResponseType>()
  } catch (e) {
    // A network or timeout error never carries a response to unwrap
    if (!isHTTPError(e)) {
      throw e
    }

    // ky reads the body to build the error, so it is only available
    // pre-parsed on the error itself
    throw new PlomberyHttpError(
      e.message,
      e.response.status,
      e.data as AllErrors,
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

export const getAuthProviders = (): UseQueryOptions<
  { id: string; name: string; redirect_url: string }[],
  HTTPError
> => ({
  queryKey: ['auth-providers'],
  queryFn: async () => {
    return await get('auth/providers')
  },
})

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
          pipeline.triggers,
          pipeline.version,
          pipeline.issues,
          pipeline.runnable,
        ),
    )
  },
  initialData: [],
})

export const getPipeline = (
  pipelineId: string,
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
      pipeline.triggers,
      pipeline.version,
      pipeline.issues,
      pipeline.runnable,
    )
  },
  initialData: new Pipeline('', '', '', [], []),
  enabled: !!pipelineId,
})

export const getPipelineInputSchema = (
  pipelineId: string,
): UseQueryOptions<JSONSchema7, HTTPError> => ({
  queryKey: ['pipeline-input', pipelineId],
  queryFn: async () => {
    return await get(`pipelines/${pipelineId}/input-schema`)
  },
})

/**
 * Runs
 */

/**
 * How many runs are asked for at a time: a page shorter than this is what
 * tells the list it reached the oldest run.
 */
export const RUNS_PAGE_SIZE = 30

/** The pages of runs as react-query caches them */
export type RunsPages = InfiniteData<PipelineRun[], number | undefined>

/** The cache key of a runs list, shared by its query and its live updates */
export const runsQueryKey = (pipelineId?: string, triggerId?: string) =>
  ['runs', pipelineId, triggerId] as const

// Defined once rather than inline: react-query only reuses the previous
// result when the selector is the same function
const flattenRuns = (data: RunsPages) => data.pages.flat()

/**
 * The runs of a pipeline or of one of its triggers, newest first, paginated.
 *
 * Pages are walked with a cursor (the id of the oldest run received so far)
 * rather than an offset, so a run started while the user is scrolling doesn't
 * shift the following pages.
 */
export const listRuns = (
  pipelineId?: string,
  triggerId?: string,
): UseInfiniteQueryOptions<
  PipelineRun[],
  HTTPError,
  PipelineRun[],
  QueryKey,
  number | undefined
> => ({
  queryKey: runsQueryKey(pipelineId, triggerId),
  queryFn: async ({ pageParam }) => {
    const runs = await get<any[]>('runs/', {
      searchParams: {
        pipeline_id: pipelineId ?? '',
        trigger_id: triggerId ?? '',
        limit: RUNS_PAGE_SIZE,
        ...(pageParam ? { before_id: pageParam } : {}),
      },
    })

    runs.forEach((run) => {
      run.start_time = run.start_time ? new Date(run.start_time) : undefined
      run.end_time = run.end_time ? new Date(run.end_time) : undefined
    })

    return runs as PipelineRun[]
  },
  initialPageParam: undefined,
  getNextPageParam: (lastPage) =>
    lastPage.length < RUNS_PAGE_SIZE
      ? undefined
      : lastPage[lastPage.length - 1].id,
  select: flattenRuns,
})

/** What `useInfiniteQuery(listRuns(...))` returns */
export type RunsQuery = UseInfiniteQueryResult<PipelineRun[], HTTPError>

export const getRun = (
  pipelineId: string,
  triggerId: string,
  runId: number,
): UseQueryOptions<PipelineRun, HTTPError> => ({
  queryKey: ['runs', pipelineId, triggerId, runId],
  queryFn: async () => {
    const run = await get(`runs/${runId}`)
    run.start_time = new Date(run.start_time)
    run.end_time = new Date(run.end_time)

    run.task_runs.forEach((taskRun: any) => {
      taskRun.start_time = taskRun.start_time
        ? new Date(taskRun.start_time)
        : undefined
      taskRun.end_time = taskRun.end_time
        ? new Date(taskRun.end_time)
        : undefined
    })
    run.updatedAt = new Date()

    return run as PipelineRun
  },
  enabled: !!(pipelineId && triggerId && runId),
})

export const getLogs = (
  runId: number,
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
      parsed.task_with_index = parsed.task
        ? parsed.task +
          (parsed.map_index !== null ? `[${parsed.map_index}]` : '')
        : null

      return parsed
    })
  },
  enabled: !!runId,
  initialData: [],
})

export const getRunDataUrl = (runId: string, taskId: string) =>
  `runs/${runId}/data/${taskId}`

export const getRunData = (
  runId: string,
  taskId: string,
): UseQueryOptions<any, HTTPError> => ({
  queryKey: ['getRunData', { runId, taskId }],
  queryFn: async () => {
    return await get(getRunDataUrl(runId, taskId))
  },
})

export const runPipeline = (
  pipelineId: string,
  triggerId?: string,
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
        reason: 'web',
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
        'https://api.github.com/repos/lucafaggianelli/plombery/releases/latest',
      )
      .json<{ tag_name: string; prerelease: boolean }>()
  },
})
