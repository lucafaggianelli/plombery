import { useEffect } from 'react'
import useWebSocket from 'react-use-websocket'

import { getWebsocketUrl } from './repository'
import { WebSocketMessage } from './types'

/**
 * Hook to access the websocket
 *
 * This is a wrapper over react-use-websocket that enforces
 * the application protocol implemented on the backend
 *
 * @param topic
 * @returns
 */
export const useSocket = (topic?: string) => {
  const filter = (msg: MessageEvent) => {
    const { type } = JSON.parse(msg.data)

    return type === topic
  }

  const hook = useWebSocket(getWebsocketUrl().toString(), {
    share: true,
    filter: topic ? filter : undefined,
  })

  const lastMessage = hook.lastJsonMessage as unknown as WebSocketMessage

  const send = (type: string, data: any) => {
    hook.sendJsonMessage({
      type,
      data,
    })
  }

  const subscribe = (topic: string) => {
    send('subscribe', topic)
  }

  const unsubscribe = (topic: string) => {
    send('unsubscribe', topic)
  }

  useEffect(() => {
    if (topic) {
      subscribe(topic)

      return () => {
        unsubscribe(topic)
      }
    }
  }, [])

  return {
    lastMessage,
    send,
    subscribe,
    unsubscribe,
  }
}
