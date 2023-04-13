type MethodType = 'get' | 'post' | 'put' | 'patch' | 'delete' | 'head'

interface FetchRequest {
  url: string
  method?: MethodType
  params?: Record<string, string | undefined>
  json?: any
}

export class HTTPError extends Error {
  public response: Response
  public request: Request

  constructor(response: Response, request: Request) {
    const code = response.status || response.status === 0 ? response.status : ''
    const title = response.statusText || ''
    const status = `${code} ${title}`.trim()
    const reason = status ? `status code ${status}` : 'an unknown error'

    super(`Request failed with ${reason}`)

    this.name = 'HTTPError'
    this.response = response
    this.request = request
  }
}

const buildSearchParams = (params: Record<string, any>): URLSearchParams => {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined) {
      return
    }

    searchParams.set(key, value)
  })

  return searchParams
}

interface Config {
  baseUrl?: string
}

export class SuperFetch {
  private config: Config

  constructor(config: Config = {}) {
    this.config = config

    // Remove trailing slash
    this.config.baseUrl = this.config.baseUrl?.replace(/\/+$/, '')
  }

  get baseUrl () {
    return this.config.baseUrl
  }

  private async fetch<ResponseType = any>(
    request: FetchRequest | string
  ): Promise<ResponseType> {
    let url: string
    let otherRequestParams: RequestInit | undefined

    if (typeof request === 'string') {
      url = request
    } else {
      const { url: _url, params, json, ...rest } = request
      url = _url
      otherRequestParams = rest

      if (json) {
        otherRequestParams.body = JSON.stringify(json)
        otherRequestParams.headers = {
          'Content-Type': 'application/json'
        }
      }

      if (params) {
        const urlParams = buildSearchParams(params)
        url += `?${urlParams}`
      }
    }

    if (this.config.baseUrl) {
      url = this.config.baseUrl + url
    }

    const fetchRequest = new Request(url, {
      ...otherRequestParams,
      credentials: 'include',
    })
    const response = await fetch(fetchRequest)

    if (!response.ok) {
      throw new HTTPError(response, fetchRequest)
    }

    if (response.headers.get('Content-Type') === 'application/json') {
      return (await response.json()) as ResponseType
    } else {
      return (await response.text()) as ResponseType
    }
  }

  private async fetchForceMethod<ResponseType = any>(
    request: Omit<FetchRequest, 'method'> | string,
    method: MethodType
  ): Promise<ResponseType> {
    if (typeof request === 'string') {
      return this.fetch({ url: request, method })
    } else {
      return this.fetch({ ...request, method })
    }
  }

  async get<ResponseType = any>(
    request: FetchRequest | string
  ): Promise<ResponseType> {
    return this.fetchForceMethod(request, 'get')
  }

  async post<ResponseType = any>(
    request: FetchRequest | string
  ): Promise<ResponseType> {
    return this.fetchForceMethod(request, 'post')
  }

  async put<ResponseType = any>(
    request: FetchRequest | string
  ): Promise<ResponseType> {
    return this.fetchForceMethod(request, 'put')
  }

  async patch<ResponseType = any>(
    request: FetchRequest | string
  ): Promise<ResponseType> {
    return this.fetchForceMethod(request, 'patch')
  }

  async delete<ResponseType = any>(
    request: FetchRequest | string
  ): Promise<ResponseType> {
    return this.fetchForceMethod(request, 'delete')
  }
}
