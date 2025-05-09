import React, { useEffect, useRef } from 'react';
import Link from 'next/link';
import styles from '@/styles/SkillsHighlight.module.css';

interface Skill {
  name: string;
  description: string;
  level: number;
  icon: React.ReactNode;
}

const SkillsHighlight: React.FC = () => {
  const skillsRef = useRef<HTMLDivElement>(null);

  // 技能列表
  const skills: Skill[] = [
    {
      name: "前端开发",
      description: "精通HTML5, CSS3, JavaScript/TypeScript, React, Vue等现代前端技术",
      level: 90,
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"></polygon>
          <line x1="12" y1="22" x2="12" y2="15.5"></line>
          <polyline points="22 8.5 12 15.5 2 8.5"></polyline>
          <polyline points="2 15.5 12 8.5 22 15.5"></polyline>
          <line x1="12" y1="2" x2="12" y2="8.5"></line>
        </svg>
      )
    },
    {
      name: "后端开发",
      description: "熟练使用Node.js, Express, Python, Django等构建高效的服务端应用",
      level: 80,
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
          <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
          <line x1="6" y1="6" x2="6.01" y2="6"></line>
          <line x1="6" y1="18" x2="6.01" y2="18"></line>
        </svg>
      )
    },
    {
      name: "UI/UX设计",
      description: "了解设计原则和用户体验最佳实践，能够创建直观美观的界面",
      level: 75,
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <circle cx="12" cy="12" r="4"></circle>
          <line x1="21.17" y1="8" x2="12" y2="8"></line>
          <line x1="3.95" y1="6.06" x2="8.54" y2="14"></line>
          <line x1="10.88" y1="21.94" x2="15.46" y2="14"></line>
        </svg>
      )
    },
    {
      name: "DevOps",
      description: "熟悉Git, Docker, CI/CD流程，能够实现自动化部署和维护",
      level: 70,
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
        </svg>
      )
    }
  ];

  // 监听滚动，添加技能条动画
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add(styles.animate);
          }
        });
      },
      { threshold: 0.1 }
    );

    const skillBars = document.querySelectorAll(`.${styles.skillBar}`);
    skillBars.forEach((bar) => observer.observe(bar));

    return () => {
      skillBars.forEach((bar) => observer.unobserve(bar));
    };
  }, []);

  return (
    <section id="skills" className={styles.skillsHighlight} ref={skillsRef}>
      <h2 className={styles.sectionTitle}>技能亮点</h2>
      <div className={styles.skillsGrid}>
        {skills.map((skill, index) => (
          <div className={styles.skillCard} key={index}>
            <div className={styles.skillIcon}>{skill.icon}</div>
            <h3 className={styles.skillName}>{skill.name}</h3>
            <p className={styles.skillDescription}>{skill.description}</p>
            <div className={styles.skillBarContainer}>
              <div
                className={styles.skillBar}
                style={{ '--skill-level': `${skill.level}%` } as React.CSSProperties}
              ></div>
            </div>
          </div>
        ))}
      </div>
      <div className={styles.viewAllContainer}>
        <Link href="/skills" className={styles.viewAllButton}>
          查看全部技能
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.buttonIcon}>
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </Link>
      </div>
    </section>
  );
};

export default SkillsHighlight;
