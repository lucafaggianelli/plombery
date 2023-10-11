import { Card, Flex, Subtitle, Title } from '@tremor/react'
import { Dialog as HUDialog, Transition } from '@headlessui/react'
import { Fragment, PropsWithChildren, ReactNode } from 'react'

interface Props extends PropsWithChildren {
  footer?: ReactNode
  isOpen: boolean
  subtitle?: string
  title?: string
  onClose: () => any
}

const Dialog: React.FC<Props> = ({
  children,
  footer,
  isOpen,
  subtitle,
  title,
  onClose,
}) => {
  return (
    <Transition show={isOpen} as={Fragment}>
      <HUDialog onClose={onClose} className="relative z-50">
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div
            className="fixed inset-0 bg-black/30 dark:bg-black/50 backdrop-blur-sm"
            aria-hidden="true"
          />
        </Transition.Child>

        <div className="fixed inset-0 flex w-screen items-center justify-center p-12">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 translate-y-1/3"
            enterTo="opacity-100 translate-y-0"
            leave="ease-in duration-300"
            leaveFrom="opacity-100 translate-y-0"
            leaveTo="opacity-0 -translate-y-1/3"
          >
            <HUDialog.Panel className="max-w-full">
              <Card>
                {title && (
                  <HUDialog.Title>
                    <Title>{title}</Title>
                  </HUDialog.Title>
                )}

                {subtitle && <Subtitle>{subtitle}</Subtitle>}

                <div className={(title || subtitle) && 'mt-6'}>{children}</div>

                {footer && (
                  <Flex className="justify-end space-x-6 mt-6">{footer}</Flex>
                )}
              </Card>
            </HUDialog.Panel>
          </Transition.Child>
        </div>
      </HUDialog>
    </Transition>
  )
}

export default Dialog
