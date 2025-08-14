/**
 * skills.tsx
 *
 * 描述：技能展示页面，用于展示个人的技术技能和专业能力
 *
 * 功能：
 * - 展示不同类别的技能（前端开发、后端开发、其他技术技能）
 * - 使用动画效果展示技能熟练度条
 * - 通过 IntersectionObserver 实现滚动时的技能条动画
 *
 * 主要组件：
 * - Skills：主要组件，包含技能展示逻辑和布局
 */

import Head from 'next/head';
import { useEffect, useRef } from 'react';
import Layout from '@/components/layout/Layout';
import styles from '@/styles/Skills.module.css';

export default function Skills() {
  const skillsRef = useRef<HTMLDivElement>(null);

  // 监听滚动，添加技能条动画
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add(styles.animate);
          }
        });
      },
      { threshold: 0.1 }
    );

    const skillBars = document.querySelectorAll(`.${styles.skillBar}`);
    skillBars.forEach((bar) => observer.observe(bar));

    return () => {
      skillBars.forEach((bar) => observer.unobserve(bar));
    };
  }, []);

  return (
    <>
      <Head>
        <title>技能 - saber的个人网站</title>
        <meta name="description" content="我的技术技能和专业能力" />
      </Head>
      <Layout>
        <div className={styles.skillsPage} ref={skillsRef}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>技能</h1>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>前端开发</h2>
              <div className={styles.skillsGrid}>
                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>HTML/CSS</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '95%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    精通HTML5语义化标签和结构，CSS3高级特性（动画、过渡、变换），
                    熟练使用预处理器（Sass/LESS）和CSS框架（Bootstrap、Tailwind CSS），
                    擅长响应式设计和移动优先原则。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>JavaScript/TypeScript</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '85%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    熟练掌握ES6+特性和语法，TypeScript类型系统和接口，
                    DOM操作和事件处理，异步编程（Promise、async/await），
                    以及模块化开发方法。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>前端框架</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '80%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    精通React生态系统（Redux、React Router），熟悉Vue.js（Vuex、Vue Router），
                    擅长组件设计和状态管理，了解前端性能优化技巧。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>响应式设计</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '90%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    熟练掌握媒体查询和断点设计，Flexbox和Grid布局，
                    移动优先策略，以及跨设备兼容性测试方法。
                  </p>
                </div>
              </div>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>后端开发</h2>
              <div className={styles.skillsGrid}>
                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>Node.js</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '80%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    熟练使用Express和Nest.js框架构建RESTful API，
                    了解Node.js性能优化和最佳实践。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>数据库</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '70%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    熟悉关系型数据库（MySQL、PostgreSQL）和NoSQL数据库（MongoDB、Redis），
                    了解SQL查询优化和ORM工具。
                  </p>
                </div>
              </div>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>其他技术技能</h2>
              <div className={styles.skillsGrid}>
                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>版本控制</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '95%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    精通Git工作流（分支策略、合并请求），GitHub/GitLab协作，
                    以及代码审查最佳实践。
                  </p>
                </div>

                <div className={styles.skillItem}>
                  <div className={styles.skillHeader}>
                    <h3 className={styles.skillName}>DevOps</h3>
                    <span className={styles.skillLevel}>⭐⭐⭐</span>
                  </div>
                  <div className={styles.skillBarContainer}>
                    <div
                      className={styles.skillBar}
                      style={{ '--skill-level': '65%' } as React.CSSProperties}
                    ></div>
                  </div>
                  <p className={styles.skillDescription}>
                    了解CI/CD流程（Jenkins、GitHub Actions），自动化测试，
                    以及监控和日志（ELK Stack）。
                  </p>
                </div>
              </div>
            </section>
          </div>
        </div>
      </Layout>
    </>
  );
}
