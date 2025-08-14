/**
 * LatestPosts.tsx
 *
 * 描述：首页的最新博客文章部分，展示最新的博客文章
 *
 * 功能：
 * - 展示最新的博客文章
 * - 显示文章标题、摘要、日期和图标
 * - 提供文章链接跳转到详细页面
 * - 提供"阅读更多"按钮链接到博客列表页面
 *
 * 主要组件/接口：
 * - LatestPosts：最新博客文章组件
 * - BlogPost：博客文章数据接口
 *
 * 导出：
 * - LatestPosts 组件（默认导出）
 */

import React from 'react';
import Link from 'next/link';
import styles from '@/styles/LatestPosts.module.css';

interface BlogPost {
  id: string;
  title: string;
  date: string;
  excerpt: string;
  icon: React.ReactNode;
}

const LatestPosts: React.FC = () => {
  // 示例博客文章数据
  const posts: BlogPost[] = [
    {
      id: 'post-1',
      title: '如何构建高性能React应用',
      date: '2023-05-15',
      excerpt: '探讨React性能优化的关键策略，包括组件拆分、状态管理和渲染优化',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <circle cx="12" cy="12" r="4"></circle>
          <line x1="4.93" y1="4.93" x2="9.17" y2="9.17"></line>
          <line x1="14.83" y1="14.83" x2="19.07" y2="19.07"></line>
          <line x1="14.83" y1="9.17" x2="19.07" y2="4.93"></line>
          <line x1="14.83" y1="9.17" x2="18.36" y2="5.64"></line>
          <line x1="4.93" y1="19.07" x2="9.17" y2="14.83"></line>
        </svg>
      )
    },
    {
      id: 'post-2',
      title: 'TypeScript高级类型技巧',
      date: '2023-04-28',
      excerpt: '深入探讨TypeScript的高级类型系统，帮助你编写更安全、更可维护的代码',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="4 17 10 11 4 5"></polyline>
          <line x1="12" y1="19" x2="20" y2="19"></line>
        </svg>
      )
    },
    {
      id: 'post-3',
      title: '现代CSS布局技术详解',
      date: '2023-04-10',
      excerpt: '探索Flexbox和Grid布局的强大功能，以及如何创建复杂而灵活的页面布局',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="3" y1="9" x2="21" y2="9"></line>
          <line x1="9" y1="21" x2="9" y2="9"></line>
        </svg>
      )
    },
    {
      id: 'post-4',
      title: 'Node.js微服务架构实践',
      date: '2023-03-22',
      excerpt: '从单体应用迁移到微服务架构的实用指南，包括服务拆分和通信策略',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 10h-4v4h4v-4z"></path>
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
          <path d="M8 21h8"></path>
          <path d="M12 17v4"></path>
        </svg>
      )
    }
  ];

  return (
    <section id="blog" className={styles.latestPosts}>
      <h2 className={styles.sectionTitle}>最新博客文章</h2>
      <div className={styles.postsGrid}>
        {posts.map((post) => (
          <Link href={`/blog/${post.id}`} key={post.id} className={styles.postCard}>
            <div className={styles.postIcon}>{post.icon}</div>
            <div className={styles.postContent}>
              <h3 className={styles.postTitle}>{post.title}</h3>
              <p className={styles.postExcerpt}>{post.excerpt}</p>
              <div className={styles.postMeta}>
                <span className={styles.postDate}>{post.date}</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
      <div className={styles.viewAllContainer}>
        <Link href="/blog" className={styles.viewAllButton}>
          阅读更多
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.buttonIcon}>
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </Link>
      </div>
    </section>
  );
};

export default LatestPosts;
