import { Button } from '@tremor/react'

import { getApiUrl } from '@/repository'

const LoginPage: React.FC = () => {
  return (
    <div className="h-screen flex justify-center items-center bg-slate-200">
      <Button
        onClick={() => {
          location.href = `${getApiUrl()}/login`
        }}
        color="indigo"
      >
        Login
      </Button>
    </div>
  )
}

export default LoginPage
