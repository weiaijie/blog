/**
 * Tagline.tsx
 *
 * 描述：网站标语组件，展示在首页顶部的主要宣传语和行动按钮
 *
 * 功能：
 * - 展示网站的主要标语和副标语
 * - 使用打字机效果展示多个标语文本
 * - 提供"查看作品"和"联系我"的行动按钮
 * - 支持平滑的显示/隐藏动画效果
 * - 响应滚动事件，在向下滚动时隐藏
 *
 * 主要组件/接口：
 * - Tagline：标语组件
 * - TaglineProps：组件属性接口
 *
 * 导出：
 * - Tagline 组件（默认导出）
 */

import React, { useEffect, useRef } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence, type Variants } from 'framer-motion';
import styles from '@/styles/Tagline.module.css';
import siteConfig from '@/config/site';

interface TaglineProps {
  visible: boolean; // 控制是否显示
}

const Tagline: React.FC<TaglineProps> = ({ visible }) => {
  const prevVisibleRef = useRef(visible);

  // 定义动画变体
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.4,
        ease: "easeInOut",
        when: "beforeChildren",
        staggerChildren: 0.05
      }
    },
    exit: {
      opacity: 0,
      transition: { duration: 0.3 }
    }
  };

  useEffect(() => {
    prevVisibleRef.current = visible;
  }, [visible]);

  const childVariants: Variants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.3, ease: "easeOut" }
    }
  };

  return (
    <AnimatePresence mode="sync">
      {visible && (
        <motion.div
          className={styles.tagline}
          initial="hidden"
          animate="visible"
          exit="exit"
          variants={containerVariants}
          layout={false}
          style={{ pointerEvents: visible ? 'auto' : 'none' }}
        >
          <div className={styles.taglineContent}>
            <motion.div className={styles.taglineMain} variants={childVariants}>
              <motion.h1 className={styles.taglineHeading} variants={childVariants}>
                {siteConfig.author} <span className={styles.taglineRole}>/ 全栈开发工程师</span>
              </motion.h1>
              <motion.div className={styles.taglineSubheading} variants={childVariants}>
                <p>{siteConfig.profile.aboutIntro[0]}</p>
                <p>{siteConfig.profile.aboutIntro[3]}</p>
              </motion.div>
              <motion.div className={styles.taglineActions} variants={childVariants}>
                <Link href="/projects" className={styles.taglinePrimaryButton}>
                  查看作品
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.taglineButtonIcon}>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                  </svg>
                </Link>
                <Link href="/contact" className={styles.taglineSecondaryButton}>
                  联系我
                </Link>
              </motion.div>
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default Tagline;
