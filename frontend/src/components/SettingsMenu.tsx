import { Card, Icon, List, Tab, TabGroup, TabList, Text } from '@tremor/react'
import {
  Cog6ToothIcon,
  MoonIcon,
  SunIcon,
  ComputerDesktopIcon,
  CodeBracketSquareIcon,
  ArrowTopRightOnSquareIcon,
} from '@heroicons/react/24/outline'
import { useState } from 'react'

import { useAuthState } from '@/contexts/AuthContext'
import { getApiUrl } from '@/repository'
import { Popover, PopoverContent, PopoverTrigger } from './Popover'
import UserInfo from './UserInfo'

interface Props {}

const THEME_MODE_LIGHT = 0
const THEME_MODE_DARK = 1
const THEME_MODE_AUTO = 2
const THEME_MODES: Record<number, 'light' | 'dark'> = {
  [THEME_MODE_LIGHT]: 'light',
  [THEME_MODE_DARK]: 'dark',
}
const THEME_LOCAL_STORAGE_KEY = 'plomberyTheme'

const ThemeSwitch: React.FC = () => {
  const initialMode =
    localStorage[THEME_LOCAL_STORAGE_KEY] === 'dark'
      ? THEME_MODE_DARK
      : THEME_LOCAL_STORAGE_KEY in localStorage
      ? THEME_MODE_LIGHT
      : THEME_MODE_AUTO
  const [themeMode, setThemeMode] = useState(initialMode)

  return (
    <TabGroup
      onIndexChange={(i) => {
        let isDarkMode = false

        if (i === THEME_MODE_AUTO) {
          localStorage.removeItem(THEME_LOCAL_STORAGE_KEY)
          isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches
        } else {
          isDarkMode = i === THEME_MODE_DARK
          localStorage[THEME_LOCAL_STORAGE_KEY] = THEME_MODES[i]
        }

        if (isDarkMode) {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }

        return setThemeMode(i)
      }}
      index={themeMode}
    >
      <TabList variant="solid">
        <Tab icon={SunIcon}>Light</Tab>
        <Tab icon={MoonIcon}>Dark</Tab>
        <Tab icon={ComputerDesktopIcon}>System</Tab>
      </TabList>
    </TabGroup>
  )
}

const SettingsMenu: React.FC<Props> = () => {
  const { user, isAuthenticationEnabled } = useAuthState()

  // If auth is not enabled, just show a settings icon
  let dialogTrigger: React.ReactElement | string = <Cog6ToothIcon />

  // otherwise show the user initials
  if (isAuthenticationEnabled && user) {
    const nameParts = user.name.split(' ')
    dialogTrigger =
      nameParts.length > 1
        ? `${nameParts.at(0)![0]}${nameParts.at(-1)![0]}`
        : nameParts[0]
  }

  return (
    <Popover placement="bottom-start">
      <PopoverTrigger>
        <div
          className="flex justify-center items-center font-medium dark:bg-dark-tremor-background dark:ring-dark-tremor-ring ring-1 ring-slate-300 text-indigo-500 rounded-full hover:ring-2 hover:ring-indigo-400 dark:hover:ring-indigo-700 transition-shadow"
          style={{ width: 34, height: 34 }}
        >
          {dialogTrigger}
        </div>
      </PopoverTrigger>
      <PopoverContent>
        <Card className="p-0 pt-4 shadow-xl z-20">
          <List>
            <a
              className="flex items-center px-6 py-2 hover:bg-tremor-brand-faint hover:dark:bg-dark-tremor-brand-faint transition-colors"
              href={getApiUrl().replace(/\/api$/, '/docs')}
              target="_blank"
            >
              <Icon
                icon={CodeBracketSquareIcon}
                color="slate"
                className="mr-3"
              />
              <Text className="flex-grow no-underline border-0">
                REST API docs
              </Text>
              <Icon icon={ArrowTopRightOnSquareIcon} color="slate" />
            </a>
          </List>

          <div className="p-6">
            <ThemeSwitch />

            {isAuthenticationEnabled && <UserInfo />}
          </div>
        </Card>
      </PopoverContent>
    </Popover>
  )
}

export default SettingsMenu
