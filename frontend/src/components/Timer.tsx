import { useEffect, useState } from 'react'

import { formatDuration } from '@/utils'

interface Props {
  startTime: Date
}

const Timer: React.FC<Props> = ({ startTime }) => {
  const [time, setTime] = useState(Date.now() - startTime.getTime())

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(Date.now() - startTime.getTime())
      // The value is pretty random so to have an uneven and more natural timer
    }, 237)

    return () => {
      clearInterval(interval)
    }
  })

  return <span>{formatDuration(time)}</span>
}

export default Timer
