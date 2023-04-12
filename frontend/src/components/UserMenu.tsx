import { useAuthState } from '@/contexts/AuthContext'
import { Button, Card, Divider, Subtitle, Text, Title } from '@tremor/react'
import { Popover, PopoverContent, PopoverTrigger } from './Popover'
import { ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline'

interface Props {}

const UserMenu: React.FC<Props> = () => {
  const { logout, user } = useAuthState()

  if (!user) {
    return <div>Not logged in</div>
  }

  const nameParts = user.name.split(' ')
  const initials =
    nameParts.length > 1
      ? `${nameParts.at(0)![0]}${nameParts.at(-1)![0]}`
      : nameParts[0]

  return (
    <Popover placement="bottom-start">
      <PopoverTrigger>
        <div
          className="flex justify-center items-center font-medium bg-white ring-1 ring-slate-200 text-indigo-500 rounded-full ml-4 hover:ring-2 transition-shadow"
          style={{ width: 34, height: 34 }}
        >
          {initials}
        </div>
      </PopoverTrigger>
      <PopoverContent>
        <Card className="shadow-xl">
          <Title>{user.name}</Title>
          <Subtitle>{user.email}</Subtitle>

          <Divider />

          <Button
            size="xs"
            variant="secondary"
            color="rose"
            icon={ArrowRightOnRectangleIcon}
            className="w-full"
            onClick={async () => await logout()}
          >
            Logout
          </Button>
        </Card>
      </PopoverContent>
    </Popover>
  )
}

export default UserMenu
