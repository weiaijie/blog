import Head from 'next/head';
import { useState } from 'react';
import Link from 'next/link';
import Layout from '@/components/layout/Layout';
import styles from '@/styles/Blog.module.css';

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

export default function Blog() {
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
      image: '/placeholder-blog.jpg'
    },
    {
      id: 'post-2',
      title: 'TypeScript高级类型技巧',
      date: '2023-04-28',
      excerpt: '深入探讨TypeScript的高级类型系统，帮助你编写更安全、更可维护的代码',
      category: 'tutorial',
      tags: ['TypeScript', '前端开发'],
      readTime: '10分钟',
      image: '/placeholder-blog.jpg'
    },
    {
      id: 'post-3',
      title: '现代CSS布局技术详解',
      date: '2023-04-10',
      excerpt: '探索Flexbox和Grid布局的强大功能，以及如何创建复杂而灵活的页面布局',
      category: 'tutorial',
      tags: ['CSS', '响应式设计', '前端开发'],
      readTime: '7分钟',
      image: '/placeholder-blog.jpg'
    },
    {
      id: 'post-4',
      title: 'Node.js微服务架构实践',
      date: '2023-03-22',
      excerpt: '从单体应用迁移到微服务架构的实用指南，包括服务拆分和通信策略',
      category: 'case-study',
      tags: ['Node.js', '微服务', '后端开发'],
      readTime: '12分钟',
      image: '/placeholder-blog.jpg'
    },
    {
      id: 'post-5',
      title: '2023年前端开发趋势展望',
      date: '2023-02-15',
      excerpt: '分析当前前端技术生态的发展方向，以及未来一年可能出现的新技术和工具',
      category: 'trend',
      tags: ['前端开发', '技术趋势'],
      readTime: '6分钟',
      image: '/placeholder-blog.jpg'
    },
    {
      id: 'post-6',
      title: '我的远程工作经验分享',
      date: '2023-01-30',
      excerpt: '作为一名远程开发者的工作体验、挑战和应对策略，以及提高效率的工具和方法',
      category: 'experience',
      tags: ['远程工作', '职业发展'],
      readTime: '9分钟',
      image: '/placeholder-blog.jpg'
    }
  ];

  // 状态管理
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // 根据分类和搜索筛选文章
  const filteredPosts = allPosts
    .filter(post => activeCategory === 'all' || post.category === activeCategory)
    .filter(post => 
      post.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
      post.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    );

  return (
    <>
      <Head>
        <title>博客 - saber的个人网站</title>
        <meta name="description" content="技术教程、项目案例分析、行业趋势和个人经验分享" />
      </Head>
      <Layout>
        <div className={styles.blogPage}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>博客</h1>
            
            <div className={styles.blogControls}>
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
            </div>
            
            <div className={styles.postsGrid}>
              {filteredPosts.length > 0 ? (
                filteredPosts.map(post => (
                  <Link href={`/blog/${post.id}`} key={post.id} className={styles.postCard}>
                    <div className={styles.postImageContainer}>
                      <div className={styles.postImage}>
                        {/* 文章图片占位符 */}
                        <div className={styles.placeholder}>
                          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            <circle cx="8.5" cy="8.5" r="1.5"></circle>
                            <polyline points="21 15 16 10 5 21"></polyline>
                          </svg>
                        </div>
                      </div>
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
                ))
              ) : (
                <div className={styles.noResults}>
                  <p>没有找到符合条件的文章</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
