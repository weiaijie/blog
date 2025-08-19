/**
 * about.tsx
 *
 * 描述：关于我页面，展示个人信息、技能和经历
 *
 * 功能：
 * - 展示个人基本信息和介绍
 * - 显示核心技能和专长
 * - 展示工作经历和教育背景
 * - 简约的苹果风格设计
 *
 * 主要组件：
 * - About：关于我页面主组件
 */

import { motion } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import SEOHead from '@/components/common/SEOHead';
import useReducedMotion, { getReducedMotionVariants, getReducedMotionTransition } from '@/hooks/useReducedMotion';
import styles from '@/styles/About.module.css';

export default function About() {
  // 检测用户动画偏好
  const prefersReducedMotion = useReducedMotion();

  // 页面动画变体
  const pageVariants = getReducedMotionVariants({
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: getReducedMotionTransition({
        duration: 0.6,
        ease: "easeOut"
      }, prefersReducedMotion)
    }
  }, prefersReducedMotion);

  const titleVariants = getReducedMotionVariants({
    hidden: { opacity: 0, scale: 0.9 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: getReducedMotionTransition({
        duration: 0.8,
        ease: "easeOut",
        delay: 0.2
      }, prefersReducedMotion)
    }
  }, prefersReducedMotion);

  return (
    <>
      <SEOHead
        title="关于我"
        description="7年全栈开发经验，Vue.js + React + Next.js + Node.js，专注于创造优质的用户体验"
        type="profile"
        keywords={['全栈开发', '前端开发', '后端开发', 'React', 'Vue.js', 'Next.js', 'Node.js', '许辉']}
        image="/images/about-og.jpg"
      />
      <Layout>
        <motion.div 
          className={styles.aboutPage}
          variants={pageVariants}
          initial="hidden"
          animate="visible"
        >
          <div className={styles.container}>
            <motion.h1 
              className={styles.pageTitle}
              variants={titleVariants}
              initial="hidden"
              animate="visible"
            >
              关于我
            </motion.h1>

            {/* 个人介绍 */}
            <motion.section
              className={styles.introSection}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              aria-label="个人介绍"
              role="region"
            >
              <div className={styles.introContent}>
                <p className={styles.introText}>
                  你好！我是许辉，一名拥有7年丰富经验的全栈开发工程师。
                  专注于Vue.js、React、Next.js等现代前端技术栈，具备Node.js后端开发能力，
                  能够独立完成从前端到后端的完整项目开发。
                </p>
                <p className={styles.introText}>
                  在项目管理和团队协作方面，具备完整的项目开发经验，
                  善于跨部门沟通协调，始终保持学习热情，关注技术发展趋势。
                </p>
              </div>
            </motion.section>

            {/* 核心技能 */}
            <motion.section
              className={styles.skillsSection}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              aria-labelledby="skills-heading"
              role="region"
            >
              <h2 id="skills-heading" className={styles.sectionTitle}>核心技能</h2>
              <div className={styles.skillsGrid}>
                <div className={styles.skillCategory}>
                  <h3 className={styles.categoryTitle}>前端开发</h3>
                  <div className={styles.skillTags}>
                    <span className={styles.skillTag}>Vue.js</span>
                    <span className={styles.skillTag}>React</span>
                    <span className={styles.skillTag}>Next.js</span>
                    <span className={styles.skillTag}>TypeScript</span>
                    <span className={styles.skillTag}>Element UI</span>
                    <span className={styles.skillTag}>Ant Design</span>
                  </div>
                </div>
                <div className={styles.skillCategory}>
                  <h3 className={styles.categoryTitle}>后端开发</h3>
                  <div className={styles.skillTags}>
                    <span className={styles.skillTag}>Node.js</span>
                    <span className={styles.skillTag}>Express</span>
                    <span className={styles.skillTag}>MySQL</span>
                    <span className={styles.skillTag}>PHP</span>
                  </div>
                </div>
                <div className={styles.skillCategory}>
                  <h3 className={styles.categoryTitle}>开发工具</h3>
                  <div className={styles.skillTags}>
                    <span className={styles.skillTag}>Git</span>
                    <span className={styles.skillTag}>Webpack</span>
                    <span className={styles.skillTag}>Vite</span>
                    <span className={styles.skillTag}>ECharts</span>
                  </div>
                </div>
              </div>
            </motion.section>

            {/* 工作经历 */}
            <motion.section
              className={styles.experienceSection}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: 0.8 }}
              aria-labelledby="experience-heading"
              role="region"
            >
              <h2 id="experience-heading" className={styles.sectionTitle}>工作经历</h2>
              <div className={styles.timeline}>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.jobTitle}>前端开发工程师</h3>
                    <p className={styles.company}>上海青松信息技术有限公司</p>
                    <p className={styles.period}>2022.06 - 2024.08</p>
                    <p className={styles.description}>
                      负责SaaS后台管理系统开发，支持多家医院的进修生管理，
                      开发了驾驶舱大屏和形成性评价系统。
                    </p>
                  </div>
                </div>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.jobTitle}>前端开发工程师</h3>
                    <p className={styles.company}>上海青松信息技术有限公司</p>
                    <p className={styles.period}>2021.09 - 2022.06</p>
                    <p className={styles.description}>
                      负责项目管理系统开发，专注于别墅装修项目管理，
                      支持PC端和飞书小程序双端开发。
                    </p>
                  </div>
                </div>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.jobTitle}>前端开发工程师</h3>
                    <p className={styles.company}>上海青松信息技术有限公司</p>
                    <p className={styles.period}>2019.10 - 2021.06</p>
                    <p className={styles.description}>
                      负责交易所管理系统开发，包含用户管理、权限控制、
                      数据可视化等功能模块。
                    </p>
                  </div>
                </div>
                <div className={styles.timelineItem}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <h3 className={styles.jobTitle}>前端开发工程师</h3>
                    <p className={styles.company}>上海欧莱美医疗美容医院</p>
                    <p className={styles.period}>2018.05 - 2019.08</p>
                    <p className={styles.description}>
                      负责医疗美容官网开发和维护，包括管理后台和移动端功能开发。
                    </p>
                  </div>
                </div>
              </div>
            </motion.section>

            {/* 教育背景 */}
            <motion.section
              className={styles.educationSection}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: 1.0 }}
              aria-labelledby="education-heading"
              role="region"
            >
              <h2 id="education-heading" className={styles.sectionTitle}>教育背景</h2>
              <div className={styles.educationCard}>
                <h3 className={styles.degree}>大专 · 计算机应用技术</h3>
                <p className={styles.school}>上海中侨职业技术学院</p>
                <p className={styles.period}>2015.09 - 2018.06</p>
              </div>
            </motion.section>
          </div>
        </motion.div>
      </Layout>
    </>
  );
}
