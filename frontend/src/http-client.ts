interface FetchRequest {
  url: string
  method?: 'get' | 'post' | 'put' | 'patch' | 'delete' | 'head'
  params?: Record<string, string | undefined>
}

export class HTTPError extends Error {
	public response: Response;
	public request: Request;

	constructor(response: Response, request: Request) {
		const code = (response.status || response.status === 0) ? response.status : '';
		const title = response.statusText || '';
		const status = `${code} ${title}`.trim();
		const reason = status ? `status code ${status}` : 'an unknown error';

		super(`Request failed with ${reason}`);

		this.name = 'HTTPError';
		this.response = response;
		this.request = request;
	}
}

const buildSearchParams = (params: Record<string, any>): URLSearchParams => {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([ key, value ]) => {
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

  constructor (config: Config = {}) {
    this.config = config
  }

  async fetch<ResponseType = any>(request: FetchRequest | string): Promise<ResponseType> {
    let url: string

    if (typeof(request) === 'string') {
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
      return await response.json() as ResponseType
    } else {
      return await response.text() as ResponseType
    }
  }
}
