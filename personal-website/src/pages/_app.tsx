/**
 * _app.tsx
 *
 * 描述：Next.js应用程序的入口文件，用于初始化页面和全局配置
 *
 * 功能：
 * - 初始化全局样式和字体
 * - 管理网站主题（亮色/暗色模式）
 * - 在页面加载前应用保存的主题偏好，避免闪烁
 * - 设置全局元数据和视口配置
 *
 * 主要组件：
 * - App：Next.js应用程序的主组件
 * - 包含主题初始化和全局配置逻辑
 */

import '@/styles/globals.css';
import '@/styles/prism-custom.css'; // 导入Prism.js代码高亮样式
import type { AppProps } from 'next/app';
import Head from 'next/head';
import { useEffect } from 'react';
import siteConfig from '@/config/site';

export default function App({ Component, pageProps }: AppProps) {
  // 在客户端初始化主题
  useEffect(() => {
    // 确保代码在客户端运行
    if (typeof window === 'undefined') return;

    try {
      // 尝试从 localStorage 读取主题偏好
      const savedTheme = localStorage.getItem('theme');

      // 如果有保存的主题偏好，则应用它
      if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
        document.documentElement.setAttribute('data-theme', savedTheme);
      } else {
        document.documentElement.setAttribute('data-theme', 'light');
      }
    } catch (err) {
      console.error('useEffect: Error applying theme:', err);
    }
  }, []);

  return (
    <>
      <Head>
        <title>{siteConfig.title}</title>
        <meta name="description" content={siteConfig.description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap"
          rel="stylesheet"
        />
        {/* 添加主题初始化脚本，避免闪烁 */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                // 确保代码在客户端运行
                if (typeof window === 'undefined') return;

                try {
                  // 尝试从 localStorage 读取主题偏好
                  var savedTheme = localStorage.getItem('theme');

                  // 如果有保存的主题偏好，则应用它
                  if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
                    document.documentElement.setAttribute('data-theme', savedTheme);
                  } else {
                    document.documentElement.setAttribute('data-theme', 'light');
                  }
                } catch (err) {
                  console.error('Inline script: Error applying theme:', err);
                  // 出错时使用默认主题
                  document.documentElement.setAttribute('data-theme', 'light');
                }
              })();
            `,
          }}
        />
      </Head>
      <Component {...pageProps} />
    </>
  );
}
