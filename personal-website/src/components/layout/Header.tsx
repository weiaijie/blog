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
            <span className={styles.name}>陈明</span>
          </Link>
        </div>

        {/* 桌面导航菜单 */}
        <nav className={styles.desktopNav}>
          <ul>
            {navItems.map((item) => (
              <li key={item.path}>
                <Link
                  href={item.path}
                  className={currentPath === item.path ? styles.active : ''}
                >
                  {item.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* 移动端汉堡菜单按钮 */}
        <button
          className={`${styles.menuButton} ${isMenuOpen ? styles.open : ''}`}
          onClick={toggleMenu}
          aria-label="菜单"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        {/* 移动端导航菜单 */}
        <div className={`${styles.mobileNav} ${isMenuOpen ? styles.open : ''}`}>
          <ul>
            {navItems.map((item) => (
              <li key={item.path}>
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
        </div>
      </div>

      {/* 个人标语/口号 */}
      <div className={styles.tagline}>
        <div className={styles.container}>
          <h2>前端开发工程师 | 用代码构建美好数字世界</h2>
        </div>
      </div>
    </header>
  );
};

export default Header;
