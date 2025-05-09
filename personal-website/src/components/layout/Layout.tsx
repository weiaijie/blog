import React, { ReactNode } from 'react';
import Header from './Header';
import styles from '@/styles/Layout.module.css';
import { ThemeProvider } from '@/contexts/ThemeContext';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <ThemeProvider>
      <div className={styles.layoutWrapper}>
        <Header />
        <main className={styles.mainContainer}>
          {children}
        </main>
      </div>
    </ThemeProvider>
  );
};

export default Layout;
