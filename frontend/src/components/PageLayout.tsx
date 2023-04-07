import { Button, Flex, Text } from '@tremor/react'
import { PropsWithChildren } from 'react'

import { useAuthState } from '@/contexts/AuthContext'

const PageLayout: React.FC<PropsWithChildren> = ({ children }) => {
  const { isAuthenticated, logout, user } = useAuthState()

  const userMenu = (
    <Flex className="justify-end space-x-4">
      <Text>{user?.name}</Text>
      <Button
        size="xs"
        variant="secondary"
        color="rose"
        onClick={async () => await logout()}
      >
        Logout
      </Button>
    </Flex>
  )

  return (
    <div>
      <Flex className="justify-end px-4 py-2">{isAuthenticated && userMenu}</Flex>
      {children}
    </div>
  )
}

export default PageLayout
