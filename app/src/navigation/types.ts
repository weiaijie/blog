/**
 * 导航系统类型定义
 * 
 * 这个文件定义了导航系统中使用的所有TypeScript类型，包括：
 * 1. 路由配置类型
 * 2. 导航状态类型  
 * 3. 页面参数类型
 * 4. 导航操作类型
 * 5. 导航守卫类型
 */

import { ComponentType } from 'react';

// ==================== 基础类型定义 ====================

/**
 * 路由名称类型
 * 定义应用中所有可用的路由名称
 */
export type RouteName = 
  | 'Home'           // 首页
  | 'Todo'           // 待办事项
  | 'Profile'        // 个人中心
  | 'Settings'       // 设置页面
  | 'Login'          // 登录页面
  | 'Register'       // 注册页面
  | 'TodoDetail'     // 待办详情页面
  | 'UserProfile'    // 用户资料页面
  | 'About'          // 关于页面
  | 'Help';          // 帮助页面

/**
 * 导航器类型
 * 定义不同类型的导航器
 */
export type NavigatorType = 
  | 'tab'            // Tab导航器
  | 'stack'          // 栈导航器
  | 'drawer'         // 抽屉导航器
  | 'modal';         // 模态导航器

/**
 * 页面转场动画类型
 */
export type TransitionType = 
  | 'slide'          // 滑动
  | 'fade'           // 淡入淡出
  | 'scale'          // 缩放
  | 'flip'           // 翻转
  | 'none';          // 无动画

// ==================== 路由参数类型 ====================

/**
 * 路由参数映射
 * 定义每个路由可以接收的参数类型
 */
export type RouteParamList = {
  Home: undefined;                           // 首页无参数
  Todo: undefined;                           // 待办列表无参数
  Profile: undefined;                        // 个人中心无参数
  Settings: undefined;                       // 设置页面无参数
  Login: { returnTo?: RouteName };           // 登录页面可接收返回地址
  Register: { email?: string };              // 注册页面可接收预填邮箱
  TodoDetail: { todoId: string };            // 待办详情需要待办ID
  UserProfile: { userId: string };           // 用户资料需要用户ID
  About: undefined;                          // 关于页面无参数
  Help: { section?: string };                // 帮助页面可接收章节参数
};

/**
 * 路由参数提取工具类型
 */
export type RouteParams<T extends RouteName> = RouteParamList[T];

// ==================== 路由配置类型 ====================

/**
 * 单个路由配置
 */
export interface RouteConfig<T extends RouteName = RouteName> {
  name: T;                                   // 路由名称
  component: ComponentType<any>;             // 页面组件
  title?: string;                            // 页面标题
  icon?: string;                             // 图标（用于Tab导航）
  headerShown?: boolean;                     // 是否显示头部
  tabBarVisible?: boolean;                   // 是否在Tab栏中显示
  gestureEnabled?: boolean;                  // 是否启用手势
  transition?: TransitionType;               // 转场动画类型
  requireAuth?: boolean;                     // 是否需要登录
  roles?: string[];                          // 需要的用户角色
  meta?: Record<string, any>;                // 额外的元数据
}

/**
 * 导航器配置
 */
export interface NavigatorConfig {
  type: NavigatorType;                       // 导航器类型
  routes: RouteConfig[];                     // 路由配置列表
  initialRoute?: RouteName;                  // 初始路由
  screenOptions?: ScreenOptions;             // 全局屏幕选项
}

/**
 * 屏幕选项配置
 */
export interface ScreenOptions {
  headerShown?: boolean;                     // 是否显示头部
  headerTitle?: string;                      // 头部标题
  headerBackTitle?: string;                  // 返回按钮标题
  gestureEnabled?: boolean;                  // 是否启用手势
  animationEnabled?: boolean;                // 是否启用动画
  transition?: TransitionType;               // 转场动画
}

// ==================== 导航状态类型 ====================

/**
 * 导航历史记录项
 */
export interface NavigationHistoryItem {
  route: RouteName;                          // 路由名称
  params?: any;                              // 路由参数
  timestamp: number;                         // 访问时间戳
  title?: string;                            // 页面标题
}

/**
 * 导航状态
 */
export interface NavigationState {
  currentRoute: RouteName;                   // 当前路由
  currentParams?: any;                       // 当前路由参数
  history: NavigationHistoryItem[];          // 导航历史
  canGoBack: boolean;                        // 是否可以返回
  canGoForward: boolean;                     // 是否可以前进
  isLoading: boolean;                        // 是否正在导航
}

// ==================== 导航操作类型 ====================

/**
 * 导航选项
 */
export interface NavigationOptions {
  replace?: boolean;                         // 是否替换当前页面
  clearHistory?: boolean;                    // 是否清空历史记录
  animated?: boolean;                        // 是否使用动画
  transition?: TransitionType;               // 指定转场动画
}

/**
 * 导航操作接口
 */
export interface NavigationActions {
  // 基础导航
  navigate<T extends RouteName>(
    route: T, 
    params?: RouteParams<T>, 
    options?: NavigationOptions
  ): Promise<void>;
  
  // 返回操作
  goBack(): Promise<void>;
  goForward(): Promise<void>;
  
  // 栈操作
  push<T extends RouteName>(
    route: T, 
    params?: RouteParams<T>
  ): Promise<void>;
  
  pop(count?: number): Promise<void>;
  popToTop(): Promise<void>;
  
  // 替换操作
  replace<T extends RouteName>(
    route: T, 
    params?: RouteParams<T>
  ): Promise<void>;
  
  // 重置操作
  reset<T extends RouteName>(
    route: T, 
    params?: RouteParams<T>
  ): Promise<void>;
}

// ==================== 导航守卫类型 ====================

/**
 * 导航守卫上下文
 */
export interface NavigationGuardContext {
  from: RouteName;                           // 来源路由
  to: RouteName;                             // 目标路由
  params?: any;                              // 路由参数
  user?: any;                                // 当前用户信息
}

/**
 * 导航守卫结果
 */
export type NavigationGuardResult = 
  | boolean                                  // 简单的允许/拒绝
  | RouteName                                // 重定向到指定路由
  | { 
      allow: boolean; 
      redirect?: RouteName; 
      message?: string; 
    };

/**
 * 导航守卫函数类型
 */
export type NavigationGuard = (
  context: NavigationGuardContext
) => NavigationGuardResult | Promise<NavigationGuardResult>;

// ==================== 导航事件类型 ====================

/**
 * 导航事件类型
 */
export type NavigationEventType = 
  | 'beforeNavigate'                         // 导航前
  | 'afterNavigate'                          // 导航后
  | 'navigationError'                        // 导航错误
  | 'routeChange';                           // 路由变化

/**
 * 导航事件数据
 */
export interface NavigationEventData {
  type: NavigationEventType;
  route: RouteName;
  params?: any;
  error?: Error;
  timestamp: number;
}

/**
 * 导航事件监听器
 */
export type NavigationEventListener = (data: NavigationEventData) => void;

// ==================== 导出类型 ====================

export default {
  RouteName,
  NavigatorType,
  TransitionType,
  RouteParamList,
  RouteParams,
  RouteConfig,
  NavigatorConfig,
  ScreenOptions,
  NavigationHistoryItem,
  NavigationState,
  NavigationOptions,
  NavigationActions,
  NavigationGuardContext,
  NavigationGuardResult,
  NavigationGuard,
  NavigationEventType,
  NavigationEventData,
  NavigationEventListener,
};
