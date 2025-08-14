/**
 * 主题管理Context
 *
 * 这个文件提供了全局的主题管理功能，包括：
 * 1. 主题状态管理（明亮/暗黑主题）
 * 2. 主题切换功能
 * 3. 主题设置的持久化存储
 * 4. 主题相关的工具函数
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { lightTheme, darkTheme, Theme, ThemeMode } from '../styles/theme'; // 主题配置
import AsyncStorage from '@react-native-async-storage/async-storage'; // 本地存储

/**
 * 主题Context的类型定义
 * 定义了主题管理系统对外提供的所有功能
 */
interface ThemeContextType {
  theme: Theme;                              // 当前主题对象（包含所有颜色、间距等配置）
  themeMode: ThemeMode;                      // 当前主题模式（'light' | 'dark'）
  toggleTheme: () => void;                   // 切换主题的函数
  setThemeMode: (mode: ThemeMode) => void;   // 设置特定主题模式的函数
  isDark: boolean;                           // 是否为暗黑主题的布尔值
}

// 创建主题Context，初始值为undefined
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * ThemeProvider组件的Props类型定义
 */
interface ThemeProviderProps {
  children: ReactNode; // 子组件
}

// 本地存储中保存主题设置的键名
const THEME_STORAGE_KEY = '@app_theme_mode';

/**
 * 主题Provider组件
 *
 * 功能：
 * 1. 管理全局主题状态
 * 2. 提供主题切换功能
 * 3. 处理主题设置的持久化存储
 * 4. 在应用启动时恢复用户的主题偏好
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // 当前主题模式状态，默认为浅色主题
  const [themeMode, setThemeModeState] = useState<ThemeMode>('light');
  // 加载状态，用于在恢复主题设置时显示加载状态
  const [isLoading, setIsLoading] = useState(true);

  // 组件挂载时从本地存储加载主题设置
  useEffect(() => {
    loadThemeFromStorage();
  }, []);

  /**
   * 从本地存储加载主题设置
   *
   * 功能：
   * 1. 从AsyncStorage读取用户之前保存的主题偏好
   * 2. 验证读取的值是否有效
   * 3. 应用有效的主题设置
   * 4. 处理加载错误和完成状态
   */
  const loadThemeFromStorage = async () => {
    try {
      // 从本地存储读取主题设置
      const savedTheme = await AsyncStorage.getItem(THEME_STORAGE_KEY);

      // 验证读取的值是否为有效的主题模式
      if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
        setThemeModeState(savedTheme);
      }
    } catch (error) {
      // 加载失败时输出警告，但不影响应用运行
      console.warn('Failed to load theme from storage:', error);
    } finally {
      // 无论成功或失败都要结束加载状态
      setIsLoading(false);
    }
  };

  /**
   * 保存主题设置到本地存储
   *
   * @param mode - 要保存的主题模式
   */
  const saveThemeToStorage = async (mode: ThemeMode) => {
    try {
      // 将主题模式保存到AsyncStorage
      await AsyncStorage.setItem(THEME_STORAGE_KEY, mode);
    } catch (error) {
      // 保存失败时输出警告
      console.warn('Failed to save theme to storage:', error);
    }
  };

  /**
   * 设置主题模式
   *
   * @param mode - 要设置的主题模式
   *
   * 功能：
   * 1. 更新当前主题状态
   * 2. 将新的主题设置保存到本地存储
   */
  const setThemeMode = (mode: ThemeMode) => {
    setThemeModeState(mode);      // 更新状态
    saveThemeToStorage(mode);     // 持久化保存
  };

  /**
   * 切换主题模式
   *
   * 功能：在浅色和暗黑主题之间切换
   */
  const toggleTheme = () => {
    const newMode = themeMode === 'light' ? 'dark' : 'light';
    setThemeMode(newMode);
  };

  // 根据当前主题模式选择对应的主题配置
  const theme = themeMode === 'light' ? lightTheme : darkTheme;
  // 计算是否为暗黑主题的布尔值
  const isDark = themeMode === 'dark';

  // 构建Context的值对象，包含所有主题相关的状态和方法
  const value: ThemeContextType = {
    theme,          // 当前主题配置对象
    themeMode,      // 当前主题模式字符串
    toggleTheme,    // 切换主题的函数
    setThemeMode,   // 设置特定主题的函数
    isDark,         // 是否为暗黑主题的布尔值
  };

  // 在加载主题设置时显示加载状态
  // 这样可以避免在恢复主题设置之前显示错误的主题
  if (isLoading) {
    return null; // 可以返回一个加载组件来提升用户体验
  }

  // 提供Context值给所有子组件
  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

/**
 * 主题Hook
 *
 * 这是一个自定义Hook，用于在组件中访问主题相关的状态和方法
 *
 * 使用方式：
 * ```tsx
 * const { theme, isDark, toggleTheme } = useTheme();
 * ```
 *
 * @returns ThemeContextType - 包含主题状态和方法的对象
 * @throws Error - 如果在ThemeProvider外部使用会抛出错误
 */
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);

  // 检查是否在ThemeProvider内部使用
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
};

export default ThemeContext;
