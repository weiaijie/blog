import { Suspense, lazy } from 'react';
import type { ReactElement } from 'react';
import { createBrowserRouter } from 'react-router-dom';
import { Layout } from './components/layout/Layout';

const HomePage = lazy(() =>
  import('./pages/HomePage').then((module) => ({ default: module.HomePage }))
);
const AboutPage = lazy(() =>
  import('./pages/AboutPage').then((module) => ({ default: module.AboutPage }))
);
const SkillsPage = lazy(() =>
  import('./pages/SkillsPage').then((module) => ({ default: module.SkillsPage }))
);
const ProjectsPage = lazy(() =>
  import('./pages/ProjectsPage').then((module) => ({ default: module.ProjectsPage }))
);
const ProjectDetailPage = lazy(() =>
  import('./pages/ProjectDetailPage').then((module) => ({
    default: module.ProjectDetailPage
  }))
);
const ContactPage = lazy(() =>
  import('./pages/ContactPage').then((module) => ({ default: module.ContactPage }))
);
const PrivacyPage = lazy(() =>
  import('./pages/PrivacyPage').then((module) => ({ default: module.PrivacyPage }))
);
const NotFoundPage = lazy(() =>
  import('./pages/NotFoundPage').then((module) => ({ default: module.NotFoundPage }))
);

const withFallback = (element: ReactElement) => (
  <Suspense fallback={<div className="loading">页面加载中...</div>}>
    {element}
  </Suspense>
);

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: withFallback(<HomePage />) },
      { path: 'about', element: withFallback(<AboutPage />) },
      { path: 'skills', element: withFallback(<SkillsPage />) },
      { path: 'projects', element: withFallback(<ProjectsPage />) },
      { path: 'projects/:slug', element: withFallback(<ProjectDetailPage />) },
      { path: 'contact', element: withFallback(<ContactPage />) },
      { path: 'privacy', element: withFallback(<PrivacyPage />) },
      { path: '*', element: withFallback(<NotFoundPage />) }
    ]
  }
], {
  basename: import.meta.env.BASE_URL
});
