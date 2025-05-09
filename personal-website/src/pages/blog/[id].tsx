import { GetStaticPaths, GetStaticProps } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { motion } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import styles from '@/styles/BlogPost.module.css';

interface BlogPost {
  id: string;
  title: string;
  date: string;
  excerpt: string;
  category: string;
  tags: string[];
  readTime: string;
  image?: string;
  content?: string;
}

// 示例博客文章数据 - 在实际应用中，这些数据应该从API或数据库获取
const blogPosts: BlogPost[] = [
  {
    id: 'post-1',
    title: '如何构建高性能React应用',
    date: '2023-05-15',
    excerpt: '探讨React性能优化的关键策略，包括组件拆分、状态管理和渲染优化',
    category: 'tutorial',
    tags: ['React', '性能优化', '前端开发'],
    readTime: '8分钟',
    image: '/placeholder-blog.jpg',
    content: `
      # 如何构建高性能React应用

      在当今的Web开发中，用户体验至关重要，而性能是用户体验的核心组成部分。React作为一个流行的前端库，提供了许多优化性能的方法和工具。本文将探讨如何构建高性能的React应用。

      ## 组件优化

      ### 使用React.memo
      
      React.memo是一个高阶组件，它可以帮助你的组件避免不必要的重新渲染。当组件的props没有变化时，React.memo会复用最近一次渲染的结果，而不是重新渲染组件。

      \`\`\`jsx
      const MyComponent = React.memo(function MyComponent(props) {
        // 组件逻辑
      });
      \`\`\`

      ### 使用useMemo和useCallback
      
      useMemo和useCallback钩子可以帮助你缓存计算结果和函数引用，避免在每次渲染时重新创建。

      \`\`\`jsx
      // 缓存计算结果
      const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
      
      // 缓存函数引用
      const memoizedCallback = useCallback(() => {
        doSomething(a, b);
      }, [a, b]);
      \`\`\`

      ## 状态管理优化

      ### 使用合适的状态管理方案
      
      根据应用的复杂度选择合适的状态管理方案：
      
      - 对于简单应用，使用React的内置状态管理（useState, useReducer）
      - 对于中等复杂度的应用，可以考虑使用Context API
      - 对于复杂应用，可以使用Redux, MobX等状态管理库

      ### 避免状态冗余
      
      确保你的状态是DRY（Don't Repeat Yourself）的，避免存储可以从现有状态派生的数据。

      ## 渲染优化

      ### 虚拟列表
      
      对于长列表，使用虚拟列表技术（如react-window或react-virtualized）只渲染可见区域的项目。

      ### 代码分割
      
      使用React.lazy和Suspense进行代码分割，只加载当前需要的代码。

      \`\`\`jsx
      const OtherComponent = React.lazy(() => import('./OtherComponent'));

      function MyComponent() {
        return (
          <React.Suspense fallback={<div>Loading...</div>}>
            <OtherComponent />
          </React.Suspense>
        );
      }
      \`\`\`

      ## 总结

      构建高性能的React应用需要从多个方面入手，包括组件优化、状态管理和渲染优化。通过合理使用React提供的API和工具，可以显著提升应用的性能和用户体验。
    `
  },
  {
    id: 'post-2',
    title: 'TypeScript高级类型技巧',
    date: '2023-04-28',
    excerpt: '深入探讨TypeScript的高级类型系统，帮助你编写更安全、更可维护的代码',
    category: 'tutorial',
    tags: ['TypeScript', '前端开发'],
    readTime: '10分钟',
    image: '/placeholder-blog.jpg',
    content: `
      # TypeScript高级类型技巧

      TypeScript的类型系统非常强大，掌握高级类型技巧可以帮助你编写更安全、更可维护的代码。本文将介绍一些TypeScript的高级类型技巧。

      ## 联合类型和交叉类型

      联合类型（Union Types）表示一个值可以是几种类型之一：

      \`\`\`typescript
      type StringOrNumber = string | number;
      \`\`\`

      交叉类型（Intersection Types）将多个类型合并为一个类型：

      \`\`\`typescript
      type Person = { name: string } & { age: number };
      \`\`\`

      ## 条件类型

      条件类型可以根据条件选择不同的类型：

      \`\`\`typescript
      type TypeName<T> = 
        T extends string ? "string" :
        T extends number ? "number" :
        T extends boolean ? "boolean" :
        "object";
      \`\`\`

      ## 映射类型

      映射类型可以从现有类型创建新类型：

      \`\`\`typescript
      type Readonly<T> = {
        readonly [P in keyof T]: T[P];
      };
      \`\`\`

      ## 总结

      TypeScript的高级类型系统提供了强大的工具，可以帮助你创建更精确的类型定义，提高代码的安全性和可维护性。
    `
  },
  // 其他文章数据...
];

interface BlogPostPageProps {
  post: BlogPost;
}

export default function BlogPostPage({ post }: BlogPostPageProps) {
  if (!post) {
    return (
      <Layout>
        <div className={styles.container}>
          <h1>文章不存在</h1>
          <Link href="/blog">返回博客列表</Link>
        </div>
      </Layout>
    );
  }

  return (
    <>
      <Head>
        <title>{post.title} - saber的个人网站</title>
        <meta name="description" content={post.excerpt} />
      </Head>
      <Layout>
        <article className={styles.blogPost}>
          <div className={styles.container}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <header className={styles.postHeader}>
                <div className={styles.postMeta}>
                  <span className={styles.postDate}>{post.date}</span>
                  <span className={styles.postReadTime}>{post.readTime}</span>
                </div>
                <h1 className={styles.postTitle}>{post.title}</h1>
                <div className={styles.postTags}>
                  {post.tags.map((tag, index) => (
                    <span className={styles.postTag} key={index}>{tag}</span>
                  ))}
                </div>
              </header>
            </motion.div>

            {post.image && (
              <motion.div
                className={styles.postImageContainer}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <div className={styles.postImage}>
                  {/* 文章图片占位符 */}
                  <div className={styles.placeholder}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                      <circle cx="8.5" cy="8.5" r="1.5"></circle>
                      <polyline points="21 15 16 10 5 21"></polyline>
                    </svg>
                  </div>
                </div>
              </motion.div>
            )}

            <motion.div
              className={styles.postContent}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              dangerouslySetInnerHTML={{ __html: post.content ? post.content.replace(/\n/g, '<br>') : '' }}
            />

            <div className={styles.postNavigation}>
              <Link href="/blog" className={styles.backButton}>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="19" y1="12" x2="5" y2="12"></line>
                  <polyline points="12 19 5 12 12 5"></polyline>
                </svg>
                返回博客列表
              </Link>
            </div>
          </div>
        </article>
      </Layout>
    </>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  // 在实际应用中，这些路径应该从API或数据库获取
  const paths = blogPosts.map(post => ({
    params: { id: post.id }
  }));

  return {
    paths,
    fallback: false // 如果访问的路径不存在，返回404页面
  };
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  // 在实际应用中，这些数据应该从API或数据库获取
  const post = blogPosts.find(p => p.id === params?.id);

  // 如果找不到文章，返回404
  if (!post) {
    return {
      notFound: true
    };
  }

  return {
    props: {
      post
    }
  };
};
