/**
 * sitemap.xml.tsx
 *
 * 描述：生成网站sitemap.xml文件，用于SEO优化
 *
 * 功能：
 * - 自动生成网站所有页面的sitemap
 * - 包含静态页面和动态页面（博客文章、项目详情等）
 * - 设置页面优先级和更新频率
 * - 支持多语言sitemap
 *
 * 主要功能：
 * - getServerSideProps：服务端生成sitemap内容
 * - 返回XML格式的sitemap
 */

import { GetServerSideProps } from 'next';

// 静态页面配置
const staticPages = [
  {
    url: '',
    changefreq: 'weekly',
    priority: '1.0',
    lastmod: new Date().toISOString()
  },
  {
    url: '/about',
    changefreq: 'monthly',
    priority: '0.8',
    lastmod: new Date().toISOString()
  },
  {
    url: '/skills',
    changefreq: 'monthly',
    priority: '0.7',
    lastmod: new Date().toISOString()
  },
  {
    url: '/projects',
    changefreq: 'weekly',
    priority: '0.9',
    lastmod: new Date().toISOString()
  },
  {
    url: '/blog',
    changefreq: 'daily',
    priority: '0.9',
    lastmod: new Date().toISOString()
  },
  {
    url: '/contact',
    changefreq: 'monthly',
    priority: '0.6',
    lastmod: new Date().toISOString()
  }
];

// 博客文章数据（在实际应用中应该从数据库或API获取）
const blogPosts = [
  {
    id: 'post-1',
    lastmod: '2023-05-15',
    priority: '0.8'
  },
  {
    id: 'post-2',
    lastmod: '2023-04-28',
    priority: '0.8'
  },
  {
    id: 'post-3',
    lastmod: '2023-04-10',
    priority: '0.8'
  },
  {
    id: 'post-4',
    lastmod: '2023-03-22',
    priority: '0.8'
  },
  {
    id: 'post-5',
    lastmod: '2023-02-15',
    priority: '0.8'
  },
  {
    id: 'post-6',
    lastmod: '2023-01-30',
    priority: '0.8'
  }
];

// 项目数据（从配置文件获取）
const projects = [
  'maoju-platform',
  'qingsong-sync',
  'medical-website',
  'personal-website'
];

function generateSiteMap(baseUrl: string) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${staticPages
    .map(({ url, changefreq, priority, lastmod }) => {
      return `
    <url>
      <loc>${baseUrl}${url}</loc>
      <lastmod>${lastmod}</lastmod>
      <changefreq>${changefreq}</changefreq>
      <priority>${priority}</priority>
    </url>
  `;
    })
    .join('')}
  ${blogPosts
    .map(({ id, lastmod, priority }) => {
      return `
    <url>
      <loc>${baseUrl}/blog/${id}</loc>
      <lastmod>${lastmod}</lastmod>
      <changefreq>monthly</changefreq>
      <priority>${priority}</priority>
    </url>
  `;
    })
    .join('')}
  ${projects
    .map((projectId) => {
      return `
    <url>
      <loc>${baseUrl}/projects/${projectId}</loc>
      <lastmod>${new Date().toISOString()}</lastmod>
      <changefreq>monthly</changefreq>
      <priority>0.7</priority>
    </url>
  `;
    })
    .join('')}
</urlset>
`;
}

function SiteMap() {
  // getServerSideProps会处理这个页面，所以这个组件不会被渲染
  return null;
}

export const getServerSideProps: GetServerSideProps = async ({ res, req }) => {
  // 获取基础URL
  const protocol = req.headers['x-forwarded-proto'] || 'http';
  const host = req.headers.host;
  const baseUrl = process.env.NODE_ENV === 'production' 
    ? 'https://weiaijie.com' // 替换为实际域名
    : `${protocol}://${host}`;

  // 生成sitemap
  const sitemap = generateSiteMap(baseUrl);

  res.setHeader('Content-Type', 'text/xml');
  // 设置缓存头
  res.setHeader('Cache-Control', 'public, s-maxage=86400, stale-while-revalidate');
  res.write(sitemap);
  res.end();

  return {
    props: {},
  };
};

export default SiteMap;
