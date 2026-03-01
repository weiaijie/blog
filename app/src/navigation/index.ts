/**
 * 导航系统入口文件
 *
 * 导出所有导航相关的组件、类型和工具
 */

// 核心导航组件
export { default as AppNavigator } from './AppNavigator';
export { default as EnhancedAppNavigator } from './components/EnhancedAppNavigator';
export { default as TabNavigator } from './components/TabNavigator';
export { default as SimpleAppNavigator } from './components/SimpleAppNavigator';
export { default as WebAppNavigator } from './components/WebAppNavigator';
export { default as AuthNavigator } from './components/AuthNavigator';
export { default as MainAppNavigator } from './components/MainAppNavigator';

// 导航上下文和Hooks
export {
  NavigationProvider,
  useNavigation,
  useRoute,
  useNavigationState,
  useParams,
  useNavigationGuard,
} from './NavigationContext';

// 路由管理器
export { router, Router } from './Router';

// 类型定义
export * from './types';

// 路由配置
export * from './config/routes';

// 导航守卫
export * from './guards';
