/**
 * index.tsx
 *
 * 描述：个人网站首页，展示个人介绍、技能亮点、精选项目和最新博客文章
 *
 * 功能：
 * - 展示网站标语(Tagline)和主要内容
 * - 实现滚动时标语的显示/隐藏效果
 * - 使用防抖和节流优化滚动事件处理
 * - 响应式设计，适配不同设备尺寸
 *
 * 主要组件：
 * - Home：主页组件，控制标语和主内容的显示逻辑
 * - Tagline：标语组件，展示在首屏
 * - MainContent：主要内容组件，包含个人介绍、技能、项目和博客文章
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import Head from 'next/head';
import Layout from '@/components/layout/Layout';
import MainContent from '@/components/layout/MainContent';
import Tagline from '@/components/sections/Tagline';

export default function Home() {
  // 控制标语和主内容的显示
  const [showTagline, setShowTagline] = useState(true);
  const [showMainContent, setShowMainContent] = useState(false);

  // 使用useRef存储上一次的滚动方向和防抖定时器
  const lastScrollY = useRef(0);
  const scrollTimer = useRef<NodeJS.Timeout | null>(null);
  const scrollThreshold = useRef(0);

  // 防抖函数
  const debounce = useCallback((fn: Function, delay: number) => {
    if (scrollTimer.current) clearTimeout(scrollTimer.current);
    scrollTimer.current = setTimeout(() => fn(), delay);
  }, []);

  // 单独处理主内容的显示，确保它只被设置一次
  useEffect(() => {
    // 页面加载时，延迟显示主内容
    const mainContentTimer = setTimeout(() => {
      setShowMainContent(true);
    }, 800); // 延迟800ms显示主内容

    return () => {
      clearTimeout(mainContentTimer);
    };
  }, []); // 空依赖数组，确保只运行一次

  // 处理标语的显示/隐藏 - 优化以避免页面跳动
  useEffect(() => {
    // 计算滚动阈值
    scrollThreshold.current = window.innerWidth <= 768 ? window.innerHeight * 0.7 : 300;

    // 添加一个小的缓冲区，防止在阈值附近滚动时频繁切换状态
    const buffer = 50; // 50px的缓冲区

    // 记录上一次的显示状态，避免不必要的状态更新
    let isCurrentlyVisible = true;

    // 优化的滚动处理函数
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      // 只有当滚动方向明确且超过缓冲区时才更新状态
      // 使用更长的防抖时间
      debounce(() => {
        // 添加缓冲区逻辑
        if (isCurrentlyVisible && currentScrollY > scrollThreshold.current + buffer) {
          // 只有当前显示且滚动超过阈值+缓冲区时才隐藏
          isCurrentlyVisible = false;
          setShowTagline(false);
        } else if (!isCurrentlyVisible && currentScrollY < scrollThreshold.current - buffer) {
          // 只有当前隐藏且滚动低于阈值-缓冲区时才显示
          isCurrentlyVisible = true;
          setShowTagline(true);
        }
        // 其他情况保持当前状态，避免频繁切换
      }, 150); // 增加防抖延迟到150ms，大幅减少状态更新频率

      // 更新上一次的滚动位置
      lastScrollY.current = currentScrollY;
    };

    // 添加滚动事件监听，使用throttle而不是每次滚动都触发
    let ticking = false;
    const throttledScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          handleScroll();
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', throttledScroll, { passive: true });

    // 添加窗口大小变化监听，更新阈值
    const handleResize = () => {
      scrollThreshold.current = window.innerWidth <= 768 ? window.innerHeight * 0.7 : 300;
    };
    window.addEventListener('resize', handleResize);

    // 清理函数
    return () => {
      window.removeEventListener('scroll', throttledScroll);
      window.removeEventListener('resize', handleResize);
      if (scrollTimer.current) clearTimeout(scrollTimer.current);
    };
  }, [debounce]);

  return (
    <>
      <Head>
        <title>saber的个人网站</title>
        <meta name="description" content="全栈开发 | 用代码构建美好数字世界" />
      </Head>
      <Layout>
        <Tagline visible={showTagline} />
        <MainContent visible={showMainContent} />
      </Layout>
    </>
  );
}
