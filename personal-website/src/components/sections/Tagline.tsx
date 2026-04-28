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
import Typewriter from '@/components/common/Typewriter';
import siteConfig from '@/config/site';

interface TaglineProps {
  visible: boolean; // 控制是否显示
}

const Tagline: React.FC<TaglineProps> = ({ visible }) => {
  const prevVisibleRef = useRef(visible);
  const codeSnippets = [
    "const focus = 'Enterprise Systems';",
    "const stack = ['Vue', 'React', 'Node.js'];",
    "export const build = () => createProduct(focus, stack);",
  ];

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
              <motion.div className={styles.taglineEyebrow} variants={childVariants}>
                Shanghai-ready / Remote-friendly / AI-assisted delivery
              </motion.div>
              <motion.h1 className={styles.taglineHeading} variants={childVariants}>
                <span className={styles.taglineName}>{siteConfig.author}</span>
                <span className={styles.taglineRole}>{siteConfig.profile.heroRole}</span>
              </motion.h1>
              <motion.div className={styles.taglineSubheading} variants={childVariants}>
                {siteConfig.profile.heroSummary.map((line) => (
                  <p key={line}>{line}</p>
                ))}
              </motion.div>
              <motion.div className={styles.taglineSignals} variants={childVariants}>
                <span>企业后台</span>
                <span>小程序交付</span>
                <span>系统对接</span>
                <span>长期维护</span>
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
            <motion.div
              className={styles.taglineVisual}
              variants={childVariants}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
            >
              <div className={styles.codePanel}>
                <div className={styles.codePanelHeader}>
                  <span className={styles.codePanelTitle}>developer.ts</span>
                </div>
                <div className={styles.codePanelBody}>
                  <div className={styles.codeLine}>
                    <span className={styles.lineNumber}>1</span>
                    <span className={styles.lineContent}>
                      <span className={styles.codeKeyword}>import</span>{' '}
                      <span className={styles.codeIdentifier}>createProduct</span>{' '}
                      <span className={styles.codeKeyword}>from</span>{' '}
                      <span className={styles.codeString}>'@/core/engineering'</span>
                    </span>
                  </div>
                  <div className={styles.codeLine}>
                    <span className={styles.lineNumber}>2</span>
                    <span className={styles.lineContent}></span>
                  </div>
                  <div className={styles.codeLine}>
                    <span className={styles.lineNumber}>3</span>
                    <span className={styles.lineContent}>
                      <Typewriter
                        texts={codeSnippets}
                        typingSpeed={38}
                        deletingSpeed={18}
                        delayAfterType={999999}
                        delayAfterDelete={500}
                        loop={false}
                        className={styles.codeTyping}
                      />
                    </span>
                  </div>
                  <div className={styles.codeLine}>
                    <span className={styles.lineNumber}>4</span>
                    <span className={styles.lineContent}>
                      <span className={styles.codeKeyword}>if</span> (
                      <span className={styles.codeIdentifier}>business</span>.
                      <span className={styles.codeProperty}>isComplex</span>) {'{'}
                    </span>
                  </div>
                  <div className={styles.codeLine}>
                    <span className={styles.lineNumber}>5</span>
                    <span className={styles.lineContent}>
                      &nbsp;&nbsp;<span className={styles.codeKeyword}>return</span>{' '}
                      <span className={styles.codeIdentifier}>build</span>()
                    </span>
                  </div>
                  <div className={styles.codeLine}>
                    <span className={styles.lineNumber}>6</span>
                    <span className={styles.lineContent}>{'}'}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default Tagline;
