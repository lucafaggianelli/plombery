import { PlayIcon } from '@heroicons/react/24/outline'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Bold, Button, Flex, Text, TextInput } from '@tremor/react'
import { JSONSchema7 } from 'json-schema'
import { createRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { getPipelineInputSchema, runPipeline } from '../repository'
import { Pipeline } from '../types'
import Dialog from './Dialog'

const schemaToForm = (schema: JSONSchema7) => {
  const resolveDefinition = (ref: string) => {
    if (!schema.definitions) {
      return
    }

    const refName = ref.split('/').pop()!
    return schema.definitions[refName] as JSONSchema7
  }

  const properties = schema.properties

  if (!properties) {
    return <Text className="mt-4">This pipeline has no input</Text>
  }

  const inputFields = Object.entries(properties).map(([key, _value]) => {
    if (typeof _value === 'boolean') {
      return
    }

    let value = _value
    let defaultValue: string | undefined

    if (_value.allOf) {
      const multi_values = _value.allOf[0] as JSONSchema7
      defaultValue = _value.default?.toString()

      if (multi_values.$ref) {
        const def = resolveDefinition(multi_values.$ref)
        if (def) {
          value = def
        }
      }
    } else if (_value.$ref) {
      const def = resolveDefinition(_value.$ref)
      if (def) {
        value = def
      }
    } else {
      defaultValue = value.default?.toString()
    }

    const label = value.title || key
    const value_type =
      (value.enum
        ? 'enum'
        : Array.isArray(value.type)
        ? value.type[0]
        : value.type) || 'string'
    const required = schema.required?.includes(key)

    if (['number', 'integer'].includes(value_type)) {
      const minimum = value.minimum || value.exclusiveMinimum
      const maximum = value.maximum || value.exclusiveMaximum

      if (minimum !== undefined && maximum !== undefined) {
        const output = createRef<HTMLOutputElement>()
        const step = value_type === 'number' ? (maximum - minimum) / 10 : 1

        return (
          <div key={key}>
            <Text>{label}</Text>

            <input
              name={key}
              type="range"
              min={minimum}
              max={maximum}
              step={step}
              defaultValue={defaultValue}
              required={required}
              onInput={(event) =>
                output.current &&
                (output.current.value = (
                  event.target as HTMLInputElement
                ).value)
              }
              className="w-full mt-2 cursor-ew-resize appearance-none h-2 bg-slate-200 border border-slate-400 rounded"
            />

            <Flex className="items-baseline space-x-4">
              <div className="ml-1">
                <div className="border-r border-slate-300 h-2 w-1" />
                <Text>{minimum}</Text>
              </div>

              <Text>
                <Bold>
                  <output
                    ref={output}
                    className="px-2 py-1 rounded bg-slate-200 block truncate text-center"
                  >
                    {defaultValue}
                  </output>
                </Bold>
              </Text>

              <div className="mr-1">
                <div className="border-r border-slate-300 h-2 w-1" />
                <Text>{maximum}</Text>
              </div>
            </Flex>
          </div>
        )
      } else {
        return (
          <div key={key}>
            <Text>{label}</Text>
            <input
              name={key}
              type="number"
              min={minimum}
              max={maximum}
              defaultValue={defaultValue}
              className="border-gray-300 rounded-md border shadow-sm px-4 py-2 text-sm font-medium invalid:border-rose-500 mt-2"
              style={{ textAlign: 'end', width: '100%' }}
              required={required}
            />
          </div>
        )
      }
    } else if (value_type === 'enum') {
      return (
        <div key={key}>
          <Text>{label}</Text>
          <select
            name={key}
            defaultValue={defaultValue || ''}
            className="border-gray-300 rounded-md border shadow-sm px-4 py-2 text-sm font-medium w-full invalid:border-rose-500 mt-2"
            required={required}
          >
            <option disabled value="">
              Select...
            </option>
            {value.enum!.map((item) => (
              <option key={item?.toString()} value={item!.toString()}>
                {item?.toString()}
              </option>
            ))}
          </select>
        </div>
      )
    } else {
      return (
        <div key={key}>
          <Text>
            {label} {required && '*'}
          </Text>
          <TextInput
            name={key}
            placeholder={label}
            defaultValue={defaultValue}
            className="mt-2"
          />
        </div>
      )
    }
  })

  return <div className="space-y-4">{inputFields}</div>
}

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
              runPipelineMutation.mutateAsync(params, {
                onSuccess(data) {
                  navigate(
                    `/pipelines/${data.pipeline_id}/triggers/${data.trigger_id}/runs/${data.id}`
                  )
                },
              })
              setOpen(false)
            } catch (error) {
              console.error(error)
            }
          }}
        >
          {query.isLoading ? (
            'Loading...'
          ) : query.isError ? (
            'Error'
          ) : (
            <div style={{ width: 350 }}>{schemaToForm(query.data)}</div>
          )}

          <Flex className="justify-end space-x-6 mt-6">
            <Button
              type="button"
              variant="secondary"
              color="indigo"
              onClick={() => {
                setOpen(false)
              }}
              disabled={runPipelineMutation.isLoading}
            >
              Close
            </Button>

            <Button
              color="indigo"
              type="submit"
              icon={PlayIcon}
              disabled={runPipelineMutation.isLoading}
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
