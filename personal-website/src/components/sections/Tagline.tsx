import React from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import styles from '@/styles/Tagline.module.css';
import Typewriter from '@/components/common/Typewriter';

interface TaglineProps {
  visible: boolean; // 控制是否显示
}

const Tagline: React.FC<TaglineProps> = ({ visible }) => {
  // 定义动画变体
  const containerVariants = {
    hidden: {
      opacity: 0,
      y: -50
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
    },
    exit: {
      opacity: 0,
      y: -30,
      transition: {
        duration: 0.5,
        ease: [0.16, 1, 0.3, 1]
      }
    }
  };

  const childVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: [0.16, 1, 0.3, 1]
      }
    }
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className={styles.tagline}
          initial="hidden"
          animate="visible"
          exit="exit"
          variants={containerVariants}
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
              animate={{
                background: [
                  "linear-gradient(135deg, #42a5f5, #2196f3, #1976d2)",
                  "linear-gradient(135deg, #4dabf5, #2196f3, #2180d2)",
                  "linear-gradient(135deg, #42a5f5, #2196f3, #1976d2)"
                ]
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
