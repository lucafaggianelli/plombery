import { io } from 'socket.io-client'

import { getWebsocketUrl } from './repository'

export const socket = io(getWebsocketUrl().toString(), {
  transports: ['websocket'],
  path: '/ws/socket.io',
})
