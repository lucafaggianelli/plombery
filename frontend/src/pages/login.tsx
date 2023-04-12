import { Button, Card, Title } from '@tremor/react'

import { getApiUrl } from '@/repository'

const LoginPage: React.FC = () => {
  return (
    <div className="h-screen flex justify-center items-center bg-slate-200">
      <Card className="w-auto">
        <div className="w-12 rounded-full mx-auto mb-4">
          <img src="/mario-pipe-flower.png" alt="Mario Pype logo" />
        </div>

        <Title className="mb-6">Welcome to Mario Pype</Title>

        <Button
          onClick={() => {
            location.href = `${getApiUrl()}/login`
          }}
          size="lg"
          color="indigo"
          className="shadow-none w-full"
        >
          Login
        </Button>
      </Card>
    </div>
  )
}

export default LoginPage
