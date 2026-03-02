/**
 * ReadingProgress.tsx
 *
 * 描述：阅读进度指示器组件
 *
 * 功能：
 * - 显示文章阅读进度条
 * - 计算阅读时间和剩余时间
 * - 提供平滑的进度动画
 * - 支持主题切换
 * - 响应式设计
 *
 * 主要接口：
 * - ReadingProgressProps：组件属性接口
 * - ReadingProgress：阅读进度组件
 */

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import styles from '@/styles/ReadingProgress.module.css';

interface ReadingProgressProps {
  target?: string; // 目标元素选择器，默认为文章内容
  showTimeEstimate?: boolean; // 是否显示时间估计
  position?: 'top' | 'bottom' | 'fixed'; // 进度条位置
  className?: string;
}

export default function ReadingProgress({
  target = '.blog-content',
  showTimeEstimate = true,
  position = 'fixed',
  className = ''
}: ReadingProgressProps) {
  const [progress, setProgress] = useState(0);
  const [timeEstimate, setTimeEstimate] = useState({ read: 0, remaining: 0 });
  const [isVisible, setIsVisible] = useState(false);
  const progressRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const targetElement = document.querySelector(target);
    if (!targetElement) return;

    // 计算阅读时间（基于平均阅读速度 200字/分钟）
    const calculateReadingTime = (text: string) => {
      const wordsPerMinute = 200;
      const words = text.length;
      const minutes = words / wordsPerMinute;
      return Math.ceil(minutes);
    };

    const totalReadingTime = calculateReadingTime(targetElement.textContent || '');

    const updateProgress = () => {
      const targetRect = targetElement.getBoundingClientRect();
      const targetHeight = targetElement.offsetHeight;
      const windowHeight = window.innerHeight;
      
      // 计算滚动进度
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const targetTop = targetElement.offsetTop;
      
      // 开始阅读的位置（目标元素顶部进入视口）
      const startReading = targetTop - windowHeight;
      // 结束阅读的位置（目标元素底部离开视口）
      const endReading = targetTop + targetHeight;
      
      // 计算当前阅读进度
      const currentProgress = Math.max(0, Math.min(100, 
        ((scrollTop - startReading) / (endReading - startReading)) * 100
      ));
      
      setProgress(currentProgress);
      
      // 显示/隐藏进度条
      setIsVisible(currentProgress > 0 && currentProgress < 100);
      
      // 计算时间估计
      if (showTimeEstimate) {
        const readTime = Math.round((currentProgress / 100) * totalReadingTime);
        const remainingTime = Math.max(0, totalReadingTime - readTime);
        setTimeEstimate({ read: readTime, remaining: remainingTime });
      }
    };

    // 节流函数
    let ticking = false;
    const throttledUpdate = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          updateProgress();
          ticking = false;
        });
        ticking = true;
      }
    };

    // 初始计算
    updateProgress();

    // 监听滚动事件
    window.addEventListener('scroll', throttledUpdate, { passive: true });
    window.addEventListener('resize', throttledUpdate, { passive: true });

    return () => {
      window.removeEventListener('scroll', throttledUpdate);
      window.removeEventListener('resize', throttledUpdate);
    };
  }, [target, showTimeEstimate]);

  // 动画变体
  const progressVariants = {
    hidden: { 
      opacity: 0, 
      y: position === 'top' ? -20 : 20 
    },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.3,
        ease: "easeOut"
      }
    }
  };

  const barVariants = {
    initial: { width: 0 },
    animate: { 
      width: `${progress}%`,
      transition: {
        duration: 0.1,
        ease: "easeOut"
      }
    }
  };

  if (!isVisible) return null;

  return (
    <motion.div
      ref={progressRef}
      className={`${styles.readingProgress} ${styles[position]} ${className}`}
      variants={progressVariants}
      initial="hidden"
      animate="visible"
      exit="hidden"
    >
      {/* 进度条背景 */}
      <div className={styles.progressBackground}>
        {/* 进度条 */}
        <motion.div
          className={styles.progressBar}
          variants={barVariants}
          initial="initial"
          animate="animate"
        />
      </div>

      {/* 时间估计 */}
      {showTimeEstimate && (
        <div className={styles.timeEstimate}>
          <span className={styles.readTime}>
            已读 {timeEstimate.read} 分钟
          </span>
          {timeEstimate.remaining > 0 && (
            <span className={styles.remainingTime}>
              还需 {timeEstimate.remaining} 分钟
            </span>
          )}
        </div>
      )}

      {/* 进度百分比 */}
      <div className={styles.progressPercent}>
        {Math.round(progress)}%
      </div>
    </motion.div>
  );
}
