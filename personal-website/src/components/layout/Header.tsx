import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import styles from '@/styles/Header.module.css';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [currentPath, setCurrentPath] = useState('/');
  const [isLoaded, setIsLoaded] = useState(false);

  // 监听滚动事件，用于改变头部样式
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    // 获取当前路径
    setCurrentPath(window.location.pathname);

    // 页面加载完成后的动画效果
    setIsLoaded(true);

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 切换菜单状态
  const toggleMenu = useCallback(() => {
    setIsMenuOpen((prev) => !prev);
    // 当菜单打开时，禁止背景滚动
    document.body.style.overflow = isMenuOpen ? 'auto' : 'hidden';
  }, [isMenuOpen]);

  // 关闭菜单
  const closeMenu = useCallback(() => {
    setIsMenuOpen(false);
    document.body.style.overflow = 'auto';
  }, []);

  // 导航菜单项
  const navItems = [
    { name: '首页', path: '/' },
    { name: '关于我', path: '/about' },
    { name: '技能', path: '/skills' },
    { name: '项目', path: '/projects' },
    { name: '博客', path: '/blog' },
    { name: '联系', path: '/contact' },
  ];

  return (
    <header className={`${styles.header} ${isScrolled ? styles.scrolled : ''} ${isLoaded ? styles.loaded : ''}`}>
      <div className={styles.container}>
        {/* 品牌标识/Logo */}
        <div className={styles.logo}>
          <Link href="/" onClick={closeMenu}>
            <span className={styles.name}>saber</span>
          </Link>
        </div>

        {/* 桌面导航菜单 - 苹果风格 */}
        <nav className={styles.desktopNav}>
          <ul>
            {navItems.map((item) => (
              <li key={item.path}>
                <Link
                  href={item.path}
                  className={currentPath === item.path ? styles.active : ''}
                  aria-current={currentPath === item.path ? 'page' : undefined}
                >
                  {item.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* 右侧操作区域 */}
        <div className={styles.actionArea}>
          {/* 搜索按钮 */}
          <button className={styles.searchButton} aria-label="搜索">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          </button>

          {/* 移动端汉堡菜单按钮 */}
          <button
            className={`${styles.menuButton} ${isMenuOpen ? styles.open : ''}`}
            onClick={toggleMenu}
            aria-label="菜单"
            aria-expanded={isMenuOpen}
          >
            <span></span>
            <span></span>
          </button>
        </div>

        {/* 移动端导航菜单 */}
        <div className={`${styles.mobileNav} ${isMenuOpen ? styles.open : ''}`}>
          <div className={styles.mobileNavHeader}>
            <div className={styles.mobileNavLogo}>
              <span className={styles.mobileNavName}>陈明</span>
              <span className={styles.mobileNavTitle}>前端开发工程师</span>
            </div>
          </div>

          <nav>
            <h3 className={styles.mobileNavSectionTitle}>导航菜单</h3>
            <ul className={styles.mobileNavMenu}>
              {navItems.map((item, index) => (
                <li
                  key={item.path}
                  style={{ '--item-index': index } as React.CSSProperties}
                >
                  <Link
                    href={item.path}
                    className={currentPath === item.path ? styles.active : ''}
                    onClick={closeMenu}
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <div className={styles.mobileNavFooter}>
            <h3 className={styles.mobileNavSectionTitle}>联系我</h3>
            <div className={styles.mobileNavContact}>
              <a href="mailto:contact@example.com" className={styles.mobileNavContactItem}>
                contact@example.com
              </a>
              <div className={styles.mobileNavSocial}>
                <a href="#" className={styles.mobileNavSocialIcon} aria-label="GitHub">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                  </svg>
                </a>
                <a href="#" className={styles.mobileNavSocialIcon} aria-label="LinkedIn">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                    <rect x="2" y="9" width="4" height="12"></rect>
                    <circle cx="4" cy="4" r="2"></circle>
                  </svg>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 个人标语/口号 - 苹果风格 */}
      <div className={styles.tagline}>
        <div className={styles.taglineContent}>
          <div className={styles.taglineMain}>
            <h2 className={styles.taglineHeading}>创造优雅的数字体验</h2>
            <p className={styles.taglineSubheading}>
              <span className={styles.taglineHighlight}>前端开发工程师</span>，专注于构建直观、高效且美观的用户界面
            </p>
            <div className={styles.taglineActions}>
              <a href="#projects" className={styles.taglinePrimaryButton}>
                查看作品
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.taglineButtonIcon}>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
              </a>
              <a href="#contact" className={styles.taglineSecondaryButton}>
                联系我
              </a>
            </div>
          </div>
          <div className={styles.taglineVisual}>
            <div className={styles.taglineImageContainer}>
              <div className={styles.taglineImage}></div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
