import { XCircleIcon } from '@heroicons/react/24/outline'
import { UseQueryResult } from '@tanstack/react-query'
import { Button, Flex, Icon, Text, Title } from '@tremor/react'
import { HTTPError } from 'ky'

interface Props {
  query: UseQueryResult<any, HTTPError>
}

const ErrorAlert: React.FC<Props> = ({ query }) => {
  if (!query.isError) {
    return null
  }

  return (
    <>
      <Flex justifyContent="start">
        <Icon icon={XCircleIcon} color="rose" className="pl-0" />
        <Title>Error fetching data</Title>
      </Flex>
      <Text>{query.error.message}</Text>
      <Flex justifyContent="center" className="mt-4">
        <Button
          color="rose"
          variant="light"
          size="xs"
          onClick={() => query.refetch()}
        >
          Retry
        </Button>
      </Flex>
    </>
  )
}

export default ErrorAlert
