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

import { motion } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import SEOHead from '@/components/common/SEOHead';
import { skillsData } from '@/config/skills';
import styles from '@/styles/Skills.module.css';

export default function Skills() {

  // 页面动画变体
  const pageVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: "easeOut"
      }
    }
  };

  const titleVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.8,
        ease: "easeOut",
        delay: 0.2
      }
    }
  };

  return (
    <>
      <SEOHead
        title="技能"
        description="7年全栈开发经验，Vue.js + React + Next.js + Node.js，熟练掌握现代Web开发技术栈"
        type="profile"
        keywords={['技能', '全栈开发', '前端开发', '后端开发', 'React', 'Vue.js', 'Next.js', 'Node.js', 'TypeScript', 'JavaScript']}
        image="/images/skills-og.svg"
      />
      <Layout>
        <motion.div
          className={styles.skillsPage}
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
              技能专长
            </motion.h1>

            <motion.div
              className={styles.skillsIntro}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <p className={styles.introText}>
                7年全栈开发经验，专注于Vue.js、React、Next.js等现代前端技术栈，
                具备Node.js后端开发能力，能够独立完成全栈项目开发。
              </p>
            </motion.div>

            {/* 简约的技能展示 */}
            <div className={styles.skillsGrid}>
              {skillsData.map((category, categoryIndex) => (
                <motion.section
                  key={category.id}
                  className={styles.skillSection}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.3 }}
                  transition={{ duration: 0.6, delay: categoryIndex * 0.1 }}
                >
                  <div className={styles.sectionHeader}>
                    <span className={styles.sectionIcon}>{category.icon}</span>
                    <h2 className={styles.sectionTitle}>{category.name}</h2>
                  </div>
                  <p className={styles.sectionDescription}>{category.description}</p>

                  <div className={styles.skillsList}>
                    {category.skills.map((skill, skillIndex) => (
                      <motion.div
                        key={skill.id}
                        className={styles.skillItem}
                        initial={{ opacity: 0, scale: 0.9 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.4, delay: skillIndex * 0.05 }}
                        whileHover={{ scale: 1.02 }}
                      >
                        <div className={styles.skillHeader}>
                          <span className={styles.skillIcon}>{skill.icon}</span>
                          <h3 className={styles.skillName}>{skill.name}</h3>
                          <div className={styles.skillLevel}>
                            {'⭐'.repeat(skill.level)}
                          </div>
                        </div>
                        <div className={styles.skillProgress}>
                          <motion.div
                            className={styles.progressBar}
                            style={{ backgroundColor: skill.color }}
                            initial={{ width: 0 }}
                            whileInView={{ width: `${skill.percentage}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 1, delay: 0.2 }}
                          />
                        </div>
                        <p className={styles.skillDescription}>{skill.description}</p>
                      </motion.div>
                    ))}
                  </div>
                </motion.section>
              ))}
            </div>
          </div>
        </motion.div>
      </Layout>
    </>
  );
}
