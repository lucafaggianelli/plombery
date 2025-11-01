import { useState } from 'react'
import {
  Button,
  Card,
  Flex,
  List,
  ListItem,
  Subtitle,
  Text,
  Title,
} from '@tremor/react'
import { TableCellsIcon } from '@heroicons/react/24/outline'

import { Pipeline, PipelineRun } from '@/types'
import { getTasksColors } from '@/utils'
import DataViewerDialog from './DataViewerDialog'
import TaskRunStatusIcon from './TaskRunStatusIcon'

interface Props {
  pipeline: Pipeline
  run: PipelineRun
}

const RunsTasksList: React.FC<Props> = ({ pipeline, run }) => {
  const [viewDataDialog, setViewDataDialog] = useState<string | undefined>()

  const tasksColors = getTasksColors(pipeline.tasks)

  return (
    <Card>
      <DataViewerDialog
        runId={run.id}
        taskId={viewDataDialog || ''}
        open={!!viewDataDialog}
        onClose={() => setViewDataDialog(undefined)}
      />

      <Title className="mb-4">Tasks</Title>

      <List>
        {pipeline.tasks.map((task, i) => {
          const taskRun = run.task_runs ? run.task_runs[i] : undefined

          return (
            <ListItem key={task.id} className="space-x-4">
              <TaskRunStatusIcon status={taskRun?.status} />

              <div className="truncate flex-grow">
                <Flex className="justify-start">
                  <div
                    className={`h-2 w-2 mr-2 rounded-full ${
                      tasksColors[task.id]
                    }`}
                  />
                  <Subtitle className="truncate text-base text-tremor-content-emphasis dark:text-dark-tremor-content-emphasis">
                    {task.name}
                  </Subtitle>
                </Flex>
                {task.description && (
                  <Text className="truncate">{task.description}</Text>
                )}
              </div>

              {taskRun?.task_output_id && (
                <Button
                  variant="light"
                  color="indigo"
                  size="xs"
                  icon={TableCellsIcon}
                  tooltip="View task output data"
                  onClick={() => setViewDataDialog(taskRun.task_output_id)}
                />
              )}

              {taskRun?.duration && (
                <div className="font-medium tabular-nums whitespace-nowrap">
                  {(taskRun.duration / 1000).toFixed(2) + ' s'}
                </div>
              )}
            </ListItem>
          )
        })}
      </List>
    </Card>
  )
}

export default RunsTasksList
