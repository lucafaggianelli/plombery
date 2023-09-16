import { useEffect, useState } from 'react'

interface Props {
  startTime: Date
}

const Timer: React.FC<Props> = ({ startTime }) => {
  const [time, setTime] = useState(Date.now() - startTime.getTime())

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(Date.now() - startTime.getTime())
    }, 500)

    return () => {
      clearInterval(interval)
    }
  })

  return <span>{(time / 1000).toFixed(2)}</span>
}

export default Timer
