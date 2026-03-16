import siteConfig from './site';

export interface RouteItem {
  name: string;
  path: string;
  icon?: React.ReactNode;
  isExternal?: boolean;
  children?: RouteItem[];
}

export const mainNavRoutes: RouteItem[] = [
  { name: '首页', path: '/' },
  { name: '关于我', path: '/about' },
  // { name: '技能', path: '/skills' },
  { name: '项目', path: '/projects' },
  { name: '联系', path: '/contact' },
];

export const footerNavRoutes: RouteItem[] = [
  { name: '首页', path: '/' },
  { name: '关于我', path: '/about' },
  // { name: '技能', path: '/skills' },
  { name: '项目', path: '/projects' },
  { name: '联系', path: '/contact' },
  { name: '隐私政策', path: '/privacy' },
  { name: '使用条款', path: '/terms' },
];

export const socialLinks: RouteItem[] = [
  {
    name: 'GitHub',
    path: siteConfig.social.github.url,
    isExternal: true,
  },
  // {
  //   name: 'LinkedIn',
  //   path: siteConfig.social.linkedin.url,
  //   isExternal: true,
  // },
  ...(siteConfig.social.twitter.url
    ? [
        {
          name: 'Twitter',
          path: siteConfig.social.twitter.url,
          isExternal: true,
        } satisfies RouteItem,
      ]
    : []),
];

export const getAllRoutes = (): RouteItem[] => {
  return [
    ...mainNavRoutes,
    ...footerNavRoutes.filter(
      (route) => !mainNavRoutes.some((mainRoute) => mainRoute.path === route.path),
    ),
  ];
};

export const getRouteByPath = (path: string): RouteItem | undefined => {
  return getAllRoutes().find((route) => route.path === path);
};

export default mainNavRoutes;
