import { Bold, Col, Flex, Grid, Text } from '@tremor/react'
import { createRef } from 'react'

interface Props
  extends Omit<
    React.InputHTMLAttributes<HTMLInputElement>,
    'type' | 'onInput'
  > {
  label?: string
}

const RangeSlider: React.FC<Props> = ({ label, ...props }) => {
  const output = createRef<HTMLOutputElement>()

  return (
    <div>
      <input
        type="range"
        onInput={(event) =>
          output.current &&
          (output.current.value = (event.target as HTMLInputElement).value)
        }
        className="w-full cursor-ew-resize appearance-none accent-indigo-500 h-2 bg-tremor-background border border-tremor-border dark:border-dark-tremor-border dark:bg-dark-tremor-background rounded"
        {...props}
      />

      <Grid numItems={3} className="items-baseline">
        <Col>
          <div className="ml-1 inline-block">
            <div
              className="border-r border-slate-300 dark:border-slate-600 h-2 mx-auto"
              style={{ width: 1 }}
            />
            <Text>{props.min}</Text>
          </div>
        </Col>

        <Flex className="justify-center">
          <Text>
            <Bold>
              <output
                ref={output}
                className="px-2 py-1 rounded bg-tremor-background-subtle dark:bg-dark-tremor-background-subtle block truncate text-center"
              >
                {props.defaultValue}
              </output>
            </Bold>
          </Text>
        </Flex>

        <Flex className="justify-end">
          <div className="mr-1">
            <div
              className="border-r border-slate-300 dark:border-slate-600 h-2 mx-auto"
              style={{ width: 1 }}
            />
            <Text>{props.max}</Text>
          </div>
        </Flex>
      </Grid>
    </div>
  )
}

export default RangeSlider
