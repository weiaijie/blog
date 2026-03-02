/**
 * BriefIntro.tsx
 *
 * 描述：首页的简短个人介绍部分，展示个人简介和"了解更多"按钮
 *
 * 功能：
 * - 展示个人简介文本
 * - 提供"了解更多"按钮链接到详细的关于页面
 * - 使用滚动动画效果增强用户体验
 * - 使用Framer Motion实现平滑的动画效果
 *
 * 主要组件/接口：
 * - BriefIntro：简短个人介绍组件
 *
 * 导出：
 * - BriefIntro 组件（默认导出）
 */

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
            我是一名专注于前端技术的全栈开发工程师，拥有7年丰富的项目开发经验。
            深度掌握Vue生态系统，熟练运用TypeScript、JavaScript ES6+，精通主流UI框架。
            曾参与医疗SaaS、金融交易、建筑管理等多个行业的核心系统开发，具备全栈项目架构能力和团队技术指导经验。
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
