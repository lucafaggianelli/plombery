import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline'
import {
  Flex,
  Icon,
  NumberInput,
  Select,
  SelectItem,
  Text,
  TextInput,
} from '@tremor/react'
import { JSONSchema7, JSONSchema7TypeName } from 'json-schema'
import { useCallback, useState } from 'react'

import RangeSlider from './RangeSlider'

interface Props {
  schema: JSONSchema7
  errors?: Record<string, string>
}

interface FieldDefinition {
  defaultValue: string | undefined
  label: string
  name: string
  required: boolean
  type: JSONSchema7TypeName | 'enum'
  value: JSONSchema7
}

type FieldType = 'checkbox' | 'range' | 'number' | 'select' | 'text'

const renderers: Record<FieldType, (field: FieldDefinition) => JSX.Element> = {
  checkbox: (field: FieldDefinition) => {
    return (
      <div className="flex items-center mb-4">
        <input
          id={`${field.name}_hidden`}
          name={field.name}
          type="hidden"
          checked={true}
          readOnly={true}
          value="false"
        />
        <input
          id={field.name}
          name={field.name}
          type="checkbox"
          defaultChecked={field.defaultValue === 'true'}
          className="w-4 h-4 accent-indigo-500 bg-tremor-background rounded dark:bg-dark-tremor-background cursor-pointer"
        />

        <label htmlFor={field.name} className="pl-2 cursor-pointer">
          <Text>{field.label}</Text>
        </label>
      </div>
    )
  },
  number: (field: FieldDefinition) => {
    const minimum = field.value.minimum ?? field.value.exclusiveMinimum
    const maximum = field.value.maximum ?? field.value.exclusiveMaximum

    return (
      <NumberInput
        name={field.name}
        min={minimum}
        max={maximum}
        defaultValue={field.defaultValue}
        required={field.required}
      />
    )
  },
  range: (field: FieldDefinition) => {
    const minimum = field.value.minimum ?? field.value.exclusiveMinimum ?? 0
    const maximum = field.value.maximum ?? field.value.exclusiveMaximum ?? 0

    const step = field.type === 'number' ? (maximum - minimum) / 10 : 1
    return (
      <RangeSlider
        name={field.name}
        label={field.label}
        min={minimum}
        max={maximum}
        step={step}
        defaultValue={field.defaultValue}
        required={field.required}
      />
    )
  },
  select: (field: FieldDefinition) => {
    const [value, setValue] = useState<string>(field.defaultValue || '')

    return (
      <div>
        <Select
          defaultValue={field.defaultValue}
          onValueChange={setValue}
          value={value}
        >
          {field.value.enum!.map((item) => (
            <SelectItem key={item?.toString()} value={item!.toString()}>
              {item?.toString()}
            </SelectItem>
          ))}
        </Select>

        <input type="hidden" name={field.name} value={value} />
      </div>
    )
  },
  text: (field: FieldDefinition) => {
    const inputType = field.value.format === 'password' ? 'password' : 'text'
    return (
      <TextInput
        type={inputType}
        name={field.name}
        placeholder={field.label}
        defaultValue={field.defaultValue}
      />
    )
  },
}

const renderField = (field: FieldDefinition) => {
  let fieldType: FieldType = 'text'

  if (field.type === 'number' || field.type === 'integer') {
    const minimum = field.value.minimum ?? field.value.exclusiveMinimum
    const maximum = field.value.maximum ?? field.value.exclusiveMaximum

    if (minimum !== undefined && maximum !== undefined) {
      fieldType = 'range'
    } else {
      fieldType = 'number'
    }
  } else if (field.type === 'enum') {
    fieldType = 'select'
  } else if (field.type === 'boolean') {
    fieldType = 'checkbox'
  }

  return renderers[fieldType](field)
}

const JsonSchemaForm: React.FC<Props> = ({ errors = {}, schema }) => {
  const resolveDefinition = useCallback(
    (ref: string) => {
      const defs = schema.definitions || schema.$defs

      if (!defs) {
        return
      }

      const refName = ref.split('/').pop()!
      return defs[refName] as JSONSchema7
    },
    [schema]
  )

  const properties = schema.properties

  if (!properties) {
    return (
      <Text className="mt-4">
        This pipeline has no input parameters, but you can still run it!
      </Text>
    )
  }

  const inputFields = Object.entries(properties).map(([key, _value]) => {
    if (typeof _value === 'boolean') {
      return
    }

    let value = _value
    let defaultValue: string | undefined
    const label = value.title || key

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

    const type =
      (value.enum
        ? 'enum'
        : Array.isArray(value.type)
        ? value.type[0]
        : value.type) || 'string'
    const required = schema.required?.includes(key) ?? false

    const component = renderField({
      defaultValue,
      label,
      name: key,
      required,
      type,
      value,
    })

    return (
      <div key={key}>
        <Flex className="justify-between">
          <Text className="mb-2">
            {label}
            {required && ' *'}
          </Text>

          {value.description && (
            <Icon
              icon={QuestionMarkCircleIcon}
              tooltip={value.description}
              color="neutral"
            />
          )}
        </Flex>
        {component}

        {errors[key] && (
          <Text color="rose" className="mt-1">
            {errors[key]}
          </Text>
        )}
      </div>
    )
  })

  return <Flex className="gap-4 flex-col items-stretch">{inputFields}</Flex>
}

export default JsonSchemaForm
