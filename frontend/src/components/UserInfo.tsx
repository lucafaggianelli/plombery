import { ArrowRightStartOnRectangleIcon } from '@heroicons/react/24/outline'
import { Button, Flex } from '@tremor/react'

import { useAuthState } from '@/contexts/AuthContext'

const UserInfo: React.FC = () => {
  const { logout, user } = useAuthState()

  if (!user) {
    return <div>Not authenticated</div>
  }

  return (
    <Flex className="gap-4 px-8 mb-6">
      <div>
        <div>{user.name}</div>
        <div className="text-sm dark:text-dark-tremor-content-subtle text-tremor-content-subtle">
          {user.email}
        </div>
      </div>

      <Button
        size="xs"
        variant="secondary"
        color="rose"
        icon={ArrowRightStartOnRectangleIcon}
        onClick={async () => await logout()}
        tooltip="Logout"
      />
    </Flex>
  )
}

export default UserInfo
