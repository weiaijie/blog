/**
 * Timeline.tsx
 *
 * 描述：时间线组件，用于展示教育背景、工作经历等时间序列信息
 *
 * 功能：
 * - 支持多种时间线项目类型
 * - 提供动画效果和交互反馈
 * - 响应式设计，适配不同设备
 * - 支持自定义图标和样式
 *
 * 主要组件/接口：
 * - Timeline：时间线容器组件
 * - TimelineItem：时间线项目组件
 * - TimelineItemProps：时间线项目属性接口
 *
 * 导出：
 * - Timeline 组件（默认导出）
 * - TimelineItem 组件
 */

import React from 'react';
import { motion } from 'framer-motion';
import styles from '@/styles/Timeline.module.css';

// 时间线项目数据接口
export interface TimelineItemData {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  date: string;
  icon?: React.ReactNode;
  type?: 'education' | 'work' | 'achievement' | 'default';
}

// 时间线项目组件属性
interface TimelineItemProps {
  item: TimelineItemData;
  index: number;
  isLast?: boolean;
}

// 时间线组件属性
interface TimelineProps {
  items: TimelineItemData[];
  className?: string;
}

// 动画变体
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { 
    opacity: 0, 
    x: -50,
    scale: 0.9
  },
  visible: { 
    opacity: 1, 
    x: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 15,
      duration: 0.6
    }
  }
};

// 时间线项目组件
const TimelineItem: React.FC<TimelineItemProps> = ({ item, index, isLast = false }) => {
  const getTypeIcon = () => {
    switch (item.type) {
      case 'education':
        return '🎓';
      case 'work':
        return '💼';
      case 'achievement':
        return '🏆';
      default:
        return '📍';
    }
  };

  return (
    <motion.div
      className={`${styles.timelineItem} ${isLast ? styles.lastItem : ''}`}
      variants={itemVariants}
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 17 }}
      role="listitem"
      aria-label={`${item.title} - ${item.date}`}
    >
      <div className={styles.timelineDot}>
        <span className={styles.timelineIcon}>
          {item.icon || getTypeIcon()}
        </span>
      </div>
      
      <motion.div 
        className={styles.timelineContent}
        whileHover={{ 
          boxShadow: "0 8px 30px rgba(0, 0, 0, 0.12)",
          y: -2
        }}
        transition={{ duration: 0.3 }}
      >
        <div className={styles.timelineHeader}>
          <h3 className={styles.timelineTitle}>{item.title}</h3>
          <span className={styles.timelineDate}>{item.date}</span>
        </div>
        <p className={styles.timelineSubtitle}>{item.subtitle}</p>
        <p className={styles.timelineDescription}>{item.description}</p>
      </motion.div>
    </motion.div>
  );
};

// 主时间线组件
const Timeline: React.FC<TimelineProps> = ({ items, className = '' }) => {
  return (
    <motion.div
      className={`${styles.timeline} ${className}`}
      variants={containerVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
      role="list"
      aria-label="时间线"
    >
      {items.map((item, index) => (
        <TimelineItem 
          key={item.id}
          item={item}
          index={index}
          isLast={index === items.length - 1}
        />
      ))}
    </motion.div>
  );
};

export default Timeline;
export { TimelineItem };
