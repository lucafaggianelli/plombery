import {
  ClipboardDocumentCheckIcon,
  ClipboardDocumentIcon,
} from '@heroicons/react/24/outline'
import { Button } from '@tremor/react'
import { useRef, useState } from 'react'

interface Props {
  content: string
}

const CopyButton: React.FC<Props> = ({ content }) => {
  const [isCopied, setCopied] = useState(false)
  const timeout = useRef<ReturnType<typeof setTimeout>>()

  return (
    <Button
      variant="light"
      color="indigo"
      size="sm"
      icon={isCopied ? ClipboardDocumentCheckIcon : ClipboardDocumentIcon}
      onClick={() => {
        navigator.clipboard.writeText(content)

        setCopied(true)

        timeout.current = setTimeout(() => setCopied(false), 3000)
      }}
    />
  )
}

export default CopyButton
