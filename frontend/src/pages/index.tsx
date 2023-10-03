import { Col, Grid, Title } from '@tremor/react'

import PageLayout from '@/components/PageLayout'
import PipelinesList from '@/components/PipelinesList'
import RunsList from '@/components/RunsList'
import { useQuery } from '@tanstack/react-query'
import { listRuns } from '@/repository'

const HomePage: React.FC = () => {
  const runsQuery = useQuery(listRuns())

  return (
    <PageLayout
      header={
        <>
          <Title>Plombery</Title>
        </>
      }
    >
      <Grid numItemsMd={2} className="gap-6 mt-6">
        <Col>
          <PipelinesList />
        </Col>

        <Col>
          <RunsList query={runsQuery} />
        </Col>
      </Grid>
    </PageLayout>
  )
}

export default HomePage
