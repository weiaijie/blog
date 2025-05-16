/**
 * routes.ts
 *
 * 描述：路由配置文件，定义网站的导航结构和路由信息
 *
 * 功能：
 * - 定义网站的主导航菜单路由
 * - 定义页脚导航菜单路由
 * - 定义社交媒体链接
 * - 提供路由查询和管理的辅助函数
 *
 * 主要接口/常量：
 * - RouteItem：路由项目接口
 * - mainNavRoutes：主导航菜单路由
 * - footerNavRoutes：页脚导航菜单路由
 * - socialLinks：社交媒体链接
 *
 * 导出：
 * - RouteItem 接口
 * - 各种路由常量和辅助函数
 * - mainNavRoutes（默认导出）
 */

// 路由配置文件
export interface RouteItem {
  name: string;
  path: string;
  icon?: React.ReactNode; // 可选的图标
  isExternal?: boolean;   // 是否为外部链接
  children?: RouteItem[]; // 子路由（如果需要）
}

// 主导航菜单路由
export const mainNavRoutes: RouteItem[] = [
  { name: '首页', path: '/' },
  { name: '关于我', path: '/about' },
  { name: '技能', path: '/skills' },
  { name: '项目', path: '/projects' },
  { name: '博客', path: '/blog' },
  { name: '联系', path: '/contact' },
];

// 页脚导航菜单路由（如果需要）
export const footerNavRoutes: RouteItem[] = [
  { name: '首页', path: '/' },
  { name: '关于我', path: '/about' },
  { name: '技能', path: '/skills' },
  { name: '项目', path: '/projects' },
  { name: '博客', path: '/blog' },
  { name: '联系', path: '/contact' },
  { name: '隐私政策', path: '/privacy' },
  { name: '条款和条件', path: '/terms' },
];

// 社交媒体链接（如果需要）
export const socialLinks: RouteItem[] = [
  {
    name: 'GitHub',
    path: 'https://github.com/username',
    isExternal: true
  },
  {
    name: 'LinkedIn',
    path: 'https://linkedin.com/in/username',
    isExternal: true
  },
  {
    name: 'Twitter',
    path: 'https://twitter.com/username',
    isExternal: true
  },
];

// 获取所有路由的辅助函数
export const getAllRoutes = (): RouteItem[] => {
  return [
    ...mainNavRoutes,
    ...footerNavRoutes.filter(route =>
      !mainNavRoutes.some(mainRoute => mainRoute.path === route.path)
    ),
  ];
};

// 根据路径获取路由的辅助函数
export const getRouteByPath = (path: string): RouteItem | undefined => {
  return getAllRoutes().find(route => route.path === path);
};

export default mainNavRoutes;
