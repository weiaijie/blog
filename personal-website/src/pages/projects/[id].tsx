/**
 * [id].tsx
 *
 * 描述：项目详情页面，展示单个项目的完整信息
 *
 * 功能：
 * - 展示项目的详细信息和技术实现
 * - 显示项目亮点、挑战和解决方案
 * - 简约的苹果风格设计
 *
 * 主要组件：
 * - ProjectDetail：项目详情页面主组件
 */

import { GetStaticPaths, GetStaticProps } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { motion } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import { getAllProjects, getProjectById, ProjectItem } from '@/config/projects';
import styles from '@/styles/ProjectDetail.module.css';

interface ProjectDetailProps {
  project: ProjectItem;
}

export default function ProjectDetail({ project }: ProjectDetailProps) {
  if (!project) {
    return (
      <Layout>
        <div className={styles.notFound}>
          <h1>项目未找到</h1>
          <Link href="/projects">返回项目列表</Link>
        </div>
      </Layout>
    );
  }

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

  return (
    <>
      <Head>
        <title>{project.name} - 许辉的个人网站</title>
        <meta name="description" content={project.description} />
        <meta property="og:title" content={`${project.name} - 许辉的个人网站`} />
        <meta property="og:description" content={project.description} />
        <meta property="og:type" content="article" />
      </Head>
      <Layout>
        <motion.div 
          className={styles.projectDetailPage}
          variants={pageVariants}
          initial="hidden"
          animate="visible"
        >
          <div className={styles.container}>
            {/* 返回按钮 */}
            <motion.div
              className={styles.backButton}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Link href="/projects" className={styles.backLink}>
                <span className={styles.backIcon}>←</span>
                返回项目列表
              </Link>
            </motion.div>

            {/* 项目头部 */}
            <motion.header
              className={styles.projectHeader}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <div className={styles.headerContent}>
                <span className={styles.projectIcon} style={{ color: project.color }}>
                  {project.icon}
                </span>
                <div className={styles.headerInfo}>
                  <h1 className={styles.projectTitle}>{project.name}</h1>
                  <p className={styles.projectSubtitle}>{project.description}</p>
                  <div className={styles.projectMeta}>
                    <span className={styles.metaItem}>
                      <strong>角色：</strong>{project.role}
                    </span>
                    <span className={styles.metaItem}>
                      <strong>团队：</strong>{project.teamSize}
                    </span>
                    <span className={styles.metaItem}>
                      <strong>周期：</strong>{project.duration}
                    </span>
                    <span className={styles.statusBadge} data-status={project.status}>
                      {project.status === 'completed' ? '已完成' : 
                       project.status === 'in-progress' ? '进行中' : '已归档'}
                    </span>
                  </div>
                </div>
              </div>
            </motion.header>

            {/* 项目详情 */}
            <div className={styles.projectContent}>
              {/* 项目描述 */}
              <motion.section
                className={styles.section}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.6, delay: 0.4 }}
              >
                <h2 className={styles.sectionTitle}>项目概述</h2>
                <p className={styles.detailedDescription}>{project.detailedDescription}</p>
              </motion.section>

              {/* 技术栈 */}
              <motion.section
                className={styles.section}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.6, delay: 0.5 }}
              >
                <h2 className={styles.sectionTitle}>技术栈</h2>
                <div className={styles.techStack}>
                  {project.technologies.map((tech, index) => (
                    <motion.span
                      key={index}
                      className={styles.techTag}
                      initial={{ opacity: 0, scale: 0.8 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                      whileHover={{ scale: 1.05 }}
                    >
                      {tech}
                    </motion.span>
                  ))}
                </div>
              </motion.section>

              {/* 项目亮点 */}
              <motion.section
                className={styles.section}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.6, delay: 0.6 }}
              >
                <h2 className={styles.sectionTitle}>项目亮点</h2>
                <div className={styles.highlightsList}>
                  {project.highlights.map((highlight, index) => (
                    <motion.div
                      key={index}
                      className={styles.highlightItem}
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.4, delay: index * 0.1 }}
                    >
                      <span className={styles.highlightIcon}>✓</span>
                      <span className={styles.highlightText}>{highlight}</span>
                    </motion.div>
                  ))}
                </div>
              </motion.section>

              {/* 挑战与解决方案 */}
              <motion.section
                className={styles.section}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.6, delay: 0.7 }}
              >
                <h2 className={styles.sectionTitle}>挑战与解决方案</h2>
                <div className={styles.challengesGrid}>
                  <div className={styles.challengesColumn}>
                    <h3 className={styles.columnTitle}>面临的挑战</h3>
                    <div className={styles.itemsList}>
                      {project.challenges.map((challenge, index) => (
                        <motion.div
                          key={index}
                          className={styles.challengeItem}
                          initial={{ opacity: 0, y: 20 }}
                          whileInView={{ opacity: 1, y: 0 }}
                          viewport={{ once: true }}
                          transition={{ duration: 0.4, delay: index * 0.1 }}
                        >
                          <span className={styles.itemIcon}>⚠️</span>
                          <span className={styles.itemText}>{challenge}</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                  <div className={styles.solutionsColumn}>
                    <h3 className={styles.columnTitle}>解决方案</h3>
                    <div className={styles.itemsList}>
                      {project.solutions.map((solution, index) => (
                        <motion.div
                          key={index}
                          className={styles.solutionItem}
                          initial={{ opacity: 0, y: 20 }}
                          whileInView={{ opacity: 1, y: 0 }}
                          viewport={{ once: true }}
                          transition={{ duration: 0.4, delay: index * 0.1 }}
                        >
                          <span className={styles.itemIcon}>💡</span>
                          <span className={styles.itemText}>{solution}</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.section>

              {/* 项目成果 */}
              <motion.section
                className={styles.section}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.6, delay: 0.8 }}
              >
                <h2 className={styles.sectionTitle}>项目成果</h2>
                <div className={styles.resultsList}>
                  {project.results.map((result, index) => (
                    <motion.div
                      key={index}
                      className={styles.resultItem}
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.4, delay: index * 0.1 }}
                    >
                      <span className={styles.resultIcon}>🎯</span>
                      <span className={styles.resultText}>{result}</span>
                    </motion.div>
                  ))}
                </div>
              </motion.section>
            </div>
          </div>
        </motion.div>
      </Layout>
    </>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const projects = getAllProjects();
  const paths = projects.map((project) => ({
    params: { id: project.id },
  }));

  return {
    paths,
    fallback: false,
  };
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const project = getProjectById(params?.id as string);

  if (!project) {
    return {
      notFound: true,
    };
  }

  return {
    props: {
      project,
    },
  };
};
