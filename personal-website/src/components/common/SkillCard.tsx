/**
 * SkillCard.tsx
 *
 * 描述：技能卡片组件，用于展示单个技能的详细信息
 *
 * 功能：
 * - 展示技能名称、熟练度和描述
 * - 动画进度条显示技能水平
 * - 支持悬停效果和交互动画
 * - 显示相关技术栈和项目
 *
 * 主要组件/接口：
 * - SkillCard：技能卡片组件
 * - SkillCardProps：组件属性接口
 *
 * 导出：
 * - SkillCard 组件（默认导出）
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { SkillItem, getSkillStars, getSkillLevelText } from '@/config/skills';
import styles from '@/styles/SkillCard.module.css';

interface SkillCardProps {
  skill: SkillItem;
  index: number;
  isVisible?: boolean;
}

const SkillCard: React.FC<SkillCardProps> = ({ skill, index, isVisible = false }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // 卡片动画变体
  const cardVariants = {
    hidden: { 
      opacity: 0, 
      y: 30,
      scale: 0.9
    },
    visible: { 
      opacity: 1, 
      y: 0,
      scale: 1,
      transition: {
        duration: 0.6,
        delay: index * 0.1,
        ease: "easeOut"
      }
    }
  };

  // 进度条动画变体
  const progressVariants = {
    hidden: { width: 0 },
    visible: { 
      width: `${skill.percentage}%`,
      transition: {
        duration: 1.2,
        delay: index * 0.1 + 0.3,
        ease: "easeOut"
      }
    }
  };

  // 展开内容动画变体
  const expandVariants = {
    collapsed: { 
      height: 0,
      opacity: 0,
      transition: {
        duration: 0.3,
        ease: "easeInOut"
      }
    },
    expanded: { 
      height: "auto",
      opacity: 1,
      transition: {
        duration: 0.3,
        ease: "easeInOut"
      }
    }
  };

  return (
    <motion.div
      className={styles.skillCard}
      variants={cardVariants}
      initial="hidden"
      animate={isVisible ? "visible" : "hidden"}
      whileHover={{ 
        y: -8,
        boxShadow: "0 12px 40px rgba(0, 0, 0, 0.15)"
      }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      {/* 技能图标和颜色装饰 */}
      <div 
        className={styles.skillIcon}
        style={{ backgroundColor: skill.color || '#6366f1' }}
      >
        <span>{skill.icon || '🔧'}</span>
      </div>

      {/* 技能头部信息 */}
      <div className={styles.skillHeader}>
        <div className={styles.skillInfo}>
          <h3 className={styles.skillName}>{skill.name}</h3>
          <div className={styles.skillMeta}>
            <span className={styles.skillLevel}>
              {getSkillStars(skill.level)}
            </span>
            <span className={styles.skillLevelText}>
              {getSkillLevelText(skill.level)}
            </span>
            <span className={styles.skillPercentage}>
              {skill.percentage}%
            </span>
          </div>
        </div>
        
        <motion.button
          className={styles.expandButton}
          onClick={() => setIsExpanded(!isExpanded)}
          whileTap={{ scale: 0.95 }}
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.3 }}
        >
          ▼
        </motion.button>
      </div>

      {/* 进度条 */}
      <div className={styles.progressContainer}>
        <div className={styles.progressTrack}>
          <motion.div
            className={styles.progressBar}
            style={{ backgroundColor: skill.color || '#6366f1' }}
            variants={progressVariants}
            initial="hidden"
            animate={isVisible ? "visible" : "hidden"}
          />
        </div>
      </div>

      {/* 技能描述 */}
      <p className={styles.skillDescription}>
        {skill.description}
      </p>

      {/* 展开的详细信息 */}
      <motion.div
        className={styles.expandedContent}
        variants={expandVariants}
        initial="collapsed"
        animate={isExpanded ? "expanded" : "collapsed"}
      >
        {skill.technologies && skill.technologies.length > 0 && (
          <div className={styles.technologiesSection}>
            <h4 className={styles.sectionTitle}>相关技术</h4>
            <div className={styles.technologiesList}>
              {skill.technologies.map((tech, techIndex) => (
                <motion.span
                  key={tech}
                  className={styles.technologyTag}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: techIndex * 0.05 }}
                >
                  {tech}
                </motion.span>
              ))}
            </div>
          </div>
        )}

        {skill.projects && skill.projects.length > 0 && (
          <div className={styles.projectsSection}>
            <h4 className={styles.sectionTitle}>相关项目</h4>
            <ul className={styles.projectsList}>
              {skill.projects.map((project, projectIndex) => (
                <motion.li
                  key={project}
                  className={styles.projectItem}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: projectIndex * 0.1 }}
                >
                  {project}
                </motion.li>
              ))}
            </ul>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
};

export default SkillCard;
