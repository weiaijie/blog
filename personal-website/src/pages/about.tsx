/**
 * about.tsx
 *
 * 描述：关于我页面，展示个人简介、教育背景和工作经历
 *
 * 功能：
 * - 展示个人简介信息
 * - 使用时间线展示教育背景
 * - 使用时间线展示工作经历
 *
 * 主要组件：
 * - About：关于我页面的主要组件
 */

import Head from 'next/head';
import Layout from '@/components/layout/Layout';
import styles from '@/styles/About.module.css';

export default function About() {
  return (
    <>
      <Head>
        <title>关于我 - saber的个人网站</title>
        <meta name="description" content="了解更多关于我的背景、经历和专业技能" />
      </Head>
      <Layout>
        <div className={styles.aboutPage}>
          <div className={styles.container}>
            <h1 className={styles.pageTitle}>关于我</h1>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>个人简介</h2>
              <div className={styles.profileContent}>
                <div className={styles.profileText}>
                  <p className={styles.paragraph}>
                    我是一名热衷于创造优质用户体验的全栈开发者。拥有多年的前后端开发经验，
                    专注于构建高性能、可扩展的Web应用程序。我相信技术的力量在于解决实际问题，
                    并且始终保持对新技术的学习热情。
                  </p>
                  <p className={styles.paragraph}>
                    在我的职业生涯中，我参与过各种规模的项目开发，从小型网站到大型企业应用。
                    我擅长使用现代前端框架（如React、Vue.js）和后端技术（如Node.js、Python）
                    来构建全栈解决方案。
                  </p>
                  <p className={styles.paragraph}>
                    除了编程，我还热衷于分享知识和经验，通过博客文章和开源贡献来回馈社区。
                    我相信持续学习和知识共享是技术进步的关键。
                  </p>
                </div>
              </div>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>教育背景</h2>
              <div className={styles.timeline}>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.timelineTitle}>计算机科学与技术 - 硕士学位</h3>
                    <p className={styles.timelineSubtitle}>某知名大学 | 2018 - 2020</p>
                    <p className={styles.timelineText}>
                      主修人工智能和Web开发，毕业论文关注于前端性能优化技术研究。
                    </p>
                  </div>
                </div>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.timelineTitle}>软件工程 - 学士学位</h3>
                    <p className={styles.timelineSubtitle}>某知名大学 | 2014 - 2018</p>
                    <p className={styles.timelineText}>
                      学习了软件开发的基础知识和实践技能，参与多个团队项目开发。
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>工作经历</h2>
              <div className={styles.timeline}>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.timelineTitle}>全栈开发工程师</h3>
                    <p className={styles.timelineSubtitle}>某科技公司 | 2020 - 至今</p>
                    <p className={styles.timelineText}>
                      负责公司核心产品的前后端开发，使用React、Node.js和MongoDB技术栈。
                      主导了多个关键功能的设计和实现，提升了产品性能和用户体验。
                    </p>
                  </div>
                </div>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.timelineTitle}>前端开发工程师</h3>
                    <p className={styles.timelineSubtitle}>某互联网公司 | 2018 - 2020</p>
                    <p className={styles.timelineText}>
                      参与公司电商平台的前端开发，使用Vue.js框架构建响应式用户界面。
                      优化了网站加载速度，提升了用户转化率。
                    </p>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </Layout>
    </>
  );
}
