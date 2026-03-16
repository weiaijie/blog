import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import styles from '@/styles/SkillsHighlight.module.css';
import ScrollAnimation from '@/components/common/ScrollAnimation';
import siteConfig from '@/config/site';

const SkillsHighlight: React.FC = () => {
  return (
    <section id="skills" className={styles.skillsHighlight}>
      <div className={styles.content}>
        <ScrollAnimation className={styles.textContent}>
          <motion.h2
            className={styles.sectionTitle}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          >
            技能亮点
          </motion.h2>
          <motion.div
            className={styles.groupList}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          >
            {siteConfig.profile.skillGroups.map((group) => (
              <p key={group.title} className={styles.description}>
                <strong className={styles.groupTitle}>{group.title}：</strong>
                {group.items.join('、')}
              </p>
            ))}
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            <motion.div whileHover={{ scale: 1.05, x: 5 }} whileTap={{ scale: 0.95 }}>
              <Link href="/skills" className={styles.moreButton}>
                查看全部技能
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className={styles.buttonIcon}
                >
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

export default SkillsHighlight;
