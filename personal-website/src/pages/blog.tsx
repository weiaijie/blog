/**
 * blog.tsx
 *
 * 描述：项目记录页面，展示项目备忘列表
 */

import { useState } from 'react';
import Link from 'next/link';
import Layout from '@/components/layout/Layout';
import SeoHead from '@/components/common/SeoHead';
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
      <SeoHead
        title="项目记录 - 许辉"
        description="记录一些项目里遇到的问题、处理方式和后续想法。"
        path="/blog/"
      />
      <Layout>
        <div className={styles.blogPage}>
          <div className={styles.container}>
            <div className={styles.hero}>
              <h1 className={styles.pageTitle}>项目记录</h1>
              <p className={styles.pageDescription}>
                不按文章来写，主要是把项目里踩过的坑和处理方式先记下来。
              </p>
            </div>

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

            <div className={styles.postsList}>
              {filteredPosts.length > 0 ? (
                filteredPosts.map((post) => (
                  <Link href={`/blog/${post.id}`} key={post.id} className={styles.postItem}>
                    <div className={styles.postDate}>{post.date}</div>
                    <div className={styles.postContent}>
                      <h2 className={styles.postTitle}>{post.title}</h2>
                      <p className={styles.postExcerpt}>{post.excerpt}</p>
                      <div className={styles.postMeta}>
                        <span className={styles.postCategory}>{post.categoryLabel}</span>
                        <span className={styles.postReadTime}>{post.readTime}</span>
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
