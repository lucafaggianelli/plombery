import { PlayIcon } from '@heroicons/react/24/outline'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Button, Flex, Text } from '@tremor/react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { getPipelineInputSchema, runPipeline } from '../repository'
import { Pipeline } from '../types'
import Dialog from './Dialog'
import JsonSchemaForm from './JsonSchemaForm'

interface Props {
  pipeline: Pipeline
}

const ManualRunDialog: React.FC<Props> = ({ pipeline }) => {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  const query = useQuery({
    ...getPipelineInputSchema(pipeline.id),
    enabled: open,
  })

  const runPipelineMutation = useMutation(runPipeline(pipeline.id))

  const formErrors =
    runPipelineMutation.isError && runPipelineMutation.error.status === 422
      ? Object.fromEntries(
          runPipelineMutation.error.data.data.detail.map((detail: any) => [
            detail.loc.join('.'),
            detail.msg,
          ])
        )
      : undefined

  const genericError = runPipelineMutation.error?.message

  return (
    <>
      <Button
        color="indigo"
        variant="secondary"
        size="xs"
        icon={PlayIcon}
        onClick={() => setOpen(true)}
      >
        Run
      </Button>

      <Dialog
        isOpen={open}
        title={`Run ${pipeline.name} manually`}
        onClose={() => setOpen(false)}
      >
        <form
          onSubmit={async (event) => {
            event.preventDefault()

            const params = Object.fromEntries(
              new FormData(event.target as HTMLFormElement).entries()
            )

            try {
              const data = await runPipelineMutation.mutateAsync(params)
              navigate(
                `/pipelines/${data.pipeline_id}/triggers/${data.trigger_id}/runs/${data.id}`
              )
              setOpen(false)
            } catch (error) {
              console.error(error)
            }
          }}
        >
          {query.isPending || query.isFetching ? (
            'Loading...'
          ) : query.isError ? (
            'Error'
          ) : (
            <div style={{ width: 350 }}>
              <JsonSchemaForm schema={query.data} errors={formErrors} />

              {genericError && (
                <Text className="mt-2" color="rose">
                  {genericError}
                </Text>
              )}
            </div>
          )}

          <Flex className="justify-end space-x-6 mt-6">
            <Button
              type="button"
              variant="secondary"
              color="indigo"
              onClick={() => {
                setOpen(false)
              }}
              disabled={runPipelineMutation.isPending}
            >
              Close
            </Button>

            <Button
              color="indigo"
              type="submit"
              icon={PlayIcon}
              disabled={runPipelineMutation.isPending}
            >
              Run
            </Button>
          </Flex>
        </form>
      </Dialog>
    </>
  )
}

export default ManualRunDialog
