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
        console.log('useEffect: Applied saved theme:', savedTheme);
      }
      // 否则，检查系统主题偏好
      else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
        console.log('useEffect: Applied system theme: dark');
      } else {
        console.log('useEffect: Using default theme: light');
      }
    } catch (err) {
      console.error('useEffect: Error applying theme:', err);
    }
  }, []);

  return (
    <>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap" rel="stylesheet" />
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
                    console.log('Inline script: Applied saved theme:', savedTheme);
                  }
                  // 否则，检查系统主题偏好
                  else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    document.documentElement.setAttribute('data-theme', 'dark');
                    console.log('Inline script: Applied system theme: dark');
                  } else {
                    document.documentElement.setAttribute('data-theme', 'light');
                    console.log('Inline script: Using default theme: light');
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
        <style dangerouslySetInnerHTML={{ __html: `
          @font-face {
            font-family: 'SF Pro Display';
            src: url('https://applesocial.s3.amazonaws.com/assets/styles/fonts/sanfrancisco/sanfranciscodisplay-regular-webfont.woff2') format('woff2');
            font-weight: 400;
            font-style: normal;
          }
          @font-face {
            font-family: 'SF Pro Display';
            src: url('https://applesocial.s3.amazonaws.com/assets/styles/fonts/sanfrancisco/sanfranciscodisplay-medium-webfont.woff2') format('woff2');
            font-weight: 500;
            font-style: normal;
          }
          @font-face {
            font-family: 'SF Pro Display';
            src: url('https://applesocial.s3.amazonaws.com/assets/styles/fonts/sanfrancisco/sanfranciscodisplay-semibold-webfont.woff2') format('woff2');
            font-weight: 600;
            font-style: normal;
          }
          @font-face {
            font-family: 'SF Pro Text';
            src: url('https://applesocial.s3.amazonaws.com/assets/styles/fonts/sanfrancisco/sanfranciscotext-regular-webfont.woff2') format('woff2');
            font-weight: 400;
            font-style: normal;
          }
          @font-face {
            font-family: 'SF Pro Text';
            src: url('https://applesocial.s3.amazonaws.com/assets/styles/fonts/sanfrancisco/sanfranciscotext-medium-webfont.woff2') format('woff2');
            font-weight: 500;
            font-style: normal;
          }
        ` }} />
      </Head>
      <Component {...pageProps} />
    </>
  );
}
