/**
 * FeaturedProjects.tsx
 *
 * 描述：首页的精选项目部分，展示代表性的真实案例
 */

import Link from 'next/link';
import styles from '@/styles/FeaturedProjects.module.css';
import { projectCaseStudies } from '@/data/projects';

const FeaturedProjects = () => {
  const homepageProjects = projectCaseStudies.slice(0, 3);

  return (
    <section id="projects" className={styles.featuredProjects}>
      <div className={styles.sectionIntro}>
        <span className={styles.sectionLabel}>Selected Work</span>
        <h2 className={styles.sectionTitle}>精选案例</h2>
        <p className={styles.sectionSummary}>
          放几段我实际参与过的项目。尽量写清楚当时要解决什么、我做了哪部分。
        </p>
      </div>
      <div className={styles.projectsList}>
        {homepageProjects.map((project) => (
          <div className={styles.projectItem} key={project.id}>
            <div className={styles.projectLeft}>
              <h3 className={styles.projectTitle}>{project.title}</h3>
              <div className={styles.projectMeta}>
                <span className={styles.projectYear}>{project.year.split(' / ')[0]}</span>
                <span className={styles.projectCategory}>{project.categoryLabel}</span>
              </div>
              <div className={styles.projectTags}>
                {project.tags.slice(0, 3).map((tag) => (
                  <span className={styles.projectTag} key={tag}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            <div className={styles.projectRight}>
              <div className={styles.projectDescription}>
                {project.summary}
              </div>
              <div className={styles.projectDescription}>
                {project.positioning}
              </div>
              {project.links.length > 0 && (
                <div className={styles.projectLinks}>
                  {project.links.map((link) => (
                    <a
                      key={link.url}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.projectLink}
                    >
                      {link.label}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className={styles.viewAllContainer}>
        <Link href="/projects" className={styles.viewAllButton}>
          查看更多项目
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={styles.buttonIcon}
          >
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </Link>
      </div>
    </section>
  );
};

export default FeaturedProjects;
