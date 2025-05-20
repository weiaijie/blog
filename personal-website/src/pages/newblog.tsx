/**
 * newblog.tsx
 *
 * 描述：重新设计的博客页面，展示个人技术博客文章列表
 *
 * 功能：
 * - 展示不同类别的博客文章（技术教程、项目案例、行业趋势、经验分享）
 * - 提供文章分类筛选功能
 * - 提供文章搜索功能（标题、摘要和标签）
 * - 展示文章卡片，包括标题、摘要、日期、阅读时间和标签
 * - 使用苹果风格的设计，提供更好的视觉体验
 *
 * 主要组件：
 * - NewBlog：博客页面的主要组件
 * - 包含博客文章数据模型定义和筛选逻辑
 */

import Head from 'next/head';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import styles from '@/styles/NewBlog.module.css';

interface BlogPost {
  id: string;
  title: string;
  date: string;
  excerpt: string;
  category: string;
  tags: string[];
  readTime: string;
  image?: string;
}

// 获取默认封面图
const getDefaultCoverImage = (category: string): string => {
  // 使用简单的颜色背景作为默认封面
  switch (category) {
    case 'tutorial':
      return 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="338" viewBox="0 0 600 338"><rect width="600" height="338" fill="%23f0f7ff"/><text x="300" y="169" font-family="Arial" font-size="24" text-anchor="middle" fill="%230071e3">技术教程</text></svg>';
    case 'case-study':
      return 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="338" viewBox="0 0 600 338"><rect width="600" height="338" fill="%23f0fff7"/><text x="300" y="169" font-family="Arial" font-size="24" text-anchor="middle" fill="%2300a67e">项目案例</text></svg>';
    case 'trend':
      return 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="338" viewBox="0 0 600 338"><rect width="600" height="338" fill="%23fff7f0"/><text x="300" y="169" font-family="Arial" font-size="24" text-anchor="middle" fill="%23e36500">行业趋势</text></svg>';
    case 'experience':
      return 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="338" viewBox="0 0 600 338"><rect width="600" height="338" fill="%23f7f0ff"/><text x="300" y="169" font-family="Arial" font-size="24" text-anchor="middle" fill="%236500e3">经验分享</text></svg>';
    default:
      return 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="338" viewBox="0 0 600 338"><rect width="600" height="338" fill="%23f5f5f7"/><text x="300" y="169" font-family="Arial" font-size="24" text-anchor="middle" fill="%231d1d1f">博客文章</text></svg>';
  }
};

