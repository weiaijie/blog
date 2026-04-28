/**
 * index.tsx
 *
 * 描述：个人网站首页，展示个人介绍、精选项目和项目记录
 */

import Layout from '@/components/layout/Layout';
import MainContent from '@/components/layout/MainContent';
import Tagline from '@/components/sections/Tagline';
import SeoHead from '@/components/common/SeoHead';

export default function Home() {
  return (
    <>
      <SeoHead
        title="许辉 - 全栈开发工程师"
        description="许辉的个人网站，整理做过的后台、小程序、官网和系统对接项目。"
        path="/"
      />
      <Layout>
        <Tagline visible={true} />
        <MainContent visible={true} />
      </Layout>
    </>
  );
}
