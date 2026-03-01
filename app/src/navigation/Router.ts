/**
 * 路由管理器
 * 
 * 这是导航系统的核心组件，负责：
 * 1. 路由注册和管理
 * 2. 导航操作执行
 * 3. 导航状态维护
 * 4. 导航守卫执行
 * 5. 导航事件分发
 */

import { 
  RouteName, 
  RouteConfig, 
  RouteParams,
  NavigationState, 
  NavigationOptions,
  NavigationActions,
  NavigationGuard,
  NavigationEventListener,
  NavigationEventData,
  NavigationEventType,
  NavigationHistoryItem,
  TransitionType
} from './types';

/**
 * 路由管理器类
 */
export class Router implements NavigationActions {
  private routes: Map<RouteName, RouteConfig> = new Map();
  private guards: NavigationGuard[] = [];
  private listeners: Map<NavigationEventType, NavigationEventListener[]> = new Map();
  private state: NavigationState = {
    currentRoute: 'Home',
    currentParams: undefined,
    history: [],
    canGoBack: false,
    canGoForward: false,
    isLoading: false,
  };
  private historyIndex: number = -1;

  // ==================== 路由注册管理 ====================

  /**
   * 注册单个路由
   */
  registerRoute(config: RouteConfig): void {
    this.routes.set(config.name, config);
  }

  /**
   * 批量注册路由
   */
  registerRoutes(configs: RouteConfig[]): void {
    configs.forEach(config => this.registerRoute(config));
  }

  /**
   * 获取路由配置
   */
  getRoute(name: RouteName): RouteConfig | undefined {
    return this.routes.get(name);
  }

  /**
   * 获取所有路由
   */
  getAllRoutes(): RouteConfig[] {
    return Array.from(this.routes.values());
  }

  // ==================== 导航守卫管理 ====================

  /**
   * 添加导航守卫
   */
  addGuard(guard: NavigationGuard): void {
    this.guards.push(guard);
  }

  /**
   * 移除导航守卫
   */
  removeGuard(guard: NavigationGuard): void {
    const index = this.guards.indexOf(guard);
    if (index > -1) {
      this.guards.splice(index, 1);
    }
  }

  /**
   * 执行导航守卫
   */
  private async executeGuards(from: RouteName, to: RouteName, params?: any): Promise<boolean> {
    for (const guard of this.guards) {
      try {
        const result = await guard({ from, to, params });
        
        if (typeof result === 'boolean') {
          if (!result) return false;
        } else if (typeof result === 'string') {
          // 重定向到指定路由
          await this.navigate(result as RouteName);
          return false;
        } else if (typeof result === 'object') {
          if (!result.allow) {
            if (result.redirect) {
              await this.navigate(result.redirect);
            }
            if (result.message) {
              this.emitEvent('navigationError', to, params, new Error(result.message));
            }
            return false;
          }
        }
      } catch (error) {
        this.emitEvent('navigationError', to, params, error as Error);
        return false;
      }
    }
    return true;
  }

  // ==================== 状态管理 ====================

  /**
   * 获取当前导航状态
   */
  getState(): NavigationState {
    return { ...this.state };
  }

  /**
   * 更新导航状态
   */
  private updateState(updates: Partial<NavigationState>): void {
    this.state = { ...this.state, ...updates };
    this.updateNavigationFlags();
  }

  /**
   * 更新导航标志
   */
  private updateNavigationFlags(): void {
    this.state.canGoBack = this.historyIndex > 0;
    this.state.canGoForward = this.historyIndex < this.state.history.length - 1;
  }

  /**
   * 添加历史记录
   */
  private addToHistory(route: RouteName, params?: any, title?: string): void {
    const historyItem: NavigationHistoryItem = {
      route,
      params,
      timestamp: Date.now(),
      title: title || this.getRoute(route)?.title || route,
    };

    // 如果当前不在历史记录的末尾，删除后面的记录
    if (this.historyIndex < this.state.history.length - 1) {
      this.state.history = this.state.history.slice(0, this.historyIndex + 1);
    }

    this.state.history.push(historyItem);
    this.historyIndex = this.state.history.length - 1;
  }

  // ==================== 事件系统 ====================

