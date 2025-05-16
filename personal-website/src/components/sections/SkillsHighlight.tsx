/**
 * SkillsHighlight.tsx
 *
 * 描述：首页的技能亮点部分，展示个人主要技能和熟练度
 *
 * 功能：
 * - 展示主要技能类别（前端开发、后端开发、UI/UX设计、DevOps）
 * - 使用动画效果展示技能熟练度条
 * - 通过IntersectionObserver实现滚动时的技能条动画
 * - 提供"查看全部技能"按钮链接到详细的技能页面
 * - 支持技能卡片的翻转效果，显示详细信息
 * - 实现技能图标的动画效果
 * - 创建交互式技能图表
 *
 * 主要组件/接口：
 * - SkillsHighlight：技能亮点组件
 * - Skill：技能数据接口
 * - SkillCard：技能卡片组件
 *
 * 导出：
 * - SkillsHighlight 组件（默认导出）
 */

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { motion, useInView, AnimatePresence } from 'framer-motion';
import styles from '@/styles/SkillsHighlight.module.css';

interface Skill {
  name: string;
  description: string;
  level: number;
  icon: React.ReactNode;
  details?: string[];
  color?: string;
}

// 技能卡片组件
const SkillCard: React.FC<{ skill: Skill; index: number }> = ({ skill, index }) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(cardRef, { once: true, amount: 0.3 });

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
        delay: index * 0.2,
        ease: [0.16, 1, 0.3, 1]
      }
    }
  };

  // 图标动画变体
  const iconVariants = {
    initial: { scale: 1 },
    hover: {
      scale: 1.1,
      rotate: 5,
      transition: {
        duration: 0.3,
        ease: "easeInOut",
        yoyo: Infinity
      }
    }
  };

  // 技能条动画变体
  const barVariants = {
    hidden: { scaleX: 0 },
    visible: {
      scaleX: 1,
      transition: {
        duration: 1,
        delay: index * 0.2 + 0.5,
        ease: [0.16, 1, 0.3, 1]
      }
    }
  };

  // 翻转卡片
  const handleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  return (
    <motion.div
      ref={cardRef}
      className={styles.skillCardContainer}
      variants={cardVariants}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
    >
      <div className={`${styles.skillCard} ${isFlipped ? styles.flipped : ''}`}>
        {/* 卡片正面 */}
        <div className={styles.skillCardFront}>
          <motion.div
            className={styles.skillIcon}
            style={{ backgroundColor: `rgba(${skill.color || 'var(--primary-rgb)'}, 0.1)` }}
            variants={iconVariants}
            initial="initial"
            whileHover="hover"
          >
            {skill.icon}
          </motion.div>
          <h3 className={styles.skillName}>{skill.name}</h3>
          <p className={styles.skillDescription}>{skill.description}</p>
          <motion.div
            className={styles.skillBarContainer}
            variants={barVariants}
            initial="hidden"
            animate={isInView ? "visible" : "hidden"}
          >
            <div
              className={styles.skillBar}
              style={{
                width: `${skill.level}%`,
                backgroundColor: skill.color || 'var(--primary-color)'
              }}
            ></div>
            <span className={styles.skillLevel}>{skill.level}%</span>
          </motion.div>
          <motion.button
            className={styles.flipButton}
            onClick={handleFlip}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            查看详情
          </motion.button>
        </div>

        {/* 卡片背面 */}
        <div className={styles.skillCardBack}>
          <h3 className={styles.skillName}>{skill.name} 详情</h3>
          <ul className={styles.skillDetailsList}>
            {skill.details?.map((detail, idx) => (
              <li key={idx} className={styles.skillDetailItem}>
                {detail}
              </li>
            ))}
          </ul>
          <motion.button
            className={styles.flipButton}
            onClick={handleFlip}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            返回
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
};

const SkillsHighlight: React.FC = () => {
  const skillsRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(skillsRef, { once: true, amount: 0.1 });

  // 技能列表
  const skills: Skill[] = [
    {
      name: "前端开发",
      description: "精通HTML5, CSS3, JavaScript/TypeScript, React, Vue等现代前端技术",
      level: 90,
      color: "65, 105, 225", // 蓝色
      details: [
        "精通React和Vue框架，构建响应式用户界面",
        "熟练使用TypeScript进行类型安全的开发",
        "掌握现代CSS技术，包括Flexbox、Grid和动画",
        "了解前端性能优化和最佳实践"
      ],
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"></polygon>
          <line x1="12" y1="22" x2="12" y2="15.5"></line>
          <polyline points="22 8.5 12 15.5 2 8.5"></polyline>
          <polyline points="2 15.5 12 8.5 22 15.5"></polyline>
          <line x1="12" y1="2" x2="12" y2="8.5"></line>
        </svg>
      )
    },
    {
      name: "后端开发",
      description: "熟练使用Node.js, Express, Python, Django等构建高效的服务端应用",
      level: 80,
      color: "46, 139, 87", // 绿色
      details: [
        "熟练使用Node.js和Express构建RESTful API",
        "了解Python和Django框架开发",
        "掌握数据库设计和优化技术",
        "具备服务器端性能调优经验"
      ],
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
          <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
          <line x1="6" y1="6" x2="6.01" y2="6"></line>
          <line x1="6" y1="18" x2="6.01" y2="18"></line>
        </svg>
      )
    },
    {
      name: "UI/UX设计",
      description: "了解设计原则和用户体验最佳实践，能够创建直观美观的界面",
      level: 75,
      color: "218, 112, 214", // 紫色
      details: [
        "掌握用户界面设计原则和最佳实践",
        "了解用户体验研究和测试方法",
        "能够使用设计工具创建原型和界面",
        "关注可访问性和包容性设计"
      ],
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <circle cx="12" cy="12" r="4"></circle>
          <line x1="21.17" y1="8" x2="12" y2="8"></line>
          <line x1="3.95" y1="6.06" x2="8.54" y2="14"></line>
          <line x1="10.88" y1="21.94" x2="15.46" y2="14"></line>
        </svg>
      )
    },
    {
      name: "DevOps",
      description: "熟悉Git, Docker, CI/CD流程，能够实现自动化部署和维护",
      level: 70,
      color: "255, 140, 0", // 橙色
      details: [
        "熟练使用Git进行版本控制和协作开发",
        "了解Docker容器化技术和微服务架构",
        "掌握CI/CD流程和自动化部署工具",
        "具备基本的服务器管理和监控经验"
      ],
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
        </svg>
      )
    }
  ];

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
        delay: 0.8,
        ease: [0.16, 1, 0.3, 1]
      }
    }
  };

  return (
    <section id="skills" className={styles.skillsHighlight} ref={skillsRef}>
      <motion.h2
        className={styles.sectionTitle}
        variants={titleVariants}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        技能亮点
      </motion.h2>
      <div className={styles.skillsGrid}>
        {skills.map((skill, index) => (
          <SkillCard key={index} skill={skill} index={index} />
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
          <Link href="/skills" className={styles.viewAllButton}>
            查看全部技能
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

export default SkillsHighlight;
