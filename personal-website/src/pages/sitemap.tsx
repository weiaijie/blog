/**
 * sitemap.tsx
 *
 * 描述：网站地图页面，提供网站所有页面的链接导航
 *
 * 功能：
 * - 展示网站的所有页面链接
 * - 按类别组织页面链接
 * - 提供清晰的导航结构
 *
 * 主要组件：
 * - Sitemap：网站地图页面的主要组件
 */

import Head from 'next/head';
import Link from 'next/link';
import Layout from '@/components/layout/Layout';
import { getAllRoutes } from '@/config/routes';
import siteConfig from '@/config/site';
import styles from '@/styles/Sitemap.module.css';

export default function Sitemap() {
  // 获取所有路由
  const allRoutes = getAllRoutes();

  // 按类别组织路由
  const mainPages = allRoutes.filter(route =>
    ['/'].includes(route.path) ||
    route.path.split('/').length === 2 &&
    !route.path.includes('privacy') &&
    !route.path.includes('terms') &&
    !route.path.includes('sitemap')
  );

  const legalPages = allRoutes.filter(route =>
    route.path.includes('privacy') ||
    route.path.includes('terms') ||
    route.path.includes('sitemap')
  );

  return (
    <>
      <Head>
        <title>网站地图 - {siteConfig.title}</title>
        <meta name="description" content="浏览网站的所有页面和内容" />
        <meta name="robots" content="noindex" />
      </Head>
      <Layout>
        <div className={styles.sitemapPage}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>网站地图</h1>

            <div className={styles.sitemapContent}>
              <section className={styles.section}>
                <h2>主要页面</h2>
                <ul className={styles.linkList}>
                  {mainPages.map((route) => (
                    <li key={route.path} className={styles.linkItem}>
                      <Link href={route.path} className={styles.link}>
                        {route.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>

              <section className={styles.section}>
                <h2>法律页面</h2>
                <ul className={styles.linkList}>
                  {legalPages.map((route) => (
                    <li key={route.path} className={styles.linkItem}>
                      <Link href={route.path} className={styles.link}>
                        {route.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
