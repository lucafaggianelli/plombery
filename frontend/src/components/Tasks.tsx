import { useState } from 'react'
import {
  Block,
  Bold,
  Button,
  Card,
  Flex,
  Icon,
  List,
  ListItem,
  Text,
  Title,
} from '@tremor/react'
import { TableCellsIcon } from '@heroicons/react/24/outline'

import { Pipeline, PipelineRun } from '@/types'
import { STATUS_COLORS, STATUS_ICONS } from '@/utils'
import DataViewerDialog from './DataViewerDialog'

interface Props {
  pipeline: Pipeline
  run: PipelineRun
}

const RunsTasksList: React.FC<Props> = ({ pipeline, run }) => {
  const [viewDataDialog, setViewDataDialog] = useState<string | undefined>()

  return (
    <Card>
      <DataViewerDialog
        runId={run.id}
        taskId={viewDataDialog || ''}
        open={!!viewDataDialog}
        onClose={() => setViewDataDialog(undefined)}
      />

      <Title>Tasks</Title>

      <List>
        {pipeline.tasks.map((task) => (
          <ListItem key={task.id}>
            <Flex spaceX="space-x-4">
              <Icon
                variant="light"
                icon={STATUS_ICONS[run.status]}
                color={STATUS_COLORS[run.status]}
              />
              <Block>
                <Text>
                  <Bold>{task.name}</Bold>
                </Text>
                {task.description && <Text truncate>{task.description}</Text>}
              </Block>
            </Flex>

            {run.status === 'completed' && (
              <Button
                variant="light"
                color="indigo"
                size="xs"
                icon={TableCellsIcon}
                onClick={() => setViewDataDialog(task.id)}
              >
                Data
              </Button>
            )}
          </ListItem>
        ))}
      </List>
    </Card>
  )
}

export default RunsTasksList
