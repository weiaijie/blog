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
import { motion, AnimatePresence } from 'framer-motion';
import styles from '@/styles/Tagline.module.css';
import Typewriter from '@/components/common/Typewriter';

interface TaglineProps {
  visible: boolean; // 控制是否显示
}

const Tagline: React.FC<TaglineProps> = ({ visible }) => {
  const prevVisibleRef = useRef(visible);

  // 定义动画变体 - 进一步优化过渡效果，避免影响滚动和页面跳动
  const containerVariants = {
    hidden: {
      opacity: 0,
      y: 0, // 不使用垂直位移，只使用透明度变化
      transition: {
        duration: 0.4,
        ease: "easeInOut"
      }
    },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4, // 进一步缩短动画时间
        ease: "easeInOut",
        when: "beforeChildren",
        staggerChildren: 0.05 // 减少子元素动画间隔
      }
    },
    exit: {
      opacity: 0,
      y: 0, // 不使用垂直位移，只使用透明度变化
      transition: {
        duration: 0.3,
        ease: "easeInOut"
      }
    }
  };

  // 更新visible状态引用，但不再尝试手动管理滚动位置
  useEffect(() => {
    prevVisibleRef.current = visible;
  }, [visible]);

  const childVariants = {
    hidden: { opacity: 0, y: 10 }, // 减小位移距离
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.3, // 缩短动画时间
        ease: "easeOut"
      }
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
          layout={false} // 防止布局变化
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            pointerEvents: visible ? 'auto' : 'none'
          }}
        >
          <div className={styles.taglineContent}>
        <motion.div className={styles.taglineMain} variants={childVariants}>
          <motion.h2 className={styles.taglineHeading} variants={childVariants}>
            <Typewriter
              texts={['创造优雅的数字体验', '构建直观的用户界面', '开发高效的应用程序']}
              typingSpeed={80}
              deletingSpeed={40}
              delayAfterType={3000}
            />
          </motion.h2>
          <motion.p className={styles.taglineSubheading} variants={childVariants}>
            <span className={styles.taglineHighlight}>全栈开发</span>，专注于构建直观、高效且美观的用户界面
          </motion.p>
          <motion.div className={styles.taglineActions} variants={childVariants}>
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Link href="/projects" className={styles.taglinePrimaryButton}>
                查看作品
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.taglineButtonIcon}>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
              </Link>
            </motion.div>
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Link href="/contact" className={styles.taglineSecondaryButton}>
                联系我
              </Link>
            </motion.div>
          </motion.div>
        </motion.div>
        <motion.div
          className={styles.taglineVisual}
          variants={childVariants}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{
            duration: 0.8,
            delay: 0.3,
            ease: [0.16, 1, 0.3, 1]
          }}
        >
          <motion.div
            className={styles.taglineImageContainer}
            whileHover={{
              scale: 1.05,
              boxShadow: "0 15px 30px rgba(0, 0, 0, 0.15)"
            }}
            transition={{ duration: 0.3 }}
          >
            <motion.div
              className={styles.taglineImage}
              // 不再使用硬编码的颜色值，而是使用CSS变量
              // 动画效果通过CSS类和opacity变化实现
              animate={{
                opacity: [0.9, 1, 0.9]
              }}
              transition={{
                duration: 5,
                repeat: Infinity,
                repeatType: "reverse"
              }}
            ></motion.div>
          </motion.div>
        </motion.div>
      </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default Tagline;
