// API相关类型定义

// 用户相关类型
export interface User {
  id: string;
  email: string;
  username: string;
  firstName?: string;
  lastName?: string;
  avatar?: string;
  phone?: string;
  createdAt: string;
  updatedAt: string;
}

// 登录请求类型
export interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

// 登录响应类型
export interface LoginResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// 注册请求类型
export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
}

// API响应基础类型
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  errors?: string[];
}

// 分页响应类型
export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

// API错误类型
export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

// 文件上传类型
export interface FileUpload {
  uri: string;
  type: string;
  name: string;
  size?: number;
}

// 上传响应类型
export interface UploadResponse {
  url: string;
  filename: string;
  size: number;
  mimeType: string;
}
