/**
 * SkillCategory.tsx
 *
 * 描述：技能分类组件，用于展示一个技能分类下的所有技能
 *
 * 功能：
 * - 展示技能分类标题和描述
 * - 网格布局展示技能卡片
 * - 支持滚动动画和交互效果
 * - 响应式设计适配不同设备
 *
 * 主要组件/接口：
 * - SkillCategory：技能分类组件
 * - SkillCategoryProps：组件属性接口
 *
 * 导出：
 * - SkillCategory 组件（默认导出）
 */

import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { SkillCategory as SkillCategoryType } from '@/config/skills';
import SkillCard from './SkillCard';
import styles from '@/styles/SkillCategory.module.css';

interface SkillCategoryProps {
  category: SkillCategoryType;
  index: number;
}

const SkillCategory: React.FC<SkillCategoryProps> = ({ category, index }) => {
  const [isVisible, setIsVisible] = useState(false);
  const categoryRef = useRef<HTMLDivElement>(null);

  // 使用 Intersection Observer 检测组件是否进入视口
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      {
        threshold: 0.2,
        rootMargin: '50px'
      }
    );

    if (categoryRef.current) {
      observer.observe(categoryRef.current);
    }

    return () => {
      if (categoryRef.current) {
        observer.unobserve(categoryRef.current);
      }
    };
  }, []);

  // 分类动画变体
  const categoryVariants = {
    hidden: { 
      opacity: 0, 
      y: 50 
    },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.6,
        delay: index * 0.2,
        ease: "easeOut"
      }
    }
  };

  // 标题动画变体
  const titleVariants = {
    hidden: { 
      opacity: 0, 
      x: -30 
    },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: {
        duration: 0.6,
        delay: index * 0.2 + 0.2,
        ease: "easeOut"
      }
    }
  };

  // 网格动画变体
  const gridVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.6,
        delay: index * 0.2 + 0.4,
        staggerChildren: 0.1
      }
    }
  };

  return (
    <motion.section
      ref={categoryRef}
      className={styles.skillCategory}
      variants={categoryVariants}
      initial="hidden"
      animate={isVisible ? "visible" : "hidden"}
    >
      {/* 分类头部 */}
      <motion.div 
        className={styles.categoryHeader}
        variants={titleVariants}
        initial="hidden"
        animate={isVisible ? "visible" : "hidden"}
      >
        <div className={styles.categoryIcon}>
          <span>{category.icon}</span>
        </div>
        <div className={styles.categoryInfo}>
          <h2 className={styles.categoryTitle}>{category.name}</h2>
          <p className={styles.categoryDescription}>{category.description}</p>
        </div>
        <div className={styles.categoryStats}>
          <span className={styles.skillCount}>
            {category.skills.length} 项技能
          </span>
        </div>
      </motion.div>

      {/* 技能网格 */}
      <motion.div
        className={styles.skillsGrid}
        variants={gridVariants}
        initial="hidden"
        animate={isVisible ? "visible" : "hidden"}
      >
        {category.skills.map((skill, skillIndex) => (
          <SkillCard
            key={skill.id}
            skill={skill}
            index={skillIndex}
            isVisible={isVisible}
          />
        ))}
      </motion.div>
    </motion.section>
  );
};

export default SkillCategory;
