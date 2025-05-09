import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '@/components/layout/Layout';
import MainContent from '@/components/layout/MainContent';
import Tagline from '@/components/sections/Tagline';

export default function Home() {
  // 控制标语和主内容的显示
  const [showTagline, setShowTagline] = useState(true);
  const [showMainContent, setShowMainContent] = useState(false);

  useEffect(() => {
    // 页面加载时，先显示标语，延迟显示主内容
    const mainContentTimer = setTimeout(() => {
      setShowMainContent(true);
    }, 800); // 延迟800ms显示主内容

    const handleScroll = () => {
      // 根据设备宽度调整滚动阈值
      const threshold = window.innerWidth <= 768 ? window.innerHeight * 0.7 : 300;

      // 当页面向下滚动超过阈值时隐藏标语
      if (window.scrollY > threshold) {
        setShowTagline(false);
      } else {
        setShowTagline(true);
      }
    };

    // 添加滚动事件监听
    window.addEventListener('scroll', handleScroll);

    // 清理函数
    return () => {
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(mainContentTimer);
    };
  }, []);

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
