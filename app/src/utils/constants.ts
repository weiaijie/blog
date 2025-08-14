// 应用常量定义

// 应用信息
export const APP_INFO = {
  NAME: 'RN学习测试应用',
  VERSION: '1.0.0',
  BUILD_NUMBER: '1',
  BUNDLE_ID: 'com.rnlearning.app',
} as const;

// 存储键名
export const STORAGE_KEYS = {
  AUTH_TOKEN: '@auth_token',
  REFRESH_TOKEN: '@refresh_token',
  USER_INFO: '@user_info',
  THEME: '@theme',
  LANGUAGE: '@language',
  FIRST_LAUNCH: '@first_launch',
  BIOMETRIC_ENABLED: '@biometric_enabled',
} as const;

// API相关常量
export const API_CONSTANTS = {
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const;

// 验证规则
export const VALIDATION_RULES = {
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PASSWORD_MIN_LENGTH: 8,
  USERNAME_MIN_LENGTH: 3,
  USERNAME_MAX_LENGTH: 20,
  PHONE_REGEX: /^1[3-9]\d{9}$/,
} as const;

// 错误消息
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络连接失败，请检查网络设置',
  TIMEOUT_ERROR: '请求超时，请稍后重试',
  UNKNOWN_ERROR: '未知错误，请稍后重试',
  INVALID_EMAIL: '请输入有效的邮箱地址',
  INVALID_PASSWORD: '密码长度至少8位',
  INVALID_USERNAME: '用户名长度应在3-20位之间',
  INVALID_PHONE: '请输入有效的手机号码',
  PASSWORD_MISMATCH: '两次输入的密码不一致',
  LOGIN_FAILED: '登录失败，请检查用户名和密码',
  REGISTER_FAILED: '注册失败，请稍后重试',
} as const;

// 成功消息
export const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: '登录成功',
  REGISTER_SUCCESS: '注册成功',
  LOGOUT_SUCCESS: '退出成功',
  PASSWORD_CHANGED: '密码修改成功',
  PROFILE_UPDATED: '个人信息更新成功',
  EMAIL_SENT: '邮件发送成功',
} as const;

// 主题相关常量
export const THEME_MODES = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system',
} as const;

// 语言相关常量
export const LANGUAGES = {
  ZH_CN: 'zh-CN',
  EN_US: 'en-US',
} as const;

// 动画持续时间
export const ANIMATION_DURATION = {
  SHORT: 200,
  MEDIUM: 300,
  LONG: 500,
} as const;

// 屏幕尺寸断点
export const BREAKPOINTS = {
  SMALL: 320,
  MEDIUM: 768,
  LARGE: 1024,
} as const;

// 默认配置
export const DEFAULT_CONFIG = {
  THEME: THEME_MODES.SYSTEM,
  LANGUAGE: LANGUAGES.ZH_CN,
  BIOMETRIC_ENABLED: false,
  NOTIFICATIONS_ENABLED: true,
} as const;
