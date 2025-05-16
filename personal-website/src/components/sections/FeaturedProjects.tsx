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
 * - 支持3D卡片效果和滑入动画
 * - 项目卡片随鼠标移动而倾斜
 *
 * 主要组件/接口：
 * - FeaturedProjects：精选项目组件
 * - Project：项目数据接口
 * - ProjectCard：项目卡片组件
 *
 * 导出：
 * - FeaturedProjects 组件（默认导出）
 */

import React, { useRef, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion, useMotionValue, useTransform, useSpring, useInView } from 'framer-motion';
import styles from '@/styles/FeaturedProjects.module.css';

interface Project {
  id: string;
  title: string;
  description: string;
  image: string;
  tags: string[];
  color?: string;
}

// 项目卡片组件
const ProjectCard: React.FC<{ project: Project; index: number }> = ({ project, index }) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(cardRef, { once: true, amount: 0.3 });

  // 鼠标位置状态
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // 3D变换效果的值
  const rotateX = useTransform(mouseY, [-100, 100], [5, -5]);
  const rotateY = useTransform(mouseX, [-100, 100], [-5, 5]);

  // 使用spring添加平滑效果
  const springRotateX = useSpring(rotateX, { stiffness: 100, damping: 30 });
  const springRotateY = useSpring(rotateY, { stiffness: 100, damping: 30 });

  // 处理鼠标移动
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;

    const rect = cardRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    mouseX.set(e.clientX - centerX);
    mouseY.set(e.clientY - centerY);
  };

  // 鼠标离开时重置
  const handleMouseLeave = () => {
    mouseX.set(0);
    mouseY.set(0);
  };

  // 卡片动画变体
  const cardVariants = {
    hidden: {
      opacity: 0,
      y: 50,
      scale: 0.9
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        duration: 0.6,
        delay: index * 0.2,
        ease: [0.16, 1, 0.3, 1]
      }
    }
  };

  return (
    <motion.div
      ref={cardRef}
      className={styles.projectCard}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        perspective: 1000,
        rotateX: springRotateX,
        rotateY: springRotateY,
        transformStyle: "preserve-3d"
      }}
      variants={cardVariants}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
    >
      <div className={styles.projectImageContainer}>
        <div
          className={styles.projectImage}
          style={{
            background: project.color || `linear-gradient(135deg, var(--primary-light), var(--primary-color), var(--primary-dark))`
          }}
        >
          {/* 项目图片占位符 */}
          <div className={styles.placeholder}>
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </div>
        </div>
        <div className={styles.projectOverlay}>
          <motion.div
            className={styles.viewProject}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            查看项目
          </motion.div>
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
    </motion.div>
  );
};

const FeaturedProjects: React.FC = () => {
  // 示例项目数据
  const projects: Project[] = [
    {
      id: 'project-1',
      title: '智能家居控制系统',
      description: '基于React和Node.js的智能家居控制平台，支持多设备管理和自动化场景设置',
      image: '/placeholder-project.jpg',
      tags: ['React', 'Node.js', 'IoT'],
      color: 'linear-gradient(135deg, #6a11cb, #2575fc)'
    },
    {
      id: 'project-2',
      title: '电子商务平台',
      description: '全栈电商网站，包含商品展示、购物车、支付集成和订单管理功能',
      image: '/placeholder-project.jpg',
      tags: ['Vue.js', 'Express', 'MongoDB'],
      color: 'linear-gradient(135deg, #f83600, #f9d423)'
    },
    {
      id: 'project-3',
      title: '数据可视化仪表板',
      description: '企业级数据分析和可视化平台，支持多种图表类型和实时数据更新',
      image: '/placeholder-project.jpg',
      tags: ['D3.js', 'TypeScript', 'GraphQL'],
      color: 'linear-gradient(135deg, #00b09b, #96c93d)'
    }
  ];

  const sectionRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(sectionRef, { once: true, amount: 0.1 });

  // 标题动画变体
  const titleVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: [0.16, 1, 0.3, 1]
      }
    }
  };

  // 按钮动画变体
  const buttonVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        delay: 0.6,
        ease: [0.16, 1, 0.3, 1]
      }
    }
  };

  return (
    <section id="projects" className={styles.featuredProjects} ref={sectionRef}>
      <motion.h2
        className={styles.sectionTitle}
        variants={titleVariants}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        精选项目
      </motion.h2>
      <div className={styles.projectsGrid}>
        {projects.map((project, index) => (
          <ProjectCard key={project.id} project={project} index={index} />
        ))}
      </div>
      <motion.div
        className={styles.viewAllContainer}
        variants={buttonVariants}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Link href="/projects" className={styles.viewAllButton}>
            查看更多项目
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.buttonIcon}>
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </Link>
        </motion.div>
      </motion.div>
    </section>
  );
};

export default FeaturedProjects;
