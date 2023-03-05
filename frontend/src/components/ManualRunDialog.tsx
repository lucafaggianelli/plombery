import { useQuery } from '@tanstack/react-query'
import {
  Block,
  Button,
  Card,
  Divider,
  Flex,
  Text,
  TextInput,
  Title,
} from '@tremor/react'
import { createRef, MouseEventHandler } from 'react'
import { getPipelineInputSchema } from '../repository'
import { Pipeline } from '../types'

const schemaToForm = (schema: any) => {
  const properties: Record<string, any> = schema.properties

  if (!properties) {
    return <Text marginTop='mt-4'>This pipeline has no input</Text>
  }

  const inputFields = Object.entries(properties).map(([key, _value]) => {
    let value = _value
    let defaultValue

    if (_value.allOf) {
      const multi_values = _value.allOf[0]
      defaultValue = _value.default

      if (multi_values.$ref) {
        const ref = multi_values['$ref'].split('/').pop()
        value = schema['definitions'][ref]
      }
    } else {
      defaultValue = value.default
    }

    const label = value.title || key
    const value_type = value.enum ? 'enum' : value.type

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
            defaultValue={defaultValue}
            className="tr-border-gray-300 tr-rounded-md tr-border tr-shadow-sm tr-pl-4 tr-pr-4 tr-pt-2 tr-pb-2 tr-text-sm tr-font-medium tr-w-full"
          >
            {value.enum.map((item: string) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      )
    } else {
      return (
        <div key={key}>
          <Text>{label}</Text>
          <TextInput
            name={key}
            placeholder={label}
            defaultValue={defaultValue}
          />
        </div>
      )
    }
  })

  return (
    <Block marginTop="mt-8" spaceY="space-y-4">
      {inputFields}
    </Block>
  )
}

interface Props {
  pipeline: Pipeline
}

const ManualRunDialog: React.FC<Props> = ({ pipeline }) => {
  const dialog = createRef<HTMLDialogElement>()

  const query = useQuery({
    queryKey: ['pipeline-input', pipeline.id],
    queryFn: () => getPipelineInputSchema(pipeline.id),
  })

  if (query.isLoading) {
    return <div>Loading...</div>
  }

  const closeDialogOnBackdropClick: MouseEventHandler<HTMLDialogElement> = (
    event
  ) => {
    var rect = dialog.current!.getBoundingClientRect()
    var isInDialog =
      rect.top <= event.clientY &&
      event.clientY <= rect.top + rect.height &&
      rect.left <= event.clientX &&
      event.clientX <= rect.left + rect.width

    if (!isInDialog) {
      dialog.current?.close()
    }
  }

  return (
    <>
      <Button
        color="indigo"
        variant="secondary"
        size="xs"
        onClick={() => dialog.current?.showModal()}
      >
        Run manually
      </Button>

      <dialog
        ref={dialog}
        style={{ padding: 0, background: 'transparent', overflow: 'visible' }}
        onClick={closeDialogOnBackdropClick}
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
          <Card>
            <Title>Run {pipeline.name} manually</Title>

            <div style={{ width: 350 }}>{schemaToForm(query.data)}</div>

            <Divider />

            <Flex justifyContent="justify-end" spaceX="space-x-6">
              <Button
                variant="secondary"
                color="indigo"
                onClick={() => {
                  dialog.current?.close()
                }}
              >
                Close
              </Button>

              <Button color="indigo" type="submit">
                Run
              </Button>
            </Flex>
          </Card>
        </form>
      </dialog>
    </>
  )
}

export default ManualRunDialog
