/**
 * SEOHead.tsx
 *
 * 描述：SEO优化组件，统一管理页面的meta标签、Open Graph和Twitter Card
 *
 * 功能：
 * - 提供统一的SEO meta标签管理
 * - 支持Open Graph和Twitter Card
 * - 支持结构化数据（JSON-LD）
 * - 自动生成canonical URL
 * - 支持多语言meta标签
 *
 * 主要接口：
 * - SEOHeadProps：SEO配置属性接口
 * - SEOHead：SEO头部组件
 */

import Head from 'next/head';
import { useRouter } from 'next/router';
import siteConfig from '@/config/site';

interface SEOHeadProps {
  title?: string;
  description?: string;
  keywords?: string[];
  image?: string;
  type?: 'website' | 'article' | 'profile';
  publishedTime?: string;
  modifiedTime?: string;
  author?: string;
  section?: string;
  tags?: string[];
  noindex?: boolean;
  canonical?: string;
  structuredData?: object;
}

export default function SEOHead({
  title,
  description,
  keywords = [],
  image,
  type = 'website',
  publishedTime,
  modifiedTime,
  author,
  section,
  tags = [],
  noindex = false,
  canonical,
  structuredData
}: SEOHeadProps) {
  const router = useRouter();
  
  // 构建完整的页面标题
  const fullTitle = title 
    ? `${title} - ${siteConfig.title}`
    : siteConfig.title;
  
  // 使用默认描述如果没有提供
  const metaDescription = description || siteConfig.description;
  
  // 构建完整的URL
  const baseUrl = process.env.NODE_ENV === 'production' 
    ? 'https://weiaijie.com' // 替换为实际域名
    : 'http://localhost:3000';
  
  const currentUrl = canonical || `${baseUrl}${router.asPath}`;
  
  // 构建图片URL
  const imageUrl = image
    ? (image.startsWith('http') ? image : `${baseUrl}${image}`)
    : `${baseUrl}/images/og-default.svg`; // 默认OG图片
  
  // 构建关键词字符串
  const keywordsString = keywords.length > 0 
    ? keywords.join(', ')
    : '全栈开发,React,Next.js,Vue.js,Node.js,前端开发,后端开发';
  
  // 默认结构化数据
  const defaultStructuredData = {
    "@context": "https://schema.org",
    "@type": type === 'profile' ? "Person" : "WebPage",
    "name": type === 'profile' ? siteConfig.author : fullTitle,
    "description": metaDescription,
    "url": currentUrl,
    ...(type === 'profile' && {
      "jobTitle": "全栈开发工程师",
      "worksFor": {
        "@type": "Organization",
        "name": "自由职业"
      },
      "sameAs": [
        siteConfig.social.github.url,
        siteConfig.social.linkedin.url
      ]
    })
  };
  
  const finalStructuredData = structuredData || defaultStructuredData;

  return (
    <Head>
      {/* 基本meta标签 */}
      <title>{fullTitle}</title>
      <meta name="description" content={metaDescription} />
      <meta name="keywords" content={keywordsString} />
      <meta name="author" content={author || siteConfig.author} />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="robots" content={noindex ? 'noindex,nofollow' : 'index,follow'} />
      <link rel="canonical" href={currentUrl} />
      
      {/* Open Graph标签 */}
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={metaDescription} />
      <meta property="og:type" content={type} />
      <meta property="og:url" content={currentUrl} />
      <meta property="og:image" content={imageUrl} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:site_name" content={siteConfig.title} />
      <meta property="og:locale" content="zh_CN" />
      
      {/* 文章特定的Open Graph标签 */}
      {type === 'article' && (
        <>
          {publishedTime && <meta property="article:published_time" content={publishedTime} />}
          {modifiedTime && <meta property="article:modified_time" content={modifiedTime} />}
          {author && <meta property="article:author" content={author} />}
          {section && <meta property="article:section" content={section} />}
          {tags.map((tag, index) => (
            <meta key={index} property="article:tag" content={tag} />
          ))}
        </>
      )}
      
      {/* Twitter Card标签 */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={metaDescription} />
      <meta name="twitter:image" content={imageUrl} />
      <meta name="twitter:creator" content="@weiaijie" />
      <meta name="twitter:site" content="@weiaijie" />
      
      {/* 结构化数据 */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(finalStructuredData)
        }}
      />
      
      {/* 其他meta标签 */}
      <meta name="theme-color" content="#0071e3" />
      <meta name="msapplication-TileColor" content="#0071e3" />
      <meta name="apple-mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-status-bar-style" content="default" />
      <meta name="format-detection" content="telephone=no" />
    </Head>
  );
}
