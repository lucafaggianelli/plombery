import PipelinesList from '@/src/components/PipelinesList'
import { Block, Card, ColGrid, Text, Title } from '@tremor/react'

export default function HomePage() {
  return (
    <main className="bg-slate-50 p-6 sm:p-10 min-h-screen">
      <Title>Mario ETL</Title>
      <Text>All your pipelines.</Text>

      <ColGrid
        numColsMd={2}
        numColsLg={3}
        gapX="gap-x-6"
        gapY="gap-y-6"
        marginTop="mt-6"
      >
        <Card>
          {/* Placeholder to set height */}
          <div className="h-28" />
        </Card>
        <Card>
          {/* Placeholder to set height */}
          <div className="h-28" />
        </Card>
        <Card>
          {/* Placeholder to set height */}
          <div className="h-28" />
        </Card>
      </ColGrid>

      <Block marginTop="mt-6">
        <PipelinesList />
      </Block>
    </main>
  )
}
