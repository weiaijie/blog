import Head from 'next/head';
import Header from '@/components/layout/Header';

export default function Home() {
  return (
    <>
      <Head>
        <title>魏爱杰的个人网站</title>
        <meta name="description" content="全栈开发工程师 | 专注于创建优雅高效的数字体验" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Header />
      <main>
        {/* 这里将添加主要内容 */}
      </main>
    </>
  );
}
