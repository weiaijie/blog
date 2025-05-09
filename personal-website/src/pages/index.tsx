import Head from 'next/head';
import Layout from '@/components/layout/Layout';
import MainContent from '@/components/layout/MainContent';

export default function Home() {
  return (
    <>
      <Head>
        <title>saber的个人网站</title>
        <meta name="description" content="全栈开发 | 用代码构建美好数字世界" />
      </Head>
      <Layout>
        <MainContent />
      </Layout>
    </>
  );
}
