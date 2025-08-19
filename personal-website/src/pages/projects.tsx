/**
 * projects.tsx
 *
 * 描述：项目展示页面，展示个人项目作品和技术实现
 *
 * 功能：
 * - 展示项目分类和详细信息
 * - 显示技术栈和项目成果
 * - 简约的苹果风格设计
 *
 * 主要组件：
 * - Projects：项目页面主组件
 */

import Link from 'next/link';
import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import SEOHead from '@/components/common/SEOHead';
import ProjectFilter, { FilterOptions } from '@/components/common/ProjectFilter';
import { projectsData, getFeaturedProjects, getAllProjects, ProjectItem } from '@/config/projects';
import styles from '@/styles/Projects.module.css';

export default function Projects() {
  // 筛选状态
  const [filters, setFilters] = useState<FilterOptions>({
    category: 'all',
    technology: 'all',
    status: 'all',
    type: 'all',
    sort: 'newest',
    search: ''
  });

  // 获取所有项目
  const allProjects = getAllProjects();

  // 筛选和排序后的项目数据
  const filteredAndSortedProjects = useMemo(() => {
    let filtered = allProjects.filter(project => {
      // 按分类筛选
      if (filters.category !== 'all' && project.category !== filters.category) {
        return false;
      }

      // 按技术栈筛选
      if (filters.technology !== 'all' && !project.technologies.includes(filters.technology)) {
        return false;
      }

      // 按状态筛选
      if (filters.status !== 'all' && project.status !== filters.status) {
        return false;
      }

      // 按类型筛选
      if (filters.type !== 'all' && project.type !== filters.type) {
        return false;
      }

      // 按搜索关键词筛选
      if (filters.search.trim() !== '') {
        const searchTerm = filters.search.toLowerCase();
        return (
          project.name.toLowerCase().includes(searchTerm) ||
          project.description.toLowerCase().includes(searchTerm) ||
          project.detailedDescription.toLowerCase().includes(searchTerm) ||
          project.technologies.some(tech =>
            tech.toLowerCase().includes(searchTerm)
          )
        );
      }

      return true;
    });

    // 排序
    filtered.sort((a, b) => {
      switch (filters.sort) {
        case 'newest':
          return new Date(b.startDate).getTime() - new Date(a.startDate).getTime();
        case 'oldest':
          return new Date(a.startDate).getTime() - new Date(b.startDate).getTime();
        case 'name':
          return a.name.localeCompare(b.name);
        case 'status':
          const statusOrder = { 'in-progress': 0, 'completed': 1, 'archived': 2 };
          return statusOrder[a.status] - statusOrder[b.status];
        default:
          return 0;
      }
    });

    return filtered;
  }, [allProjects, filters]);

  // 按分类重新组织筛选后的项目
  const filteredProjectsData = useMemo(() => {
    return projectsData.map(category => {
      const categoryProjects = filteredAndSortedProjects.filter(
        project => project.category === category.id
      );

      if (categoryProjects.length === 0) {
        return null;
      }

      return {
        ...category,
        projects: categoryProjects
      };
    }).filter(Boolean);
  }, [filteredAndSortedProjects]);

  // 处理筛选条件变化
  const handleFilterChange = (newFilters: FilterOptions) => {
    setFilters(newFilters);
  };

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
        title="项目"
        description="7年全栈开发经验项目作品展示，包含企业级应用、业务系统、Web开发等实际项目案例"
        type="website"
        keywords={['项目作品', '全栈开发', '企业级应用', 'Vue.js', 'React', 'Next.js', 'Node.js', '业务系统', 'Web开发']}
        image="/images/projects-og.svg"
      />
      <Layout>
        <motion.div 
          className={styles.projectsPage}
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
              我的项目
            </motion.h1>

            <motion.div
              className={styles.projectsIntro}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <p className={styles.introText}>
                7年全栈开发经验，参与开发了多个企业级应用和业务系统。
                以下是我的主要项目作品，展示了在不同技术栈和业务场景下的实践经验。
              </p>
            </motion.div>

            {/* 项目筛选器 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              <ProjectFilter
                projects={allProjects}
                onFilterChange={handleFilterChange}
              />
            </motion.div>

            {/* 筛选结果统计 */}
            {(filters.category !== 'all' || filters.technology !== 'all' || filters.status !== 'all' ||
              filters.type !== 'all' || filters.search.trim() !== '') && (
              <motion.div
                className={styles.filterResults}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4 }}
              >
                <p className={styles.resultsText}>
                  找到 {filteredAndSortedProjects.length} 个项目
                  {filters.sort !== 'newest' && (
                    <span className={styles.sortInfo}>
                      ，按{filters.sort === 'oldest' ? '时间升序' :
                           filters.sort === 'name' ? '名称' : '状态'}排序
                    </span>
                  )}
                </p>
              </motion.div>
            )}

            {/* 精选项目 */}
            <motion.section
              className={styles.featuredSection}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              <h2 className={styles.sectionTitle}>精选项目</h2>
              <div className={styles.featuredGrid}>
                {getFeaturedProjects().map((project, index) => (
                  <Link
                    key={project.id}
                    href={`/projects/${project.id}`}
                    className={styles.projectLink}
                    aria-label={`查看项目详情：${project.name}`}
                  >
                    <motion.div
                      className={styles.featuredCard}
                      initial={{ opacity: 0, y: 30 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.6, delay: index * 0.1 }}
                      whileHover={{ y: -5 }}
                      role="article"
                      tabIndex={0}
                    >
                    <div className={styles.cardHeader}>
                      <span className={styles.projectIcon} style={{ color: project.color }}>
                        {project.icon}
                      </span>
                      <div className={styles.projectMeta}>
                        <h3 className={styles.projectTitle}>{project.name}</h3>
                        <p className={styles.projectPeriod}>{project.duration}</p>
                      </div>
                      <span className={styles.statusBadge} data-status={project.status}>
                        {project.status === 'completed' ? '已完成' : 
                         project.status === 'in-progress' ? '进行中' : '已归档'}
                      </span>
                    </div>
                    <p className={styles.projectDescription}>{project.description}</p>
                    <div className={styles.techStack}>
                      {project.technologies.slice(0, 4).map((tech, techIndex) => (
                        <span key={techIndex} className={styles.techTag}>{tech}</span>
                      ))}
                      {project.technologies.length > 4 && (
                        <span className={styles.techMore}>+{project.technologies.length - 4}</span>
                      )}
                    </div>
                    <div className={styles.projectHighlights}>
                      {project.highlights.slice(0, 2).map((highlight, hlIndex) => (
                        <div key={hlIndex} className={styles.highlight}>
                          <span className={styles.highlightIcon}>✓</span>
                          <span className={styles.highlightText}>{highlight}</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                  </Link>
                ))}
              </div>
            </motion.section>

            {/* 所有项目分类 */}
            <div className={styles.categoriesContainer}>
              {filteredProjectsData.length > 0 ? (
                filteredProjectsData.map((category, categoryIndex) => (
                <motion.section
                  key={category.id}
                  className={styles.categorySection}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.3 }}
                  transition={{ duration: 0.6, delay: categoryIndex * 0.1 }}
                >
                  <div className={styles.categoryHeader}>
                    <span className={styles.categoryIcon}>{category.icon}</span>
                    <div className={styles.categoryInfo}>
                      <h2 className={styles.categoryTitle}>{category.name}</h2>
                      <p className={styles.categoryDescription}>{category.description}</p>
                    </div>
                    <span className={styles.projectCount}>{category.projects.length} 个项目</span>
                  </div>
                  
                  <div className={styles.projectsGrid}>
                    {category.projects.map((project, projectIndex) => (
                      <Link
                        key={project.id}
                        href={`/projects/${project.id}`}
                        className={styles.projectLink}
                        aria-label={`查看项目详情：${project.name}`}
                      >
                        <motion.div
                          className={styles.projectCard}
                          initial={{ opacity: 0, scale: 0.95 }}
                          whileInView={{ opacity: 1, scale: 1 }}
                          viewport={{ once: true }}
                          transition={{ duration: 0.4, delay: projectIndex * 0.05 }}
                          whileHover={{ scale: 1.02 }}
                          role="article"
                          tabIndex={0}
                        >
                        <div className={styles.cardContent}>
                          <div className={styles.projectHeader}>
                            <span className={styles.projectIcon} style={{ color: project.color }}>
                              {project.icon}
                            </span>
                            <h3 className={styles.projectName}>{project.name}</h3>
                          </div>
                          <p className={styles.projectDesc}>{project.description}</p>
                          <div className={styles.projectDetails}>
                            <span className={styles.role}>{project.role}</span>
                            <span className={styles.team}>{project.teamSize}</span>
                            <span className={styles.duration}>{project.duration}</span>
                          </div>
                          <div className={styles.technologies}>
                            {project.technologies.slice(0, 3).map((tech, techIndex) => (
                              <span key={techIndex} className={styles.tech}>{tech}</span>
                            ))}
                            {project.technologies.length > 3 && (
                              <span className={styles.techMore}>+{project.technologies.length - 3}</span>
                            )}
                          </div>
                        </div>
                      </motion.div>
                      </Link>
                    ))}
                  </div>
                </motion.section>
              ))
              ) : (
                <motion.div
                  className={styles.noResults}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                >
                  <div className={styles.noResultsIcon}>🔍</div>
                  <h3 className={styles.noResultsTitle}>未找到匹配的项目</h3>
                  <p className={styles.noResultsText}>
                    请尝试调整筛选条件或搜索关键词
                  </p>
                </motion.div>
              )}
            </div>
          </div>
        </motion.div>
      </Layout>
    </>
  );
}
