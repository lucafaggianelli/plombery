import { Text, Title } from '@tremor/react'

import PageLayout from '@/components/PageLayout'
import PipelinesList from '@/components/PipelinesList'

export default function HomePage() {
  return (
    <PageLayout
      header={
        <>
          <Title>Mario Pype</Title>
          <Text>All your pipelines.</Text>
        </>
      }
    >
      <div className="mt-6">
        <PipelinesList />
      </div>
    </PageLayout>
  )
}
