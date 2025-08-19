/**
 * 通用工具函数库
 *
 * 这个文件包含了应用中常用的工具函数，提供：
 *
 * 功能分类：
 * 1. 平台检测 - 检测iOS/Android平台
 * 2. 屏幕尺寸 - 获取设备屏幕信息
 * 3. 数据验证 - 邮箱、密码、手机号等验证
 * 4. 日期处理 - 日期格式化和处理
 * 5. 性能优化 - 防抖、节流函数
 * 6. 数据处理 - 深拷贝、对象检查等
 * 7. 字符串处理 - 格式化、截断等
 * 8. 文件处理 - 文件大小格式化
 *
 * 设计原则：
 * - 纯函数设计，无副作用
 * - TypeScript类型安全
 * - 高性能实现
 * - 易于测试和维护
 */

import { Dimensions, Platform } from 'react-native';
import { VALIDATION_RULES } from './constants';

// ==================== 平台检测工具 ====================

/**
 * 获取屏幕尺寸信息
 *
 * @returns 包含宽度和高度的对象
 */
export const getScreenDimensions = () => {
  const { width, height } = Dimensions.get('window');
  return { width, height };
};

/**
 * 判断是否为iOS平台
 *
 * @returns 是否为iOS平台
 */
export const isIOS = Platform.OS === 'ios';

/**
 * 判断是否为Android平台
 *
 * @returns 是否为Android平台
 */
export const isAndroid = Platform.OS === 'android';

// ==================== 数据验证工具 ====================

/**
 * 邮箱地址验证
 *
 * @param email - 要验证的邮箱地址
 * @returns 是否为有效的邮箱格式
 */
export const validateEmail = (email: string): boolean => {
  return VALIDATION_RULES.EMAIL_REGEX.test(email);
};

/**
 * 密码强度验证
 *
 * @param password - 要验证的密码
 * @returns 是否满足最小长度要求
 */
export const validatePassword = (password: string): boolean => {
  return password.length >= VALIDATION_RULES.PASSWORD_MIN_LENGTH;
};

/**
 * 用户名验证
 *
 * @param username - 要验证的用户名
 * @returns 是否满足长度要求
 */
export const validateUsername = (username: string): boolean => {
  return (
    username.length >= VALIDATION_RULES.USERNAME_MIN_LENGTH &&
    username.length <= VALIDATION_RULES.USERNAME_MAX_LENGTH
  );
};

/**
 * 手机号码验证
 *
 * @param phone - 要验证的手机号码
 * @returns 是否为有效的手机号格式
 */
export const validatePhone = (phone: string): boolean => {
  return VALIDATION_RULES.PHONE_REGEX.test(phone);
};

// ==================== 日期处理工具 ====================

/**
 * 格式化日期为指定格式的字符串
 *
 * @param date - 要格式化的日期对象或日期字符串
 * @param format - 日期格式字符串，支持YYYY、MM、DD、HH、mm、ss
 * @returns 格式化后的日期字符串
 *
 * 使用示例：
 * formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss') // "2024-01-15 14:30:25"
 */
export const formatDate = (date: Date | string, format = 'YYYY-MM-DD'): string => {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
};

// ==================== 性能优化工具 ====================

/**
 * 延迟执行函数
 *
 * @param ms - 延迟的毫秒数
 * @returns Promise对象，在指定时间后resolve
 *
 * 使用示例：
 * await delay(1000); // 延迟1秒
 */
export const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * 防抖函数 - 在事件被触发n秒后再执行回调，如果在这n秒内又被触发，则重新计时
 *
 * @param func - 要防抖的函数
 * @param wait - 等待时间（毫秒）
 * @returns 防抖后的函数
 *
 * 使用场景：搜索框输入、按钮点击防重复等
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * 节流函数 - 规定在一个单位时间内，只能触发一次函数
 *
 * @param func - 要节流的函数
 * @param limit - 时间间隔（毫秒）
 * @returns 节流后的函数
 *
 * 使用场景：滚动事件、窗口resize事件等高频触发的事件
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

// ==================== 字符串处理工具 ====================

/**
 * 生成指定长度的随机字符串
 *
 * @param length - 字符串长度
 * @returns 随机字符串
 *
 * 使用场景：生成临时ID、验证码等
 */
export const generateRandomString = (length: number): string => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
};

// ==================== 数据处理工具 ====================

/**
 * 深拷贝对象 - 创建对象的完全独立副本
 *
 * @param obj - 要拷贝的对象
 * @returns 深拷贝后的对象
 *
 * 功能：
 * - 支持基本类型、Date对象、数组、普通对象
 * - 递归处理嵌套结构
 * - 避免引用共享问题
 */
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as unknown as T;
  }

  if (obj instanceof Array) {
    return obj.map(item => deepClone(item)) as unknown as T;
  }

  if (typeof obj === 'object') {
    const clonedObj = {} as T;
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }

  return obj;
};

// ==================== 文件处理工具 ====================

/**
 * 格式化文件大小为可读的字符串
 *
 * @param bytes - 文件大小（字节）
 * @returns 格式化后的文件大小字符串
 *
 * 使用示例：
 * formatFileSize(1024) // "1 KB"
 * formatFileSize(1048576) // "1 MB"
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 检查对象是否为空
 *
 * @param obj - 要检查的对象
 * @returns 是否为空
 *
 * 功能：
 * - 支持null、undefined检查
 * - 支持数组、字符串长度检查
 * - 支持对象属性数量检查
 */
export const isEmpty = (obj: any): boolean => {
  if (obj == null) return true;
  if (Array.isArray(obj) || typeof obj === 'string') return obj.length === 0;
  if (typeof obj === 'object') return Object.keys(obj).length === 0;
  return false;
};

/**
 * 首字母大写转换
 *
 * @param str - 要转换的字符串
 * @returns 首字母大写的字符串
 */
export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

/**
 * 截断文本并添加省略号
 *
 * @param text - 要截断的文本
 * @param maxLength - 最大长度
 * @returns 截断后的文本
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};
