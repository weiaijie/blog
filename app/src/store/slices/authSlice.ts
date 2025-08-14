/**
 * 认证状态管理切片
 *
 * 这个文件提供了用户认证相关的状态管理功能，包括：
 *
 * 主要功能：
 * 1. 用户登录状态管理 - 跟踪用户是否已登录
 * 2. 用户信息存储 - 保存当前登录用户的详细信息
 * 3. 认证令牌管理 - 管理API访问令牌
 * 4. 加载状态管理 - 跟踪认证操作的进行状态
 * 5. 错误处理 - 处理认证过程中的错误信息
 *
 * 技术实现：
 * - 使用React Hooks实现简化的状态管理
 * - 不依赖Redux Toolkit，便于学习理解
 * - 提供完整的TypeScript类型定义
 * - 模拟真实的认证流程和API调用
 *
 * 注意：这是一个学习用的简化版本
 * 在生产环境中建议使用Redux Toolkit或其他成熟的状态管理方案
 */

import { useState, useCallback } from 'react';

/**
 * 用户信息类型定义
 * 定义了用户对象的完整结构
 */
export interface User {
  id: string;           // 用户唯一标识符
  email: string;        // 用户邮箱地址
  username: string;     // 用户名
  firstName?: string;   // 名字（可选）
  lastName?: string;    // 姓氏（可选）
  avatar?: string;      // 头像URL（可选）
}

/**
 * 认证状态类型定义
 * 定义了认证系统的完整状态结构
 */
export interface AuthState {
  isAuthenticated: boolean;  // 是否已认证
  user: User | null;         // 当前用户信息（未登录时为null）
  token: string | null;      // 认证令牌（未登录时为null）
  loading: boolean;          // 是否正在进行认证操作
  error: string | null;      // 错误信息（无错误时为null）
}

// 初始状态
const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  loading: false,
  error: null,
};

// 模拟用户数据
const mockUser: User = {
  id: '1',
  email: 'learner@example.com',
  username: 'learner',
  firstName: '学习',
  lastName: '者',
  avatar: '👤',
};

// 自定义Hook用于认证状态管理
export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>(initialState);

  // 登录
  const login = useCallback(async (email: string, password: string) => {
    setAuthState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 简单的验证逻辑
      if (email === 'learner@example.com' && password === '123456') {
        const token = 'mock-jwt-token-' + Date.now();
        
        setAuthState({
          isAuthenticated: true,
          user: mockUser,
          token,
          loading: false,
          error: null,
        });
        
        return { success: true, user: mockUser, token };
      } else {
        throw new Error('邮箱或密码错误');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '登录失败';
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      return { success: false, error: errorMessage };
    }
  }, []);

  // 注册
  const register = useCallback(async (userData: {
    email: string;
    username: string;
    password: string;
    firstName?: string;
    lastName?: string;
  }) => {
    setAuthState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const newUser: User = {
        id: Date.now().toString(),
        email: userData.email,
        username: userData.username,
        firstName: userData.firstName,
        lastName: userData.lastName,
        avatar: '👤',
      };
      
      const token = 'mock-jwt-token-' + Date.now();
      
      setAuthState({
        isAuthenticated: true,
        user: newUser,
        token,
        loading: false,
        error: null,
      });
      
      return { success: true, user: newUser, token };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '注册失败';
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      return { success: false, error: errorMessage };
    }
  }, []);

  // 登出
  const logout = useCallback(async () => {
    setAuthState(prev => ({ ...prev, loading: true }));
    
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setAuthState(initialState);
      return { success: true };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '登出失败';
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      return { success: false, error: errorMessage };
    }
  }, []);

  // 更新用户信息
  const updateUser = useCallback(async (userData: Partial<User>) => {
    if (!authState.user) return { success: false, error: '用户未登录' };
    
    setAuthState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800));
      
      const updatedUser = { ...authState.user, ...userData };
      
      setAuthState(prev => ({
        ...prev,
        user: updatedUser,
        loading: false,
        error: null,
      }));
      
      return { success: true, user: updatedUser };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '更新失败';
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      return { success: false, error: errorMessage };
    }
  }, [authState.user]);

  // 清除错误
  const clearError = useCallback(() => {
    setAuthState(prev => ({ ...prev, error: null }));
  }, []);

  // 检查认证状态
  const checkAuth = useCallback(async () => {
    setAuthState(prev => ({ ...prev, loading: true }));
    
    try {
      // 模拟检查本地存储的token
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // 这里可以检查本地存储的token是否有效
      const hasValidToken = false; // 模拟没有有效token
      
      if (hasValidToken) {
        setAuthState({
          isAuthenticated: true,
          user: mockUser,
          token: 'existing-token',
          loading: false,
          error: null,
        });
      } else {
        setAuthState(prev => ({ ...prev, loading: false }));
      }
    } catch (error) {
      setAuthState(prev => ({ ...prev, loading: false }));
    }
  }, []);

  return {
    // 状态
    ...authState,
    
    // 操作
    login,
    register,
    logout,
    updateUser,
    clearError,
    checkAuth,
  };
};

export default useAuth;
