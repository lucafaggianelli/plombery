import { Flex } from '@tremor/react'
import { PropsWithChildren, ReactNode } from 'react'

import { useAuthState } from '@/contexts/AuthContext'
import UserMenu from './UserMenu'

interface Props extends PropsWithChildren {
  header?: ReactNode
}

const PageLayout: React.FC<Props> = ({ children, header }) => {
  const { isAuthenticated } = useAuthState()

  return (
    <div className="bg-slate-50 p-6 sm:p-10 min-h-screen">
      <Flex className="items-start">
        {header && <div className="flex-grow">{header}</div>}
        {isAuthenticated && <UserMenu />}
      </Flex>

      <main>{children}</main>
    </div>
  )
}

export default PageLayout
