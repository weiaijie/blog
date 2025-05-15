import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// 定义主题类型
export type Theme = 'light' | 'dark';

// 定义主题上下文的类型
interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

// 创建主题上下文
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// 主题提供者组件的属性类型
interface ThemeProviderProps {
  children: ReactNode;
}

// 主题提供者组件
export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // 状态用于跟踪当前主题
  // 尝试从 localStorage 读取初始主题，如果不存在则使用 'light'
  const [theme, setTheme] = useState<Theme>(() => {
    // 确保代码在客户端运行
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('theme') as Theme | null;
      if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
        return savedTheme;
      }

      // 如果没有保存的主题，检查系统偏好
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
    }

    return 'light';
  });

  // 在组件挂载时，监听系统主题变化
  useEffect(() => {
    // 只在客户端运行
    if (typeof window === 'undefined') return;

    // 监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      // 只有当用户没有明确设置主题偏好时，才跟随系统主题
      if (!localStorage.getItem('theme')) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    };

    // 使用正确的 API 添加事件监听器
    try {
      // 现代浏览器
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } catch (e) {
      // 旧版浏览器兼容
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, []);

  // 当主题变化时，更新 document 的 data-theme 属性和 localStorage
  useEffect(() => {
    // 只在客户端运行
    if (typeof window === 'undefined') return;

    // 更新 document 的 data-theme 属性
    document.documentElement.setAttribute('data-theme', theme);

    // 保存主题到 localStorage
    try {
      localStorage.setItem('theme', theme);
    } catch (e) {
      console.error('Failed to save theme preference:', e);
    }
  }, [theme]);

  // 切换主题的函数
  const toggleTheme = () => {
    setTheme(prevTheme => (prevTheme === 'light' ? 'dark' : 'light'));

    // 在控制台输出当前主题，方便调试
    if (typeof window !== 'undefined') {
      console.log('Theme toggled to:', theme === 'light' ? 'dark' : 'light');
    }
  };

  // 提供主题上下文值
  const contextValue: ThemeContextType = {
    theme,
    toggleTheme,
    setTheme,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// 自定义钩子，用于在组件中访问主题上下文
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