  /**
   * 添加事件监听器
   */
  addEventListener(type: NavigationEventType, listener: NavigationEventListener): void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type)!.push(listener);
  }

  /**
   * 移除事件监听器
   */
  removeEventListener(type: NavigationEventType, listener: NavigationEventListener): void {
    const listeners = this.listeners.get(type);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * 发送事件
   */
  private emitEvent(
    type: NavigationEventType, 
    route: RouteName, 
    params?: any, 
    error?: Error
  ): void {
    const eventData: NavigationEventData = {
      type,
      route,
      params,
      error,
      timestamp: Date.now(),
    };

    const listeners = this.listeners.get(type);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(eventData);
        } catch (err) {
          console.error('Navigation event listener error:', err);
        }
      });
    }
  }

  // ==================== 导航操作实现 ====================

  /**
   * 导航到指定路由
   */
  async navigate<T extends RouteName>(
    route: T, 
    params?: RouteParams<T>, 
    options: NavigationOptions = {}
  ): Promise<void> {
    try {
      this.updateState({ isLoading: true });
      this.emitEvent('beforeNavigate', route, params);

      // 检查路由是否存在
      const routeConfig = this.getRoute(route);
      if (!routeConfig) {
        throw new Error(`Route "${route}" not found`);
      }

      // 执行导航守卫
      const guardsPassed = await this.executeGuards(this.state.currentRoute, route, params);
      if (!guardsPassed) {
        this.updateState({ isLoading: false });
        return;
      }

      // 更新状态
      const previousRoute = this.state.currentRoute;
      this.updateState({
        currentRoute: route,
        currentParams: params,
        isLoading: false,
      });

      // 添加到历史记录（除非是替换操作）
      if (!options.replace) {
        this.addToHistory(route, params, routeConfig.title);
      }

      // 如果是清空历史记录
      if (options.clearHistory) {
        this.state.history = [];
        this.historyIndex = -1;
        this.addToHistory(route, params, routeConfig.title);
      }

      this.emitEvent('afterNavigate', route, params);
      this.emitEvent('routeChange', route, params);

    } catch (error) {
      this.updateState({ isLoading: false });
      this.emitEvent('navigationError', route, params, error as Error);
      throw error;
    }
  }

  /**
   * 返回上一页
   */
  async goBack(): Promise<void> {
    if (!this.state.canGoBack) {
      throw new Error('Cannot go back');
    }

    this.historyIndex--;
    const historyItem = this.state.history[this.historyIndex];
    
    this.updateState({
      currentRoute: historyItem.route,
      currentParams: historyItem.params,
    });

    this.emitEvent('routeChange', historyItem.route, historyItem.params);
  }

  /**
   * 前进到下一页
   */
  async goForward(): Promise<void> {
    if (!this.state.canGoForward) {
      throw new Error('Cannot go forward');
    }

    this.historyIndex++;
    const historyItem = this.state.history[this.historyIndex];
    
    this.updateState({
      currentRoute: historyItem.route,
      currentParams: historyItem.params,
    });

    this.emitEvent('routeChange', historyItem.route, historyItem.params);
  }

  /**
   * 推入新页面到栈顶
   */
  async push<T extends RouteName>(route: T, params?: RouteParams<T>): Promise<void> {
    await this.navigate(route, params);
  }

  /**
   * 弹出页面
   */
  async pop(count: number = 1): Promise<void> {
    for (let i = 0; i < count && this.state.canGoBack; i++) {
      await this.goBack();
    }
  }

  /**
   * 弹出到栈顶
   */
  async popToTop(): Promise<void> {
    if (this.state.history.length > 0) {
      const firstItem = this.state.history[0];
      await this.navigate(firstItem.route, firstItem.params, { clearHistory: true });
    }
  }

  /**
   * 替换当前页面
   */
  async replace<T extends RouteName>(route: T, params?: RouteParams<T>): Promise<void> {
    await this.navigate(route, params, { replace: true });
  }

  /**
   * 重置导航栈
   */
  async reset<T extends RouteName>(route: T, params?: RouteParams<T>): Promise<void> {
    await this.navigate(route, params, { clearHistory: true });
  }
}

// 创建全局路由实例
export const router = new Router();

export default router;
