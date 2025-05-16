/**
 * Layout.tsx
 *
 * 描述：网站布局组件，提供统一的页面结构和主题支持
 *
 * 功能：
 * - 提供统一的页面布局结构
 * - 包含网站头部和页脚组件
 * - 提供主题上下文支持
 * - 包装页面内容
 *
 * 主要组件/接口：
 * - Layout：布局组件
 * - LayoutProps：组件属性接口
 *
 * 导出：
 * - Layout 组件（默认导出）
 */

import React, { ReactNode } from 'react';
import Header from './Header';
import Footer from './Footer';
import styles from '@/styles/Layout.module.css';
import { ThemeProvider } from '@/contexts/ThemeContext';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <ThemeProvider>
      <div className={styles.layoutWrapper}>
        <Header />
        <main className={styles.mainContainer}>
          {children}
        </main>
        <Footer />
      </div>
    </ThemeProvider>
  );
};

export default Layout;
