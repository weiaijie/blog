import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import styles from '@/styles/Header.module.css';
import { mainNavRoutes } from '@/config/routes';
import ThemeToggle from '@/components/common/ThemeToggle';

interface HeaderProps {}

const Header: React.FC<HeaderProps> = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  // 不再需要currentPath状态，使用router.pathname代替
  // 直接使用常量，不需要状态变量
  const isLoaded = true; // 内容始终显示
  const [isSearchActive, setIsSearchActive] = useState(false);

  // 监听滚动事件，用于改变头部样式
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    // 不再需要手动设置当前路径，使用router.pathname代替

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

  // 处理搜索按钮点击
  const handleSearchClick = useCallback(() => {
    setIsSearchActive(prev => !prev);
    // 这里可以添加搜索功能的实现，例如显示搜索框等
    alert('搜索功能即将上线');
  }, []);

  // 使用集中管理的路由配置
  const router = useRouter();

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
            {mainNavRoutes.map((item) => (
              <li key={item.path}>
                <Link
                  href={item.path}
                  className={router.pathname === item.path ? styles.active : ''}
                  aria-current={router.pathname === item.path ? 'page' : undefined}
                  style={{ color: 'currentColor' }} // 确保颜色过渡效果
                >
                  {item.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* 右侧操作区域 */}
        <div className={styles.actionArea}>
          {/* 主题切换按钮 */}
          <ThemeToggle className={styles.themeToggle} />

          {/* 搜索按钮 */}
          <button
            className={`${styles.searchButton} ${isSearchActive ? styles.active : ''}`}
            aria-label="搜索"
            onClick={handleSearchClick}
            aria-expanded={isSearchActive}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          </button>

          {/* 移动端汉堡菜单按钮 */}
          <div
            className={`${styles.menuButton} ${isMenuOpen ? styles.open : ''}`}
            onClick={toggleMenu}
            aria-label="菜单"
            aria-expanded={isMenuOpen}
          >
            <span></span>
            <span></span>
          </div>
        </div>

        {/* 移动端导航菜单 */}
        <div className={`${styles.mobileNav} ${isMenuOpen ? styles.open : ''}`}>
          <div className={styles.mobileNavHeader}>
            <div className={styles.mobileNavLogo}>
              <span className={styles.mobileNavName}>saber</span>
              <span className={styles.mobileNavTitle}>全栈开发</span>
            </div>
          </div>

          <nav>
            <h3 className={styles.mobileNavSectionTitle}>导航菜单</h3>
            <ul className={styles.mobileNavMenu}>
              {mainNavRoutes.map((item, index) => (
                <li
                  key={item.path}
                  style={{ '--item-index': index } as React.CSSProperties}
                >
                  <Link
                    href={item.path}
                    className={router.pathname === item.path ? styles.active : ''}
                    onClick={closeMenu}
                    style={{ color: 'currentColor' }} // 确保SVG图标继承当前文本颜色
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <div className={styles.mobileNavFooter}>
            <h3 className={styles.mobileNavSectionTitle}>设置</h3>
            <div className={styles.mobileNavSettings}>
              <div className={styles.mobileNavThemeToggle}>
                <span className={styles.mobileNavSettingLabel}>主题模式</span>
                <ThemeToggle />
              </div>
            </div>

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

      {/* 标语部分已移至独立组件 */}
    </header>
  );
};

export default Header;
