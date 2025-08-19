/**
 * 主题状态管理切片
 * 管理应用的主题设置
 */

import { useState, useCallback, useEffect } from 'react';
import { useColorScheme } from 'react-native';

// 主题模式类型
export type ThemeMode = 'light' | 'dark' | 'system';

// 主题状态类型
export interface ThemeState {
  mode: ThemeMode;
  isDark: boolean;
  colors: {
    primary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    success: string;
    warning: string;
  };
}

// 浅色主题颜色
const lightColors = {
  primary: '#007AFF',
  background: '#FFFFFF',
  surface: '#FFFFFF',
  text: '#111827',
  textSecondary: '#6B7280',
  border: '#E5E7EB',
  error: '#EF4444',
  success: '#10B981',
  warning: '#F59E0B',
};

// 深色主题颜色
const darkColors = {
  primary: '#0A84FF',
  background: '#1F2937',
  surface: '#374151',
  text: '#FFFFFF',
  textSecondary: '#D1D5DB',
  border: '#4B5563',
  error: '#F87171',
  success: '#34D399',
  warning: '#FBBF24',
};

// 自定义Hook用于主题管理
export const useTheme = () => {
  const systemColorScheme = useColorScheme();
  const [themeMode, setThemeMode] = useState<ThemeMode>('system');

  // 计算当前是否为深色模式
  const isDark = themeMode === 'dark' || (themeMode === 'system' && systemColorScheme === 'dark');

  // 获取当前主题颜色
  const colors = isDark ? darkColors : lightColors;

  // 主题状态
  const themeState: ThemeState = {
    mode: themeMode,
    isDark,
    colors,
  };

  // 设置主题模式
  const setMode = useCallback((mode: ThemeMode) => {
    setThemeMode(mode);
    // 这里可以添加持久化存储逻辑
    // StorageUtil.setString('theme_mode', mode);
  }, []);

  // 切换主题
  const toggleTheme = useCallback(() => {
    if (themeMode === 'light') {
      setMode('dark');
    } else if (themeMode === 'dark') {
      setMode('system');
    } else {
      setMode('light');
    }
  }, [themeMode, setMode]);

  // 设置浅色主题
  const setLightTheme = useCallback(() => {
    setMode('light');
  }, [setMode]);

  // 设置深色主题
  const setDarkTheme = useCallback(() => {
    setMode('dark');
  }, [setMode]);

  // 设置系统主题
  const setSystemTheme = useCallback(() => {
    setMode('system');
  }, [setMode]);

  // 获取主题描述
  const getThemeDescription = useCallback(() => {
    switch (themeMode) {
      case 'light':
        return '浅色模式';
      case 'dark':
        return '深色模式';
      case 'system':
        return `跟随系统 (${systemColorScheme === 'dark' ? '深色' : '浅色'})`;
      default:
        return '未知模式';
    }
  }, [themeMode, systemColorScheme]);

  // 初始化时从存储加载主题设置
  useEffect(() => {
    const loadThemeFromStorage = async () => {
      try {
        // 这里可以从本地存储加载主题设置
        // const savedMode = await StorageUtil.getString('theme_mode');
        // if (savedMode && ['light', 'dark', 'system'].includes(savedMode)) {
        //   setThemeMode(savedMode as ThemeMode);
        // }
      } catch (error) {
        console.warn('Failed to load theme from storage:', error);
      }
    };

    loadThemeFromStorage();
  }, []);

  return {
    // 状态
    ...themeState,
    
    // 操作
    setMode,
    toggleTheme,
    setLightTheme,
    setDarkTheme,
    setSystemTheme,
    getThemeDescription,
  };
};

// 主题上下文相关的Hook
export const useThemeColors = () => {
  const { colors } = useTheme();
  return colors;
};

export const useIsDarkTheme = () => {
  const { isDark } = useTheme();
  return isDark;
};

export default useTheme;
