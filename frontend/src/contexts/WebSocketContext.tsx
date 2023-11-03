import { PropsWithChildren, useEffect, useState } from 'react'

import { socket } from '@/socket'

interface Props extends PropsWithChildren {}

const WebSocketContext: React.FC<Props> = ({ children }) => {
  const [_, setIsConnected] = useState(socket.connected)

  useEffect(() => {
    function onConnect() {
      setIsConnected(true)
    }

    function onDisconnect() {
      setIsConnected(false)
    }

    socket.on('connect', onConnect)
    socket.on('disconnect', onDisconnect)

    return () => {
      socket.off('connect', onConnect)
      socket.off('disconnect', onDisconnect)
    }
  }, [])

  return children
}

export default WebSocketContext
