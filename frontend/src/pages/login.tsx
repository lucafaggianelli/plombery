import { useQuery } from '@tanstack/react-query'
import { Card, Title } from '@tremor/react'

import { getApiUrl, getAuthProviders } from '@/repository'

const LoginPage: React.FC = () => {
  const providersQuery = useQuery(getAuthProviders())

  return (
    <div className="bg-slate-100 dark:bg-slate-950 h-screen flex justify-center items-center">
      <Card className="w-auto">
        <div className="w-12 mx-auto mb-4">
          <img src="/logo.svg" alt="Plombery logo" />
        </div>

        <Title className="mb-12 text-center">Welcome to Plombery</Title>

        {providersQuery.data?.map((provider) => (
          <a
            key={provider.name}
            href={`${getApiUrl()}/auth/login`}
            className="w-full flex gap-4 tremor-Button-root shrink-0 justify-center items-center group font-medium rounded-tremor-default border dark:shadow-dark-tremor-input px-4 py-2.5 bg-indigo-500 dark:bg-indigo-500 border-indigo-500 dark:border-indigo-500 text-white dark:text-white hover:bg-indigo-600 dark:hover:bg-indigo-600 hover:border-indigo-700 dark:hover:border-indigo-700 shadow-none no-underline"
          >
            {provider.logo && (
              <img src={provider.logo} alt={provider.name} className="size-8" />
            )}
            Sign in with {provider.name}
          </a>
        ))}
      </Card>
    </div>
  )
}

export default LoginPage
