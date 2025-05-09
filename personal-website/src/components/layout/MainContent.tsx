import React from 'react';
import { motion } from 'framer-motion';
import styles from '@/styles/MainContent.module.css';
import BriefIntro from '@/components/sections/BriefIntro';
import SkillsHighlight from '@/components/sections/SkillsHighlight';
import FeaturedProjects from '@/components/sections/FeaturedProjects';
import LatestPosts from '@/components/sections/LatestPosts';

interface MainContentProps {
  visible?: boolean;
}

const MainContent: React.FC<MainContentProps> = ({ visible = false }) => {
  // 定义动画变体
  const containerVariants = {
    hidden: {
      opacity: 0,
      y: 50
    },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.8,
        ease: [0.16, 1, 0.3, 1],
        when: "beforeChildren",
        staggerChildren: 0.2
      }
    }
  };

  const sectionVariants = {
    hidden: {
      opacity: 0,
      y: 30
    },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: [0.16, 1, 0.3, 1]
      }
    }
  };

  return (
    <motion.div
      className={styles.mainContent}
      initial="hidden"
      animate={visible ? "visible" : "hidden"}
      variants={containerVariants}
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
