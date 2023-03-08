import {
  RouterProvider,
  createBrowserRouter,
  RouteObject,
} from 'react-router-dom'

const pages = import.meta.glob<React.FC>('./pages/**/[a-z0-9]*.tsx', {
  eager: true,
  import: 'default',
})

const routes: RouteObject[] = Object.entries(pages).map(
  ([filename, Component]) => {
    const path = filename
      .slice('./pages'.length)
      .replace(/index\.tsx$/, '')
      .split('/')
      .map((part) => part.replace(/\[(.+)\]/, ':$1'))
      .join('/')

    return {
      path,
      element: <Component />,
    }
  }
)

const Router = () => {
  const router = createBrowserRouter(routes)

  return <RouterProvider router={router} />
}

export default Router
