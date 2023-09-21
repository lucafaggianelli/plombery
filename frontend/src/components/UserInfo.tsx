import { useAuthState } from "@/contexts/AuthContext"
import { ArrowRightOnRectangleIcon } from "@heroicons/react/24/outline"
import { Button, Flex, Subtitle, Title } from "@tremor/react"

const UserInfo: React.FC = () => {
  const { logout, user } = useAuthState()

  if (!user) {
    return <div>Not authenticated</div>
  }

  return (
    <Flex className="gap-4 mt-8">
      <div>
        <Title>{user.name}</Title>
        <Subtitle>{user.email}</Subtitle>
      </div>

      <Button
        size="xs"
        variant="secondary"
        color="rose"
        icon={ArrowRightOnRectangleIcon}
        onClick={async () => await logout()}
      >
      </Button>
    </Flex>
  )
}

export default UserInfo
