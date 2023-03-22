import PipelinesList from '@/components/PipelinesList'
import { Block, Card, ColGrid, Text, Title } from '@tremor/react'

export default function HomePage() {
  return (
    <main className="bg-slate-50 p-6 sm:p-10 min-h-screen">
      <Title>Mario Pype</Title>
      <Text>All your pipelines.</Text>

      <Block marginTop="mt-6">
        <PipelinesList />
      </Block>
    </main>
  )
}
