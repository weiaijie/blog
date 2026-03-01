/**
 * 认证守卫
 * 
 * 这个守卫用于保护需要登录才能访问的页面，提供：
 * 1. 登录状态检查
 * 2. 自动重定向到登录页
 * 3. 登录后返回原页面
 * 4. 角色权限验证
 */

import { NavigationGuard, NavigationGuardContext, NavigationGuardResult } from '../types';

/**
 * 认证守卫配置
 */
interface AuthGuardConfig {
  loginRoute?: string;           // 登录页面路由名称
  redirectAfterLogin?: boolean;  // 登录后是否重定向回原页面
  requiredRoles?: string[];      // 需要的用户角色
}

/**
 * 创建认证守卫
 * 
 * @param config 守卫配置
 * @param getUserInfo 获取用户信息的函数
 * @returns 认证守卫函数
 */
export const createAuthGuard = (
  config: AuthGuardConfig = {},
  getUserInfo: () => { isAuthenticated: boolean; user?: any; roles?: string[] } | null
): NavigationGuard => {
  const {
    loginRoute = 'Login',
    redirectAfterLogin = true,
    requiredRoles = [],
  } = config;

  return async (context: NavigationGuardContext): Promise<NavigationGuardResult> => {
    try {
      // 获取当前用户信息
      const userInfo = getUserInfo();
      
      // 检查是否需要认证
      const targetRoute = context.to;
      
      // 如果目标是登录页面，直接允许
      if (targetRoute === loginRoute) {
        return true;
      }

      // 检查路由是否需要认证（这里可以从路由配置中获取）
      // 暂时硬编码一些需要认证的页面
      const authRequiredRoutes = ['Profile', 'UserProfile', 'Settings'];
      const requiresAuth = authRequiredRoutes.includes(targetRoute);

      if (!requiresAuth) {
        return true; // 不需要认证的页面直接允许访问
      }

      // 检查用户是否已登录
      if (!userInfo || !userInfo.isAuthenticated) {
        return {
          allow: false,
          redirect: loginRoute as any,
          message: '请先登录',
        };
      }

      // 检查角色权限
      if (requiredRoles.length > 0) {
        const userRoles = userInfo.roles || [];
        const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));
        
        if (!hasRequiredRole) {
          return {
            allow: false,
            message: '权限不足',
          };
        }
      }

      // 所有检查通过，允许访问
      return true;

    } catch (error) {
      console.error('Auth guard error:', error);
      return {
        allow: false,
        redirect: loginRoute as any,
        message: '认证检查失败',
      };
    }
  };
};

/**
 * 默认认证守卫
 * 使用默认配置的认证守卫
 */
export const defaultAuthGuard = createAuthGuard();

/**
 * 管理员权限守卫
 * 需要管理员角色的守卫
 */
export const adminGuard = createAuthGuard(
  {
    requiredRoles: ['admin'],
  },
  () => {
    // 这里应该从实际的认证系统获取用户信息
    // 暂时返回模拟数据
    return {
      isAuthenticated: false,
      user: null,
      roles: [],
    };
  }
);

/**
 * VIP用户守卫
 * 需要VIP权限的守卫
 */
export const vipGuard = createAuthGuard(
  {
    requiredRoles: ['vip', 'premium'],
  },
  () => {
    // 这里应该从实际的认证系统获取用户信息
    return {
      isAuthenticated: false,
      user: null,
      roles: [],
    };
  }
);

export default createAuthGuard;
