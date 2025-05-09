import React, { ReactNode, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Header from './Header';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const router = useRouter();
  const isHomePage = router.pathname === '/';
  const [marginTop, setMarginTop] = useState('44px');

  useEffect(() => {
    const handleResize = () => {
      if (isHomePage) {
        // 首页需要为标语留出空间
        if (window.innerWidth <= 480) {
          setMarginTop('220px');
        } else if (window.innerWidth <= 734) {
          setMarginTop('240px');
        } else {
          setMarginTop('250px');
        }
      } else {
        // 其他页面只需要为导航栏留出空间
        setMarginTop('44px');
      }
    };

    // 初始设置
    handleResize();

    // 监听窗口大小变化
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isHomePage]);

  return (
    <>
      <Header showTagline={isHomePage} />
      <main style={{ marginTop }}>
        {children}
      </main>
    </>
  );
};

export default Layout;
