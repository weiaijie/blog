import React, { useEffect, useRef } from 'react';
import { motion, useAnimation } from 'framer-motion';
import styles from '@/styles/MainContent.module.css';
import BriefIntro from '@/components/sections/BriefIntro';
import SkillsHighlight from '@/components/sections/SkillsHighlight';
import FeaturedProjects from '@/components/sections/FeaturedProjects';
import LatestPosts from '@/components/sections/LatestPosts';

interface MainContentProps {
  visible?: boolean;
}

const MainContent: React.FC<MainContentProps> = ({ visible = false }) => {
  // 使用动画控制器
  const controls = useAnimation();
  // 跟踪是否已经显示过内容
  const hasAnimated = useRef(false);

  // 定义动画变体 - 优化以避免闪烁
  const containerVariants = {
    hidden: {
      opacity: 0,
      y: 20 // 减小位移距离
    },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6, // 缩短动画时间
        ease: [0.16, 1, 0.3, 1],
        when: "beforeChildren",
        staggerChildren: 0.1 // 减少子元素动画间隔
      }
    },
    stable: { // 新增稳定状态，用于内容已显示后
      opacity: 1,
      y: 0
    }
  };

  const sectionVariants = {
    hidden: {
      opacity: 0,
      y: 15 // 减小位移距离
    },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4, // 缩短动画时间
        ease: [0.16, 1, 0.3, 1]
      }
    },
    stable: { // 新增稳定状态
      opacity: 1,
      y: 0
    }
  };

  // 监听可见性变化
  useEffect(() => {
    if (visible) {
      // 如果内容变为可见，执行动画
      controls.start("visible").then(() => {
        // 动画完成后，标记为已动画
        hasAnimated.current = true;
        // 切换到稳定状态，防止再次触发动画
        controls.start("stable");
      });
    } else if (!hasAnimated.current) {
      // 只有在尚未显示过的情况下才隐藏
      controls.start("hidden");
    }
    // 如果已经显示过，即使visible变为false也保持稳定状态
  }, [visible, controls]);

  return (
    <motion.div
      className={styles.mainContent}
      initial="hidden"
      animate={controls}
      variants={containerVariants}
      style={{ willChange: "opacity, transform" }} // 优化性能
    >
      <div className={styles.container}>
        <motion.div variants={sectionVariants}>
          <BriefIntro />
        </motion.div>
        <motion.div variants={sectionVariants}>
          <SkillsHighlight />
        </motion.div>
        <motion.div variants={sectionVariants}>
          <FeaturedProjects />
        </motion.div>
        <motion.div variants={sectionVariants}>
          <LatestPosts />
        </motion.div>
      </div>
    </motion.div>
  );
};

export default MainContent;
