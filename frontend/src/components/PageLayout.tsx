import { Flex } from '@tremor/react'
import { PropsWithChildren, ReactNode } from 'react'

import SettingsMenu from './SettingsMenu'

interface Props extends PropsWithChildren {
  header?: ReactNode
}

const PageLayout: React.FC<Props> = ({ children, header }) => {
  return (
    <div className="bg-slate-100 dark:bg-slate-950 p-6 sm:p-10 min-h-screen">
      <Flex className="items-start gap-4 md:gap-8">
        {header && <div className="flex-grow max-w-full">{header}</div>}
        <SettingsMenu />
      </Flex>

      <main>{children}</main>
    </div>
  )
}

export default PageLayout
