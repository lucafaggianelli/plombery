type MethodType = 'get' | 'post' | 'put' | 'patch' | 'delete' | 'head'

interface FetchRequest {
  url: string
  method?: MethodType
  params?: Record<string, string | undefined>
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

  private async fetch<ResponseType = any>(
    request: FetchRequest | string
  ): Promise<ResponseType> {
    let url: string

    if (typeof request === 'string') {
      url = request
    } else {
      url = request.url

      if (request.params) {
        const params = buildSearchParams(request.params)
        url += `?${params}`
      }
    }

    if (this.config.baseUrl) {
      url = this.config.baseUrl + url
    }

    const fetchR = new Request(url)
    const response = await fetch(fetchR)

    if (!response.ok) {
      throw new HTTPError(response, fetchR)
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
