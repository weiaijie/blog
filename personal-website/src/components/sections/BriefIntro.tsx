import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import styles from '@/styles/BriefIntro.module.css';

const BriefIntro: React.FC = () => {
  return (
    <section id="about" className={styles.briefIntro}>
      <div className={styles.content}>
        <div className={styles.textContent}>
          <h2 className={styles.sectionTitle}>关于我</h2>
          <p className={styles.description}>
            我是一名热衷于创造优质用户体验的全栈开发者。拥有多年的前后端开发经验，
            专注于构建高性能、可扩展的Web应用程序。我相信技术的力量在于解决实际问题，
            并且始终保持对新技术的学习热情。
          </p>
          <Link href="/about" className={styles.moreButton}>
            了解更多
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.buttonIcon}>
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </Link>
        </div>
        <div className={styles.imageContainer}>
          <div className={styles.imageWrapper}>
            <div className={styles.image}>
              {/* 这里可以放置个人照片或头像 */}
              <div className={styles.placeholder}>
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default BriefIntro;
