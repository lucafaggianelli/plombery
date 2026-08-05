import { Field, Label, Select } from '@headlessui/react'
import {
  ChevronDownIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/react/24/outline'
import { Flex, Icon, NumberInput, Text, TextInput } from '@tremor/react'
import { JSONSchema7, JSONSchema7TypeName } from 'json-schema'
import React, { useCallback } from 'react'

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

const renderers: Record<
  FieldType,
  (field: FieldDefinition) => React.ReactElement
> = {
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
    return (
      <div className="relative">
        <Select
          name={field.name}
          defaultValue={field.defaultValue}
          className="appearance-none text-sm/6 w-full outline-none text-left whitespace-nowrap truncate rounded-tremor-default focus:ring-2 transition duration-100 border px-3 py-1.5 shadow-tremor-input focus:border-tremor-brand-subtle focus:ring-tremor-brand-muted dark:shadow-dark-tremor-input dark:focus:border-dark-tremor-brand-subtle dark:focus:ring-dark-tremor-brand-muted pl-3 bg-tremor-background dark:bg-dark-tremor-background hover:bg-tremor-background-muted dark:hover:bg-dark-tremor-background-muted text-tremor-content dark:text-dark-tremor-content border-tremor-border dark:border-dark-tremor-border"
        >
          {field.value.enum!.map((item) => (
            <option key={item?.toString()} value={item!.toString()}>
              {item?.toString()}
            </option>
          ))}
        </Select>
        <ChevronDownIcon
          className="group pointer-events-none absolute top-2.5 right-2.5 size-4"
          aria-hidden="true"
        />
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
      <Field key={key}>
        <Flex className="mb-2 justify-between">
          <Label className="text-sm font-medium">
            {label}
            {required && ' *'}
          </Label>

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
      </Field>
    )
  })

  return <Flex className="gap-6 flex-col items-stretch">{inputFields}</Flex>
}

export default JsonSchemaForm
