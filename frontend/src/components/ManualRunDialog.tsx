import { useQuery } from '@tanstack/react-query'
import { Block, Button, Flex, Text, TextInput } from '@tremor/react'
import { JSONSchema7 } from 'json-schema'
import { useState } from 'react'

import { getPipelineInputSchema } from '../repository'
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
    return <Text marginTop="mt-4">This pipeline has no input</Text>
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

    if (['number', 'float', 'integer'].includes(value_type)) {
      const minimum = value.minimum || value.exclusiveMinimum
      const maximum = value.maximum || value.exclusiveMaximum

      if (minimum !== undefined && maximum !== undefined) {
        const step = (maximum - minimum) / 10

        return (
          <Block key={key}>
            <input
              name={key}
              type="range"
              min={minimum}
              max={maximum}
              step={step}
              defaultValue={defaultValue}
              required={required}
            />
          </Block>
        )
      } else {
        return (
          <Block key={key}>
            <Text>{label}</Text>
            <input
              name={key}
              type="number"
              min={minimum}
              max={maximum}
              defaultValue={defaultValue}
              className="tr-border-gray-300 tr-rounded-md tr-border tr-shadow-sm tr-pl-4 tr-pr-4 tr-pt-2 tr-pb-2 tr-text-sm tr-font-medium"
              style={{ textAlign: 'end', width: '100%' }}
              required={required}
            />
          </Block>
        )
      }
    } else if (value_type === 'enum') {
      return (
        <div key={key}>
          <Text>{label}</Text>
          <select
            name={key}
            defaultValue={defaultValue || ''}
            className="tr-border-gray-300 tr-rounded-md tr-border tr-shadow-sm tr-pl-4 tr-pr-4 tr-pt-2 tr-pb-2 tr-text-sm tr-font-medium tr-w-full"
            required={required}
          >
            <option disabled value="">
              Select...
            </option>
            {value.enum!.map((item) => (
              <option key={item?.toString()} value={item?.toString()}>
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
          />
        </div>
      )
    }
  })

  return <Block spaceY="space-y-4">{inputFields}</Block>
}

interface Props {
  pipeline: Pipeline
}

const ManualRunDialog: React.FC<Props> = ({ pipeline }) => {
  const [open, setOpen] = useState(false)

  const query = useQuery({
    queryKey: ['pipeline-input', pipeline.id],
    queryFn: () => getPipelineInputSchema(pipeline.id),
    enabled: open,
  })

  return (
    <>
      <Button
        color="indigo"
        variant="secondary"
        size="xs"
        onClick={() => setOpen(true)}
      >
        Run manually
      </Button>

      <Dialog
        isOpen={open}
        title={`Run ${pipeline.name} manually`}
        onClose={() => setOpen(false)}
      >
        <form
          method="dialog"
          onSubmit={(event) => {
            console.log(
              'submitted',
              Object.fromEntries(
                new FormData(event.target as HTMLFormElement).entries()
              )
            )
          }}
        >
          {query.isLoading ? (
            'Loading...'
          ) : (
            <div style={{ width: 350 }}>{schemaToForm(query.data)}</div>
          )}

          <Flex
            justifyContent="justify-end"
            spaceX="space-x-6"
            marginTop="mt-6"
          >
            <Button
              variant="secondary"
              color="indigo"
              onClick={() => {
                setOpen(false)
              }}
            >
              Close
            </Button>

            <Button color="indigo" type="submit">
              Run
            </Button>
          </Flex>
        </form>
      </Dialog>
    </>
  )
}

export default ManualRunDialog
