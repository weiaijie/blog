/**
 * ThemeToggle.tsx
 *
 * 描述：主题切换按钮组件，用于切换网站的亮色/暗色主题模式
 *
 * 功能：
 * - 提供直观的主题切换按钮
 * - 根据当前主题显示对应的图标（太阳/月亮）
 * - 支持动画效果
 * - 处理服务器端渲染和客户端渲染的差异
 * - 提供无障碍支持（aria标签）
 *
 * 主要组件/接口：
 * - ThemeToggle：主题切换按钮组件
 * - ThemeToggleProps：组件属性接口
 *
 * 导出：
 * - ThemeToggle 组件（默认导出）
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '@/contexts/ThemeContext';
import styles from '@/styles/ThemeToggle.module.css';

interface ThemeToggleProps {
  className?: string;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ className = '' }) => {
  const { theme, toggleTheme } = useTheme();
  // 添加客户端渲染状态
  const [mounted, setMounted] = useState(false);

  // 在客户端挂载后设置状态
  useEffect(() => {
    setMounted(true);
  }, []);

  // 确定是否为暗色模式
  const isDark = theme === 'dark';

  // 渲染太阳图标
  const renderSunIcon = () => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={styles.icon}
    >
      <circle cx="12" cy="12" r="5"></circle>
      <line x1="12" y1="1" x2="12" y2="3"></line>
      <line x1="12" y1="21" x2="12" y2="23"></line>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
      <line x1="1" y1="12" x2="3" y2="12"></line>
      <line x1="21" y1="12" x2="23" y2="12"></line>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
    </svg>
  );

  // 渲染月亮图标
  const renderMoonIcon = () => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={styles.icon}
    >
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
    </svg>
  );

  // 在服务器端渲染时，始终使用默认值
  const ariaLabel = !mounted ? '切换主题' : (isDark ? '切换到亮色模式' : '切换到暗色模式');

  return (
    <motion.button
      className={`${styles.themeToggle} ${className}`}
      onClick={toggleTheme}
      aria-label={ariaLabel}
      whileTap={{ scale: 0.95 }}
      title={ariaLabel}
    >
      <div className={styles.toggleTrack}>
        <div className={`${styles.toggleThumb} ${mounted && isDark ? styles.dark : ''}`}>
          {/* 只在客户端渲染时显示正确的图标，服务器端始终渲染太阳图标 */}
          {!mounted || !isDark ? renderSunIcon() : renderMoonIcon()}
        </div>
      </div>
    </motion.button>
  );
};

export default ThemeToggle;
