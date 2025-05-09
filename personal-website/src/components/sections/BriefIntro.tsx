import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import styles from '@/styles/BriefIntro.module.css';
import ScrollAnimation from '@/components/common/ScrollAnimation';

const BriefIntro: React.FC = () => {
  return (
    <section id="about" className={styles.briefIntro}>
      <div className={styles.content}>
        <ScrollAnimation className={styles.textContent}>
          <motion.h2
            className={styles.sectionTitle}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          >
            关于我
          </motion.h2>
          <motion.p
            className={styles.description}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          >
            我是一名热衷于创造优质用户体验的全栈开发者。拥有多年的前后端开发经验，
            专注于构建高性能、可扩展的Web应用程序。我相信技术的力量在于解决实际问题，
            并且始终保持对新技术的学习热情。
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            <motion.div
              whileHover={{ scale: 1.05, x: 5 }}
              whileTap={{ scale: 0.95 }}
            >
              <Link href="/about" className={styles.moreButton}>
                了解更多
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.buttonIcon}>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
              </Link>
            </motion.div>
          </motion.div>
        </ScrollAnimation>
      </div>
    </section>
  );
};

export default BriefIntro;
