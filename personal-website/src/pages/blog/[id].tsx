/**
 * blog/[id].tsx
 *
 * 描述：项目记录详情页
 */

import { GetStaticPaths, GetStaticProps } from 'next';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Layout from '@/components/layout/Layout';
import SeoHead from '@/components/common/SeoHead';
import styles from '@/styles/BlogPost.module.css';
import { blogPosts, BlogPost } from '@/data/blog';

interface BlogPostPageProps {
  post: BlogPost;
}

export default function BlogPostPage({ post }: BlogPostPageProps) {
  return (
    <>
      <SeoHead
        title={`${post.title} - 许辉`}
        description={post.excerpt}
        path={`/blog/${post.id}/`}
        type="article"
        publishedTime={post.date}
      />
      <Layout>
        <article className={styles.blogPost}>
          <div className={styles.container}>
            <div className={styles.postNavigation}>
              <Link href="/blog" className={styles.backButton}>
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
                >
                  <line x1="19" y1="12" x2="5" y2="12"></line>
                  <polyline points="12 19 5 12 12 5"></polyline>
                </svg>
                返回列表
              </Link>
            </div>

            <header className={styles.postHeader}>
              <h1 className={styles.postTitle}>{post.title}</h1>
              <div className={styles.postMeta}>
                <span className={styles.postDate}>{post.date}</span>
                <span className={styles.postCategory}>{post.categoryLabel}</span>
                <span className={styles.postReadTime}>{post.readTime}</span>
              </div>
            </header>

            <div className={styles.postContent}>
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  // 忽略 markdown 中的 h1，因为我们已经在 header 中渲染了标题
                  h1: () => null
                }}
              >
                {post.content.trim()}
              </ReactMarkdown>
            </div>
          </div>
        </article>
      </Layout>
    </>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const paths = blogPosts.map((post) => ({
    params: { id: post.id },
  }));

  return {
    paths,
    fallback: false,
  };
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const post = blogPosts.find((item) => item.id === params?.id);

  if (!post) {
    return {
      notFound: true,
    };
  }

  return {
    props: {
      post,
    },
  };
};
