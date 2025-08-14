/**
 * FeaturedProjects.tsx
 *
 * 描述：首页的精选项目部分，展示个人代表性项目
 *
 * 功能：
 * - 展示精选的个人项目
 * - 显示项目标题、描述和技术标签
 * - 提供项目图片展示
 * - 提供"查看更多项目"按钮链接到详细的项目页面
 *
 * 主要组件/接口：
 * - FeaturedProjects：精选项目组件
 * - Project：项目数据接口
 *
 * 导出：
 * - FeaturedProjects 组件（默认导出）
 */

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import styles from '@/styles/FeaturedProjects.module.css';

interface Project {
  id: string;
  title: string;
  description: string;
  image: string;
  tags: string[];
}

const FeaturedProjects: React.FC = () => {
  // 示例项目数据
  const projects: Project[] = [
    {
      id: 'project-1',
      title: '智能家居控制系统',
      description: '基于React和Node.js的智能家居控制平台，支持多设备管理和自动化场景设置',
      image: '/placeholder-project.jpg',
      tags: ['React', 'Node.js', 'IoT']
    },
    {
      id: 'project-2',
      title: '电子商务平台',
      description: '全栈电商网站，包含商品展示、购物车、支付集成和订单管理功能',
      image: '/placeholder-project.jpg',
      tags: ['Vue.js', 'Express', 'MongoDB']
    },
    {
      id: 'project-3',
      title: '数据可视化仪表板',
      description: '企业级数据分析和可视化平台，支持多种图表类型和实时数据更新',
      image: '/placeholder-project.jpg',
      tags: ['D3.js', 'TypeScript', 'GraphQL']
    }
  ];

  return (
    <section id="projects" className={styles.featuredProjects}>
      <h2 className={styles.sectionTitle}>精选项目</h2>
      <div className={styles.projectsGrid}>
        {projects.map((project) => (
          <div className={styles.projectCard} key={project.id}>
            <div className={styles.projectImageContainer}>
              <div className={styles.projectImage}>
                {/* 项目图片占位符 */}
                <div className={styles.placeholder}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                    <polyline points="21 15 16 10 5 21"></polyline>
                  </svg>
                </div>
              </div>
            </div>
            <div className={styles.projectContent}>
              <h3 className={styles.projectTitle}>{project.title}</h3>
              <p className={styles.projectDescription}>{project.description}</p>
              <div className={styles.projectTags}>
                {project.tags.map((tag, index) => (
                  <span className={styles.projectTag} key={index}>{tag}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className={styles.viewAllContainer}>
        <Link href="/projects" className={styles.viewAllButton}>
          查看更多项目
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.buttonIcon}>
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </Link>
      </div>
    </section>
  );
};

export default FeaturedProjects;
