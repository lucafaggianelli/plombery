import { useQuery } from '@tanstack/react-query'
import { Card, Title } from '@tremor/react'
import React, { SVGProps } from 'react'

import { getApiUrl, getAuthProviders } from '@/repository'
import MicrosoftIcon from '@/components/icons/microsoft'
import GoogleIcon from '@/components/icons/google'
import { twMerge } from 'tailwind-merge'
import { useAuthState } from '@/contexts/AuthContext'
import { Navigate } from 'react-router'

const ICONS: Record<string, React.FC<SVGProps<SVGSVGElement>>> = {
  google: GoogleIcon,
  microsoft: MicrosoftIcon,
}

const LoginPage: React.FC = () => {
  const providersQuery = useQuery(getAuthProviders())
  const { isAuthenticated } = useAuthState()

  if (isAuthenticated) {
    return <Navigate to="/" />
  }

  return (
    <div
      className="bg-slate-100 dark:bg-slate-950 min-h-screen flex justify-center items-center"
      style={{
        backgroundImage: 'linear',
      }}
    >
      <div
        className={twMerge(
          'absolute inset-0',
          '[background-size:40px_40px]',
          'bg-center',
          '[background-image:linear-gradient(to_right,#e4e4e7_1px,transparent_1px),linear-gradient(to_bottom,#e4e4e7_1px,transparent_1px)]',
          'dark:[background-image:linear-gradient(to_right,#262626_1px,transparent_1px),linear-gradient(to_bottom,#262626_1px,transparent_1px)]'
        )}
      />
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-white [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)] dark:bg-black"></div>

      <Card className="w-auto">
        <div className="size-16 mx-auto mb-4 bg-tremor-brand-muted dark:bg-transparent rounded-full p-3">
          <img src="/logo.svg" alt="Plombery logo" />
        </div>

        <Title className="mb-12 text-center">Welcome to Plombery</Title>

        {providersQuery.data?.map((provider) => {
          const Icon = ICONS[provider.id]

          return (
            <a
              key={provider.name}
              href={`${getApiUrl()}/auth/login`}
              className="w-full flex gap-4 tremor-Button-root shrink-0 justify-center items-center group font-medium rounded-tremor-default border dark:shadow-dark-tremor-input px-4 py-1.5 bg-indigo-500 dark:bg-indigo-500 border-indigo-500 dark:border-indigo-500 text-white dark:text-white hover:bg-indigo-600 dark:hover:bg-indigo-600 hover:border-indigo-700 dark:hover:border-indigo-700 shadow-none no-underline"
            >
              {Icon && <Icon className="fill-current size-8" />}
              Sign in with {provider.name}
            </a>
          )
        })}
      </Card>
    </div>
  )
}

export default LoginPage
