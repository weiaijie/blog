import React from 'react';
import styles from '@/styles/MainContent.module.css';
import BriefIntro from '@/components/sections/BriefIntro';
import SkillsHighlight from '@/components/sections/SkillsHighlight';
import FeaturedProjects from '@/components/sections/FeaturedProjects';
import LatestPosts from '@/components/sections/LatestPosts';

const MainContent: React.FC = () => {
  return (
    <div className={styles.mainContent}>
      <div className={styles.container}>
        <BriefIntro />
        <SkillsHighlight />
        <FeaturedProjects />
        <LatestPosts />
      </div>
    </div>
  );
};

export default MainContent;
