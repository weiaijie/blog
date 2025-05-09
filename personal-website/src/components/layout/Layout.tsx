import React, { ReactNode } from 'react';
import Header from './Header';
import styles from '@/styles/Layout.module.css';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <>
      <Header />
      <main className={styles.mainContainer}>
        {children}
      </main>
    </>
  );
};

export default Layout;
