/**
 * 导航上下文
 * 
 * 提供React组件访问导航功能的上下文，包括：
 * 1. 导航操作方法
 * 2. 当前路由状态
 * 3. 导航历史信息
 * 4. 路由配置访问
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { router } from './Router';
import { 
  NavigationState, 
  NavigationActions, 
  RouteName, 
  RouteConfig,
  NavigationEventData 
} from './types';

/**
 * 导航上下文类型定义
 */
interface NavigationContextType extends NavigationActions {
  // 导航状态
  state: NavigationState;
  
  // 路由配置
  getRoute: (name: RouteName) => RouteConfig | undefined;
  getAllRoutes: () => RouteConfig[];
  
  // 状态查询
  isCurrentRoute: (route: RouteName) => boolean;
  getCurrentRoute: () => RouteName;
  getCurrentParams: () => any;
  
  // 历史管理
  getHistory: () => NavigationState['history'];
  canGoBack: () => boolean;
  canGoForward: () => boolean;
}

/**
 * 创建导航上下文
 */
const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

/**
 * 导航提供者组件属性
 */
interface NavigationProviderProps {
  children: ReactNode;
  initialRoute?: RouteName;
}

/**
 * 导航提供者组件
 * 
 * 为整个应用提供导航功能的上下文
 */
export const NavigationProvider: React.FC<NavigationProviderProps> = ({ 
  children, 
  initialRoute = 'Home' 
}) => {
  // 导航状态
  const [navigationState, setNavigationState] = useState<NavigationState>(router.getState());

  // 监听导航状态变化
  useEffect(() => {
    const handleNavigationChange = (eventData: NavigationEventData) => {
      // 更新本地状态以触发组件重新渲染
      setNavigationState(router.getState());
    };

    // 添加事件监听器
    router.addEventListener('routeChange', handleNavigationChange);
    router.addEventListener('afterNavigate', handleNavigationChange);

    // 设置初始路由
    if (router.getState().currentRoute !== initialRoute) {
      router.navigate(initialRoute).catch(console.error);
    }

    // 清理函数
    return () => {
      router.removeEventListener('routeChange', handleNavigationChange);
      router.removeEventListener('afterNavigate', handleNavigationChange);
    };
  }, [initialRoute]);

  // 构建上下文值
  const contextValue: NavigationContextType = {
    // 导航状态
    state: navigationState,

    // 导航操作方法（直接代理到router）
    navigate: router.navigate.bind(router),
    goBack: router.goBack.bind(router),
    goForward: router.goForward.bind(router),
    push: router.push.bind(router),
    pop: router.pop.bind(router),
    popToTop: router.popToTop.bind(router),
    replace: router.replace.bind(router),
    reset: router.reset.bind(router),

    // 路由配置访问
    getRoute: router.getRoute.bind(router),
    getAllRoutes: router.getAllRoutes.bind(router),

    // 状态查询方法
    isCurrentRoute: (route: RouteName) => navigationState.currentRoute === route,
    getCurrentRoute: () => navigationState.currentRoute,
    getCurrentParams: () => navigationState.currentParams,

    // 历史管理
    getHistory: () => navigationState.history,
    canGoBack: () => navigationState.canGoBack,
    canGoForward: () => navigationState.canGoForward,
  };

  return (
    <NavigationContext.Provider value={contextValue}>
      {children}
    </NavigationContext.Provider>
  );
};

/**
 * 使用导航上下文的Hook
 * 
 * @returns 导航上下文对象
 * @throws 如果在NavigationProvider外部使用会抛出错误
 */
export const useNavigationContext = (): NavigationContextType => {
  const context = useContext(NavigationContext);
  
  if (context === undefined) {
    throw new Error('useNavigationContext must be used within a NavigationProvider');
  }
  
  return context;
};

/**
 * 导航Hook - 提供导航操作方法
 * 
 * @returns 导航操作对象
 */
export const useNavigation = (): NavigationActions => {
  const context = useNavigationContext();
  
  return {
    navigate: context.navigate,
    goBack: context.goBack,
    goForward: context.goForward,
    push: context.push,
    pop: context.pop,
    popToTop: context.popToTop,
    replace: context.replace,
    reset: context.reset,
  };
};

/**
 * 路由Hook - 提供当前路由信息
 * 
 * @returns 当前路由信息
 */
export const useRoute = () => {
  const context = useNavigationContext();
  
  return {
    name: context.getCurrentRoute(),
    params: context.getCurrentParams(),
    config: context.getRoute(context.getCurrentRoute()),
  };
};

/**
 * 导航状态Hook - 提供导航状态信息
 * 
 * @returns 导航状态对象
 */
export const useNavigationState = () => {
  const context = useNavigationContext();
  
  return {
    state: context.state,
    isCurrentRoute: context.isCurrentRoute,
    canGoBack: context.canGoBack(),
    canGoForward: context.canGoForward(),
    history: context.getHistory(),
  };
};

/**
 * 路由参数Hook - 获取当前路由的参数
 * 
 * @returns 当前路由参数
 */
export const useParams = <T = any>(): T => {
  const context = useNavigationContext();
  return context.getCurrentParams() as T;
};

/**
 * 路由守卫Hook - 用于组件级别的路由守卫
 * 
 * @param guard 守卫函数
 * @param deps 依赖数组
 */
export const useNavigationGuard = (
  guard: (route: RouteName, params?: any) => boolean | Promise<boolean>,
  deps: any[] = []
) => {
  const context = useNavigationContext();
  
  useEffect(() => {
    const navigationGuard = async ({ to, params }: any) => {
      try {
        const result = await guard(to, params);
        return result;
      } catch (error) {
        console.error('Navigation guard error:', error);
        return false;
      }
    };

    router.addGuard(navigationGuard);

    return () => {
      router.removeGuard(navigationGuard);
    };
  }, deps);
};

export default NavigationContext;
