import {
  ClipboardDocumentCheckIcon,
  ClipboardDocumentIcon,
} from '@heroicons/react/24/outline'
import { Button } from '@tremor/react'
import { useRef, useState } from 'react'

interface Props {
  className?: string
  content: string
}

const CopyButton: React.FC<Props> = ({ className, content }) => {
  const [isCopied, setCopied] = useState(false)
  const timeout = useRef<ReturnType<typeof setTimeout> | null>(null)

  return (
    <Button
      variant="light"
      color="indigo"
      size="sm"
      icon={isCopied ? ClipboardDocumentCheckIcon : ClipboardDocumentIcon}
      tooltip="Click to copy"
      disabled={isCopied}
      className={className}
      onClick={async () => {
        await navigator.clipboard.writeText(content)

        setCopied(true)

        if (timeout.current) {
          clearTimeout(timeout.current)
        }

        timeout.current = setTimeout(() => setCopied(false), 3000)
      }}
    />
  )
}

export default CopyButton
