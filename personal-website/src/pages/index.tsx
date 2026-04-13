/**
 * index.tsx
 *
 * 描述：个人网站首页，展示个人介绍、精选项目和最新博客文章
 */

import Head from 'next/head';
import Layout from '@/components/layout/Layout';
import MainContent from '@/components/layout/MainContent';
import Tagline from '@/components/sections/Tagline';

export default function Home() {
  return (
    <>
      <Head>
        <title>许辉 - 全栈开发工程师</title>
        <meta name="description" content="拥有8年经验的全栈开发工程师，专注于构建直观、高效且美观的产品体验。" />
      </Head>
      <Layout>
        <Tagline visible={true} />
        <MainContent visible={true} />
      </Layout>
    </>
  );
}
