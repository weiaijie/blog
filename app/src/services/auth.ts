// 认证服务
import apiClient from './api';
import { LoginRequest, LoginResponse, RegisterRequest, User } from '@/types';

// 认证相关API接口
export const authService = {
  // 用户登录
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
    return response.data;
  },

  // 用户注册
  register: async (userData: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>('/auth/register', userData);
    return response.data;
  },

  // 获取当前用户信息
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  // 刷新token
  refreshToken: async (refreshToken: string): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/refresh', {
      refreshToken,
    });
    return response.data;
  },

  // 用户登出
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },

  // 忘记密码
  forgotPassword: async (email: string): Promise<void> => {
    await apiClient.post('/auth/forgot-password', { email });
  },

  // 重置密码
  resetPassword: async (token: string, newPassword: string): Promise<void> => {
    await apiClient.post('/auth/reset-password', {
      token,
      password: newPassword,
    });
  },

  // 修改密码
  changePassword: async (oldPassword: string, newPassword: string): Promise<void> => {
    await apiClient.post('/auth/change-password', {
      oldPassword,
      newPassword,
    });
  },
};

export default authService;
