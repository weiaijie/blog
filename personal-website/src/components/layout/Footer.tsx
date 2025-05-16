/**
 * Footer.tsx
 *
 * 描述：网站页脚组件，采用苹果风格设计，包含导航链接、法律信息和版权声明
 *
 * 功能：
 * - 提供多列导航链接布局
 * - 显示社交媒体链接和联系方式
 * - 显示版权信息和法律声明
 * - 支持亮色/暗色主题模式
 * - 响应式设计，适配不同设备尺寸
 *
 * 主要组件/接口：
 * - Footer：页脚组件
 * - FooterProps：组件属性接口
 *
 * 导出：
 * - Footer 组件（默认导出）
 */

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { motion, AnimatePresence } from 'framer-motion';
import { socialLinks, footerNavRoutes } from '@/config/routes';
import styles from '@/styles/Footer.module.css';
import { useTheme } from '@/contexts/ThemeContext';

interface FooterProps {}

const Footer: React.FC<FooterProps> = () => {
  const router = useRouter();
  const { theme } = useTheme();
  const currentYear = new Date().getFullYear();
  const [isMobile, setIsMobile] = useState(false);
  const [expandedSections, setExpandedSections] = useState<{[key: string]: boolean}>({
    navigation: false,
    about: false,
    contact: false
  });

  // 检测是否为移动设备
  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth <= 833);
    };

    // 初始检查
    checkIfMobile();

    // 监听窗口大小变化
    window.addEventListener('resize', checkIfMobile);

    // 清理函数
    return () => window.removeEventListener('resize', checkIfMobile);
  }, []);

  // 切换展开/折叠状态
  const toggleSection = (section: string) => {
    if (isMobile) {
      setExpandedSections(prev => ({
        ...prev,
        [section]: !prev[section]
      }));
    }
  };

  // 社交媒体图标
  const socialIcons = {
    GitHub: (
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
      </svg>
    ),
    LinkedIn: (
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
        <rect x="2" y="9" width="4" height="12"></rect>
        <circle cx="4" cy="4" r="2"></circle>
      </svg>
    ),
    Twitter: (
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path>
      </svg>
    )
  };

  // 箭头图标 - 用于移动端展开/折叠指示
  const ChevronIcon = ({ isExpanded }: { isExpanded: boolean }) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="12"
      height="12"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`${styles.chevronIcon} ${isExpanded ? styles.expanded : ''}`}
    >
      <polyline points="6 9 12 15 18 9"></polyline>
    </svg>
  );

  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        {/* 页脚主要内容 - 多列导航 */}
        <div className={styles.footerDirectory}>
          {/* 第一列 - 导航链接 */}
          <div className={styles.directoryColumn}>
            <h3
              className={`${styles.directoryTitle} ${isMobile ? styles.toggleable : ''}`}
              onClick={() => toggleSection('navigation')}
              aria-expanded={expandedSections.navigation}
            >
              导航
              {isMobile && <ChevronIcon isExpanded={expandedSections.navigation} />}
            </h3>
            <AnimatePresence mode="sync">
              {(!isMobile || expandedSections.navigation) && (
                <motion.ul
                  className={styles.directoryList}
                  initial={isMobile ? { height: 0, opacity: 0, y: -10 } : { opacity: 1 }}
                  animate={isMobile ? { height: 'auto', opacity: 1, y: 0 } : { opacity: 1 }}
                  exit={isMobile ? { height: 0, opacity: 0, y: -10 } : { opacity: 1 }}
                  transition={{
                    height: { duration: 0.3, ease: [0.33, 1, 0.68, 1] },
                    opacity: { duration: 0.2, ease: "easeOut" },
                    y: { duration: 0.2, ease: "easeOut" }
                  }}
                  layout="position"
                  style={{ willChange: "opacity, height, transform" }}
                >
                  {footerNavRoutes.slice(0, 6).map((route, index) => (
                    <motion.li
                      key={route.path}
                      className={styles.directoryItem}
                      initial={isMobile ? { opacity: 0, y: -5 } : { opacity: 1 }}
                      animate={isMobile ? { opacity: 1, y: 0 } : { opacity: 1 }}
                      transition={{
                        delay: isMobile ? index * 0.05 : 0,
                        duration: 0.2
                      }}
                    >
                      <Link
                        href={route.path}
                        className={router.pathname === route.path ? styles.active : ''}
                      >
                        {route.name}
                      </Link>
                    </motion.li>
                  ))}
                </motion.ul>
              )}
            </AnimatePresence>
          </div>

          {/* 第二列 - 关于和法律 */}
          <div className={styles.directoryColumn}>
            <h3
              className={`${styles.directoryTitle} ${isMobile ? styles.toggleable : ''}`}
              onClick={() => toggleSection('about')}
              aria-expanded={expandedSections.about}
            >
              关于
              {isMobile && <ChevronIcon isExpanded={expandedSections.about} />}
            </h3>
            <AnimatePresence mode="sync">
              {(!isMobile || expandedSections.about) && (
                <motion.ul
                  className={styles.directoryList}
                  initial={isMobile ? { height: 0, opacity: 0, y: -10 } : { opacity: 1 }}
                  animate={isMobile ? { height: 'auto', opacity: 1, y: 0 } : { opacity: 1 }}
                  exit={isMobile ? { height: 0, opacity: 0, y: -10 } : { opacity: 1 }}
                  transition={{
                    height: { duration: 0.3, ease: [0.33, 1, 0.68, 1] },
                    opacity: { duration: 0.2, ease: "easeOut" },
                    y: { duration: 0.2, ease: "easeOut" }
                  }}
                  layout="position"
                  style={{ willChange: "opacity, height, transform" }}
                >
                  {[
                    { name: "关于我", path: "/about" },
                    { name: "隐私政策", path: "/privacy" },
                    { name: "使用条款", path: "/terms" }
                  ].map((item, index) => (
                    <motion.li
                      key={item.path}
                      className={styles.directoryItem}
                      initial={isMobile ? { opacity: 0, y: -5 } : { opacity: 1 }}
                      animate={isMobile ? { opacity: 1, y: 0 } : { opacity: 1 }}
                      transition={{
                        delay: isMobile ? index * 0.05 : 0,
                        duration: 0.2
                      }}
                    >
                      <Link href={item.path}>{item.name}</Link>
                    </motion.li>
                  ))}
                </motion.ul>
              )}
            </AnimatePresence>
          </div>

          {/* 第三列 - 联系方式 */}
          <div className={styles.directoryColumn}>
            <h3
              className={`${styles.directoryTitle} ${isMobile ? styles.toggleable : ''}`}
              onClick={() => toggleSection('contact')}
              aria-expanded={expandedSections.contact}
            >
              联系
              {isMobile && <ChevronIcon isExpanded={expandedSections.contact} />}
            </h3>
            <AnimatePresence mode="sync">
              {(!isMobile || expandedSections.contact) && (
                <motion.ul
                  className={styles.directoryList}
                  initial={isMobile ? { height: 0, opacity: 0, y: -10 } : { opacity: 1 }}
                  animate={isMobile ? { height: 'auto', opacity: 1, y: 0 } : { opacity: 1 }}
                  exit={isMobile ? { height: 0, opacity: 0, y: -10 } : { opacity: 1 }}
                  transition={{
                    height: { duration: 0.3, ease: [0.33, 1, 0.68, 1] },
                    opacity: { duration: 0.2, ease: "easeOut" },
                    y: { duration: 0.2, ease: "easeOut" }
                  }}
                  layout="position"
                  style={{ willChange: "opacity, height, transform" }}
                >
                  <motion.li
                    className={styles.directoryItem}
                    initial={isMobile ? { opacity: 0, y: -5 } : { opacity: 1 }}
                    animate={isMobile ? { opacity: 1, y: 0 } : { opacity: 1 }}
                    transition={{
                      delay: isMobile ? 0.05 : 0,
                      duration: 0.2
                    }}
                  >
                    <a href="mailto:contact@example.com" className={styles.contactLink}>
                      contact@example.com
                    </a>
                  </motion.li>
                  <motion.li
                    className={styles.directoryItem}
                    initial={isMobile ? { opacity: 0, y: -5 } : { opacity: 1 }}
                    animate={isMobile ? { opacity: 1, y: 0 } : { opacity: 1 }}
                    transition={{
                      delay: isMobile ? 0.1 : 0,
                      duration: 0.2
                    }}
                  >
                    <div className={styles.socialLinks}>
                      {socialLinks.map((social, index) => (
                        <motion.a
                          key={social.name}
                          href={social.path}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={styles.socialLink}
                          aria-label={social.name}
                          whileHover={{ scale: 1.15, color: 'var(--primary-color)' }}
                          whileTap={{ scale: 0.95 }}
                          initial={isMobile ? { opacity: 0 } : { opacity: 1 }}
                          animate={isMobile ? { opacity: 1 } : { opacity: 1 }}
                          transition={{
                            delay: isMobile ? 0.15 + (index * 0.05) : 0,
                            duration: 0.2,
                            scale: { type: "spring", stiffness: 400, damping: 17 }
                          }}
                        >
                          {socialIcons[social.name as keyof typeof socialIcons]}
                        </motion.a>
                      ))}
                    </div>
                  </motion.li>
                </motion.ul>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* 页脚底部 - 版权信息 */}
        <motion.div
          className={styles.footerLegal}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: 0.2,
            duration: 0.5,
            ease: [0.25, 0.1, 0.25, 1.0]
          }}
        >
          <div className={styles.legalLinks}>
            {[
              { name: "隐私政策", path: "/privacy" },
              { name: "使用条款", path: "/terms" },
              { name: "网站地图", path: "/sitemap" }
            ].map((link, index) => (
              <motion.div
                key={link.path}
                whileHover={{ y: -2 }}
                transition={{ type: "spring", stiffness: 400, damping: 17 }}
              >
                <Link href={link.path} className={styles.legalLink}>
                  {link.name}
                </Link>
              </motion.div>
            ))}
          </div>
          <motion.div
            className={styles.copyright}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <p>Copyright © {currentYear} saber. 保留所有权利。</p>
            <p className={styles.techStack}>使用 Next.js、React 和 TypeScript 构建</p>
          </motion.div>
        </motion.div>
      </div>
    </footer>
  );
};

export default Footer;
