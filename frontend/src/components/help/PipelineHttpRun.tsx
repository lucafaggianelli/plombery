import {
  Button,
  Tab,
  TabGroup,
  TabList,
  TabPanel,
  TabPanels,
} from '@tremor/react'
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline'
import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import {
  okaidia,
  oneLight,
} from 'react-syntax-highlighter/dist/esm/styles/prism'

import CopyButton from '@/components/CopyButton'
import Dialog from '@/components/Dialog'
import { getPipelineRunUrl } from '@/repository'

interface Props {
  pipelineId: string
  triggerId?: string
}

const PipelineHttpRun: React.FC<Props> = ({ pipelineId, triggerId }) => {
  const [open, setOpen] = useState(false)
  const isDark = document.documentElement.classList.contains('dark')

  const SNIPPETS = [
    {
      language: 'python',
      name: 'Python',
      code: `import httpx

httpx.post('${getPipelineRunUrl(pipelineId)}', json={${triggerId ? `\n  "trigger_id": "${triggerId}",` : ''}
  "params": {
    "name": "value",
  }
})`,
    },
    {
      language: 'js',
      name: 'JavaScript',
      code: `fetch('${getPipelineRunUrl(pipelineId)}', {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({${triggerId ? `\n    trigger_id: '${triggerId}',` : ''}
    params: {},
  }),
})`,
    },
  ]

  return (
    <>
      <Button
        color="indigo"
        variant="secondary"
        size="xs"
        icon={QuestionMarkCircleIcon}
        onClick={() => setOpen(true)}
      ></Button>

      <Dialog
        isOpen={open}
        title="Run via HTTP request"
        subtitle="You can run pipelines and triggers via HTTP requests"
        onClose={() => setOpen(false)}
      >
        <TabGroup>
          <TabList className="mt-8">
            {SNIPPETS.map((snippet) => (
              <Tab key={snippet.name}>{snippet.name}</Tab>
            ))}
          </TabList>
          <TabPanels>
            {SNIPPETS.map((snippet) => (
              <TabPanel key={snippet.name}>
                <div className="mt-6 relative group">
                  <SyntaxHighlighter
                    language={snippet.language}
                    style={isDark ? okaidia : oneLight}
                    customStyle={{ borderRadius: 8 }}
                  >
                    {snippet.code}
                  </SyntaxHighlighter>

                  <CopyButton
                    content={snippet.code}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-200/80 dark:bg-slate-800/80 rounded p-2"
                  />
                </div>
              </TabPanel>
            ))}
          </TabPanels>
        </TabGroup>
      </Dialog>
    </>
  )
}

export default PipelineHttpRun
