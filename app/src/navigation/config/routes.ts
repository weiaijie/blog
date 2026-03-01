/**
 * 路由配置
 * 
 * 定义应用中所有路由的配置信息，包括：
 * 1. 页面组件映射
 * 2. 路由元数据
 * 3. 导航选项
 * 4. 权限设置
 */

import { RouteConfig } from '../types';

// 导入页面组件
import HomeScreen from '../../screens/home/HomeScreen';
import TodoScreen from '../../screens/todo/TodoScreen';
import ProfileScreen from '../../screens/profile/ProfileScreen';
import SettingsScreen from '../../screens/settings/SettingsScreen';
import LoginScreen from '../../screens/auth/LoginScreen';
import NavigationTest from '../components/NavigationTest';

/**
 * 主要Tab路由配置
 * 这些路由会显示在底部Tab导航栏中
 */
export const tabRoutes: RouteConfig[] = [
  {
    name: 'Home',
    component: NavigationTest, // 暂时使用导航测试页面
    title: '首页',
    icon: '🏠',
    headerShown: true,
    tabBarVisible: true,
    gestureEnabled: true,
    transition: 'fade',
    requireAuth: false,
    meta: {
      description: '应用主页，展示主要功能',
      category: 'main',
    },
  },
  {
    name: 'Todo',
    component: TodoScreen,
    title: '待办',
    icon: '📝',
    headerShown: true,
    tabBarVisible: true,
    gestureEnabled: true,
    transition: 'slide',
    requireAuth: false,
    meta: {
      description: '待办事项管理',
      category: 'productivity',
    },
  },
  {
    name: 'Profile',
    component: ProfileScreen,
    title: '个人',
    icon: '👤',
    headerShown: true,
    tabBarVisible: true,
    gestureEnabled: true,
    transition: 'slide',
    requireAuth: true,
    meta: {
      description: '个人中心和用户信息',
      category: 'user',
    },
  },
  {
    name: 'Settings',
    component: SettingsScreen,
    title: '设置',
    icon: '⚙️',
    headerShown: true,
    tabBarVisible: true,
    gestureEnabled: true,
    transition: 'slide',
    requireAuth: false,
    meta: {
      description: '应用设置和配置',
      category: 'system',
    },
  },
];

/**
 * 认证相关路由配置
 * 这些路由用于用户认证流程
 */
export const authRoutes: RouteConfig[] = [
  {
    name: 'Login',
    component: LoginScreen,
    title: '登录',
    icon: '🔐',
    headerShown: true,
    tabBarVisible: false,
    gestureEnabled: true,
    transition: 'slide',
    requireAuth: false,
    meta: {
      description: '用户登录页面',
      category: 'auth',
      fullScreen: true,
    },
  },
  {
    name: 'Register',
    component: LoginScreen, // 暂时使用登录页面，后续可以创建专门的注册页面
    title: '注册',
    icon: '📝',
    headerShown: true,
    tabBarVisible: false,
    gestureEnabled: true,
    transition: 'slide',
    requireAuth: false,
    meta: {
      description: '用户注册页面',
      category: 'auth',
      fullScreen: true,
    },
  },
];

/**
 * 详情页路由配置
 * 这些路由用于显示详细信息，通常通过栈导航访问
 */
export const detailRoutes: RouteConfig[] = [
  {
    name: 'TodoDetail',
    component: TodoScreen, // 暂时使用待办页面，后续可以创建专门的详情页面
    title: '待办详情',
    icon: '📄',
    headerShown: true,
    tabBarVisible: false,
    gestureEnabled: true,
    transition: 'slide',
    requireAuth: false,
    meta: {
      description: '待办事项详情页面',
      category: 'detail',
      parentRoute: 'Todo',
    },
  },
  {
    name: 'UserProfile',
    component: ProfileScreen, // 暂时使用个人页面，后续可以创建专门的用户资料页面
    title: '用户资料',
    icon: '👥',
    headerShown: true,
    tabBarVisible: false,
    gestureEnabled: true,
    transition: 'slide',
    requireAuth: true,
    meta: {
      description: '用户资料详情页面',
      category: 'detail',
      parentRoute: 'Profile',
    },
  },
];

/**
 * 信息页路由配置
 * 这些路由用于显示应用信息和帮助内容
 */
export const infoRoutes: RouteConfig[] = [
  {
    name: 'About',
    component: SettingsScreen, // 暂时使用设置页面，后续可以创建专门的关于页面
    title: '关于',
    icon: 'ℹ️',
    headerShown: true,
    tabBarVisible: false,
    gestureEnabled: true,
    transition: 'fade',
    requireAuth: false,
    meta: {
      description: '关于应用的信息',
      category: 'info',
      parentRoute: 'Settings',
    },
  },
  {
    name: 'Help',
    component: SettingsScreen, // 暂时使用设置页面，后续可以创建专门的帮助页面
    title: '帮助',
    icon: '❓',
    headerShown: true,
    tabBarVisible: false,
    gestureEnabled: true,
    transition: 'slide',
    requireAuth: false,
    meta: {
      description: '应用使用帮助',
      category: 'info',
      parentRoute: 'Settings',
    },
  },
];

/**
 * 所有路由配置的合集
 */
export const allRoutes: RouteConfig[] = [
  ...tabRoutes,
  ...authRoutes,
  ...detailRoutes,
  ...infoRoutes,
];

/**
 * 根据类别获取路由
 */
export const getRoutesByCategory = (category: string): RouteConfig[] => {
  return allRoutes.filter(route => route.meta?.category === category);
};

/**
 * 获取Tab路由（用于底部导航栏）
 */
export const getTabRoutes = (): RouteConfig[] => {
  return allRoutes.filter(route => route.tabBarVisible === true);
};

/**
 * 获取需要认证的路由
 */
export const getAuthRequiredRoutes = (): RouteConfig[] => {
  return allRoutes.filter(route => route.requireAuth === true);
};

/**
 * 获取公开路由（不需要认证）
 */
export const getPublicRoutes = (): RouteConfig[] => {
  return allRoutes.filter(route => route.requireAuth === false);
};

/**
 * 根据路由名称获取路由配置
 */
export const getRouteConfig = (routeName: string): RouteConfig | undefined => {
  return allRoutes.find(route => route.name === routeName);
};

/**
 * 检查路由是否存在
 */
export const routeExists = (routeName: string): boolean => {
  return allRoutes.some(route => route.name === routeName);
};

/**
 * 获取路由的父路由
 */
export const getParentRoute = (routeName: string): RouteConfig | undefined => {
  const route = getRouteConfig(routeName);
  if (route?.meta?.parentRoute) {
    return getRouteConfig(route.meta.parentRoute);
  }
  return undefined;
};

/**
 * 获取路由的子路由
 */
export const getChildRoutes = (routeName: string): RouteConfig[] => {
  return allRoutes.filter(route => route.meta?.parentRoute === routeName);
};

/**
 * 默认导出所有路由配置
 */
export default allRoutes;
