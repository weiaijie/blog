/**
 * blog.tsx
 *
 * 描述：博客页面，展示文章列表
 */

import Head from 'next/head';
import { useState } from 'react';
import Link from 'next/link';
import Layout from '@/components/layout/Layout';
import styles from '@/styles/Blog.module.css';
import { blogPosts, blogCategories } from '@/data/blog';

export default function Blog() {
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredPosts = blogPosts
    .filter((post) => activeCategory === 'all' || post.category === activeCategory)
    .filter(
      (post) =>
        post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    );

  return (
    <>
      <Head>
        <title>博客 - saber的个人网站</title>
        <meta name="description" content="项目复盘、架构实践和工程经验文章。" />
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
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className={styles.searchIcon}
                >
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </div>

              <div className={styles.categoryFilter}>
                {blogCategories.map((category) => (
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
                filteredPosts.map((post) => (
                  <Link href={`/blog/${post.id}`} key={post.id} className={styles.postCard}>
                    <div className={styles.postContent}>
                      <div className={styles.postMeta}>
                        <span className={styles.postDate}>{post.date}</span>
                        <span className={styles.postReadTime}>{post.readTime}</span>
                      </div>
                      <h2 className={styles.postTitle}>{post.title}</h2>
                      <p className={styles.postExcerpt}>{post.excerpt}</p>
                      <div className={styles.postTags}>
                        <span className={styles.postTag}>{post.categoryLabel}</span>
                        {post.tags.map((tag) => (
                          <span className={styles.postTag} key={tag}>
                            {tag}
                          </span>
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
