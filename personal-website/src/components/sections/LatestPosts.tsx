/**
 * LatestPosts.tsx
 *
 * 描述：首页的最新文章部分，展示真实文章摘要
 */

import Link from 'next/link';
import styles from '@/styles/LatestPosts.module.css';
import { featuredBlogPosts } from '@/data/blog';

const LatestPosts = () => {
  return (
    <section id="blog" className={styles.latestPosts}>
      <h2 className={styles.sectionTitle}>最新文章</h2>
      <div className={styles.postsList}>
        {featuredBlogPosts.map((post) => (
          <Link href={`/blog/${post.id}`} key={post.id} className={styles.postItem}>
            <div className={styles.postDate}>{post.date}</div>
            <div className={styles.postContent}>
              <h3 className={styles.postTitle}>{post.title}</h3>
              <div className={styles.postMeta}>
                <span className={styles.postCategory}>{post.categoryLabel}</span>
                <span className={styles.postReadTime}>{post.readTime}</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
      <div className={styles.viewAllContainer}>
        <Link href="/blog" className={styles.viewAllButton}>
          查看全部文章
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={styles.buttonIcon}
          >
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </Link>
      </div>
    </section>
  );
};

export default LatestPosts;