export default function NewBlog() {
  // 博客分类
  const categories = [
    { id: 'all', name: '全部' },
    { id: 'tutorial', name: '技术教程' },
    { id: 'case-study', name: '项目案例' },
    { id: 'trend', name: '行业趋势' },
    { id: 'experience', name: '经验分享' },
  ];

  // 示例博客文章数据
  const allPosts: BlogPost[] = [
    {
      id: 'post-1',
      title: '如何构建高性能React应用',
      date: '2023-05-15',
      excerpt: '探讨React性能优化的关键策略，包括组件拆分、状态管理和渲染优化',
      category: 'tutorial',
      tags: ['React', '性能优化', '前端开发'],
      readTime: '8分钟',
      image: '/placeholder-blog.jpg' // 有图片
    },
    {
      id: 'post-2',
      title: 'TypeScript高级类型技巧',
      date: '2023-04-28',
      excerpt: '深入探讨TypeScript的高级类型系统，帮助你编写更安全、更可维护的代码',
      category: 'tutorial',
      tags: ['TypeScript', '前端开发'],
      readTime: '10分钟'
      // 没有图片
    },
    {
      id: 'post-3',
      title: '现代CSS布局技术详解',
      date: '2023-04-10',
      excerpt: '探索Flexbox和Grid布局的强大功能，以及如何创建复杂而灵活的页面布局',
      category: 'tutorial',
      tags: ['CSS', '响应式设计', '前端开发'],
      readTime: '7分钟',
      image: '/placeholder-blog.jpg' // 有图片
    },
    {
      id: 'post-4',
      title: 'Node.js微服务架构实践',
      date: '2023-03-22',
      excerpt: '从单体应用迁移到微服务架构的实用指南，包括服务拆分和通信策略',
      category: 'case-study',
      tags: ['Node.js', '微服务', '后端开发'],
      readTime: '12分钟'
      // 没有图片
    },
    {
      id: 'post-5',
      title: '2023年前端开发趋势展望',
      date: '2023-02-15',
      excerpt: '分析当前前端技术生态的发展方向，以及未来一年可能出现的新技术和工具',
      category: 'trend',
      tags: ['前端开发', '技术趋势'],
      readTime: '6分钟',
      image: '/placeholder-blog.jpg' // 有图片
    },
    {
      id: 'post-6',
      title: '我的远程工作经验分享',
      date: '2023-01-30',
      excerpt: '作为一名远程开发者的工作体验、挑战和应对策略，以及提高效率的工具和方法',
      category: 'experience',
      tags: ['远程工作', '职业发展'],
      readTime: '9分钟'
      // 没有图片
    }
  ];

  // 状态管理
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoaded, setIsLoaded] = useState(false);

  // 页面加载动画
  useEffect(() => {
    setIsLoaded(true);
  }, []);

  // 根据分类和搜索筛选文章
  const filteredPosts = allPosts
    .filter(post => activeCategory === 'all' || post.category === activeCategory)
    .filter(post =>
      post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    );

  // 动画变体
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: [0.25, 0.1, 0.25, 1.0]
      }
    }
  };

  return (
    <>
      <Head>
        <title>博客 - saber的个人网站</title>
        <meta name="description" content="技术教程、项目案例分析、行业趋势和个人经验分享" />
      </Head>
      <Layout>
        <div className={styles.blogPage}>
          <motion.div
            className={styles.titleSection}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: isLoaded ? 1 : 0, y: isLoaded ? 0 : 20 }}
            transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1.0] }}
          >
            <h1 className={styles.pageTitle}>博客</h1>
            <p className={styles.pageDescription}>
              分享我在技术领域的探索、思考和经验，包括前端开发、后端技术、项目实践和行业趋势
            </p>
          </motion.div>

          <motion.div
            className={styles.controlsSection}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: isLoaded ? 1 : 0, y: isLoaded ? 0 : 20 }}
            transition={{ duration: 0.6, delay: 0.1, ease: [0.25, 0.1, 0.25, 1.0] }}
          >
            <div className={styles.searchBar}>
              <input
                type="text"
                placeholder="搜索文章..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={styles.searchInput}
              />
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.searchIcon}>
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            </div>

            <div className={styles.categoryFilter}>
              {categories.map(category => (
                <button
                  key={category.id}
                  className={`${styles.categoryButton} ${activeCategory === category.id ? styles.active : ''}`}
                  onClick={() => setActiveCategory(category.id)}
                >
                  {category.name}
                </button>
              ))}
            </div>
          </motion.div>

          <motion.div
            className={styles.postsContainer}
            variants={containerVariants}
            initial="hidden"
            animate={isLoaded ? "visible" : "hidden"}
          >
            {filteredPosts.length > 0 ? (
              filteredPosts.map(post => (
                <motion.div key={post.id} variants={itemVariants}>
                  <Link href={`/blog/${post.id}`} className={styles.postCard}>
                    <div className={styles.postImageContainer}>
                      <div className={styles.postImage}>
                        {post.image ? (
                          // 使用Next.js的Image组件处理真实图片
                          <Image
                            src={post.image.endsWith('.jpg') || post.image.endsWith('.png') ? post.image : '/placeholder-blog.svg'}
                            alt={post.title}
                            className={styles.defaultCover}
                            width={600}
                            height={338}
                            onError={(e) => {
                              // 图片加载失败时显示占位符
                              const target = e.target as HTMLImageElement;
                              target.style.display = 'none';

                              // 安全地访问parentElement
                              if (target.parentElement) {
                                target.parentElement.classList.add(styles.placeholder);
                                target.parentElement.innerHTML = `
                                  <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                                    <polyline points="21 15 16 10 5 21"></polyline>
                                  </svg>
                                `;
                              }
                            }}
                          />
                        ) : (
                          // 使用普通img标签处理SVG文件
                          <img
                            src={getDefaultCoverImage(post.category)}
                            alt={post.title}
                            className={styles.defaultCover}
                          />
                        )}
                      </div>
                      {/* 将分类标识移到图片容器中，确保它始终显示 */}
                      <span className={styles.categoryBadge}>
                        {categories.find(cat => cat.id === post.category)?.name || post.category}
                      </span>
                    </div>
                    <div className={styles.postContent}>
                      <div className={styles.postMeta}>
                        <span className={styles.postDate}>{post.date}</span>
                        <span className={styles.postReadTime}>{post.readTime}</span>
                      </div>
                      <h2 className={styles.postTitle}>{post.title}</h2>
                      <p className={styles.postExcerpt}>{post.excerpt}</p>
                      <div className={styles.postTags}>
                        {post.tags.map((tag, index) => (
                          <span className={styles.postTag} key={index}>{tag}</span>
                        ))}
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))
            ) : (
              <motion.div className={styles.noResults} variants={itemVariants}>
                <p>没有找到符合条件的文章</p>
              </motion.div>
            )}
          </motion.div>
        </div>
      </Layout>
    </>
  );
}
